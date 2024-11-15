import aiohttp
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import statsmodels.formula.api as sm

from datetime import timedelta, date, timezone, datetime
from decimal import Decimal

from fastapi import HTTPException
from scipy import stats
from scipy.stats import norm


CORP_B_URL = 'https://iss.moex.com/iss/engines/stock/markets/bonds/boards/TQCB/securities.json'
GOV_B_URL = 'https://iss.moex.com/iss/engines/stock/markets/bonds/boards/TQOB/securities.json'
HIST_URL = 'https://iss.moex.com/iss/history/engines/stock/markets/bonds/securities/{ticker}.json?from={start_date}&till={end_date}&marketprice_board=1&start={point}'


# Исключение - слишком мало наблюдений
class NotEnoughObservations(Exception):
    pass

# Функция для получения данных по валютам с сайта ЦБ РФ
async def fetch_currency_data(session, request_date):
    currency_url = f"https://www.cbr.ru/scripts/XML_daily.asp?date_req={request_date.strftime('%d/%m/%Y')}"
    async with session.get(currency_url) as response:
        if response.status == 200:
            xml_data = await response.text()
            root = ET.fromstring(xml_data)

            currency_data = []
            for currency in root.findall('./Valute'):
                currency_name = currency.find('./Name').text
                currency_code = currency.find('./CharCode').text
                curs = Decimal(currency.find('./Value').text.replace(',', '.'))

                currency_data.append([currency_name, currency_code, curs])
                currency_data.append(['Российский рубль', 'SUR', 1.000])
                df = pd.DataFrame(currency_data, columns=['currency_name', 'currency_code', 'curs'])
            currency_dict = df.to_dict(orient='records')
            return currency_dict
        else:
            raise Exception(f"API error: {response.status}")


# Функция для загрузки данных по валютам, полученных с помощью функции fetch_currency_data()
async def load_currency_data():
    async with aiohttp.ClientSession() as session:
        offset = timezone(timedelta(hours=3))
        current_datetime = datetime.now(offset)

        if current_datetime.weekday() in range(1, 6):
            request_date = current_datetime - timedelta(days=1)
        elif current_datetime.weekday() == 6:
            request_date = current_datetime - timedelta(days=2)
        elif current_datetime.weekday() == 0:
            request_date = current_datetime - timedelta(days=3)

        currency_dict = await fetch_currency_data(session=session, request_date=request_date)
        return currency_dict


# Функция для конвертации данных, выраженных в ин.валюте, в рубли
def convert_currency_cur(row, col_name, curr_dict, key_name):
    currency_id = row[key_name]
    if currency_id in curr_dict and row[col_name]:
        return Decimal(Decimal(row[col_name]) * curr_dict[currency_id])
    else:
        return None


# Функция для получения данных по облигациям с сайта Московской биржи
async def fetch_bond_data(session, url, curr_dict):
    async with session.get(url) as response:
        if response.status == 200:
            data = await response.json()

            if data is not None:

                columns = [
                    column for column in data["securities"]["columns"]
                ]
                df = pd.DataFrame(columns=columns)
                rows = data["securities"]["data"]

                for row in rows:
                    rows_data = dict(zip(columns, [i for i in row]))
                    df = pd.concat([df, pd.DataFrame([rows_data])], ignore_index=True)

                df['MATDATE'] = df['MATDATE'].apply(lambda x: x if x != '0000-00-00' else None)
                df['NEXTCOUPON'] = df['NEXTCOUPON'].apply(lambda x: x if x != '0000-00-00' else None)
                df['PREVDATE'] = df['PREVDATE'].apply(lambda x: x if x != '0000-00-00' else None)
                df['PREVWAPRICE'] = df['PREVWAPRICE'].fillna(0)
                df['COUPONVALUE'] = df['COUPONVALUE'].fillna(0)
                df['PREVWAPRICE'] = df['PREVWAPRICE'] * df['FACEVALUE'] / 100

                df['prevwaprice_rub'] = df.apply(
                    convert_currency_cur,
                    col_name="PREVWAPRICE",
                    key_name="FACEUNIT", curr_dict=curr_dict, axis=1
                )
                df['nominal_rub'] = df.apply(
                    convert_currency_cur,
                    col_name='FACEVALUE',
                    key_name="FACEUNIT", curr_dict=curr_dict, axis=1
                )
                df['accum_coupon_rub'] = df.apply(
                    convert_currency_cur,
                    col_name='ACCRUEDINT',
                    key_name="CURRENCYID", curr_dict=curr_dict, axis=1
                )
                df['coupon_value_rub'] = df.apply(
                    convert_currency_cur,
                    col_name='COUPONVALUE',
                    key_name="FACEUNIT", curr_dict=curr_dict, axis=1
                )

                df = df[['SECID', 'SECNAME', 'PREVWAPRICE',
                         'FACEVALUE', 'COUPONVALUE', 'COUPONPERIOD',
                         'ACCRUEDINT', 'FACEUNIT', 'CURRENCYID',
                         'LOTSIZE', 'ISSUESIZE', 'PREVDATE',
                         'NEXTCOUPON', 'MATDATE', 'prevwaprice_rub',
                         'nominal_rub', 'accum_coupon_rub', 'coupon_value_rub']]

                df = df.rename(columns={'SECID': 'ticker', 'SECNAME': 'name',
                                        'PREVWAPRICE': 'prevwaprice_cur',
                                        'FACEVALUE': 'nominal_cur', 'COUPONVALUE': 'coupon_value_cur',
                                        'COUPONPERIOD': 'coupon_period', 'ACCRUEDINT': 'accum_coupon_cur',
                                        'FACEUNIT': 'cur_of_nominal', 'CURRENCYID': 'cur_of_market',
                                        'LOTSIZE': 'lot_size', 'ISSUESIZE': 'issue_size',
                                        'PREVDATE': 'prev_date', 'NEXTCOUPON': 'next_coupon_date',
                                        'MATDATE': 'maturity_date'})
                df['loading_date'] = date.today()
            return df
        else:
            raise Exception(f'API error: {response.status}')


# Функция для загрузки данных по облигациям, полученных с помощью функции fetch_bond_data()
async def load_bond_data(curr_dict):
    async with aiohttp.ClientSession() as session:
        corp_df = await fetch_bond_data(session=session, url=CORP_B_URL, curr_dict=curr_dict)
        gov_df = await fetch_bond_data(session=session, url=GOV_B_URL, curr_dict=curr_dict)
        total_df = pd.concat([corp_df, gov_df], ignore_index=True)
        bonds_dict = total_df.to_dict(orient='records')

        return bonds_dict


# Функция для получения данных по историческим ценам облигации с сайта Московской биржи (за год)
async def fetch_hist_bond_data(session, ticker):
    end_date = datetime.today().strftime("%Y-%m-%d")
    start_date = (datetime.today() - timedelta(days=365)).strftime("%Y-%m-%d")

    df = pd.DataFrame(columns=['trade_date', 'close_price'])
    for point in ["0", "100", "200"]:
        full_url = HIST_URL.format(**locals())
        async with session.get(full_url) as response:
            if response.status == 200:
                data = await response.json()

                if data is not None:
                    columns = ['trade_date', 'close_price']
                    rows = data["history"]["data"]
                    data = [[row[1], row[9]] for row in rows]

                    new_df = pd.DataFrame(data, columns=columns)
                    df = pd.concat([df, new_df])
    return df


# Функция для загрузки данных по историческим ценам облигаций и расчет коэф.корреляции между ними
async def load_hist_bond_data(ticker_1, ticker_2):
    async with aiohttp.ClientSession() as session:
        df1 = await fetch_hist_bond_data(session, ticker_1)
        df2 = await fetch_hist_bond_data(session, ticker_2)
        merged_df = pd.merge(df1, df2, on='trade_date', how='outer')
        merged_df = merged_df.dropna()
        print(merged_df)
        if merged_df.shape[0] < 30:
            raise NotEnoughObservations("Как минимум в одной из облигаций слишком мало "
                                        "наблюдений (менее 30) для расчета корреляции")

        col_1 = merged_df.close_price_x
        col_2 = merged_df.close_price_y

        # Проверка на нормальность
        loc, scale = norm.fit(col_1)
        n = norm(loc=loc, scale=scale)
        norm_1 = 0.05 <= stats.kstest(col_1, n.cdf).pvalue

        loc, scale = norm.fit(col_2)
        n = norm(loc=loc, scale=scale)
        norm_2 = 0.05 <= stats.kstest(col_2, n.cdf).pvalue

        col_dict = {
            1: col_1,
            2: col_2
        }
        # Проверка на выбросы
        for i in range(1, 3):
            col = col_dict[i]

            q1 = np.percentile(col, 25)
            q3 = np.percentile(col, 75)
            IQR = q3 - q1
            lower_bound = q1 - 1.5 * IQR
            upper_bound = q3 + 1.5 * IQR
            outliers = [x for x in col
                        if x < lower_bound or x > upper_bound]
            if outliers:
                if i == 1:
                    outliers_1 = True
                elif i == 2:
                    outliers_2 = True
            else:
                if i == 1:
                    outliers_1 = False
                elif i == 2:
                    outliers_2 = False

        corr_p = stats.pearsonr(col_1, col_2).pvalue
        corr_s = stats.spearmanr(col_1, col_2).pvalue
        corr_k = stats.kendalltau(col_1, col_2).pvalue
        model = sm.ols('y ~ x', data={'x': col_1, 'y': col_2})
        results = model.fit(cov_type='HC1')
        rob_corr = results.params[1]
        print(corr_p, corr_s, corr_k, rob_corr)

        if norm_1 and norm_2 and not outliers_1 and not outliers_2:
            advice = 'Рекомендуется ориентироваться на коэффициент Пирсона'
        elif (not norm_1 or not norm_2) and not outliers_1 and not outliers_2:
            advice = 'Рекомендуется ориентироваться на коэффициент Спирмена или Кендалла'
        elif outliers_1 or outliers_2:
            advice = ('Рекомендуется ориентироваться на корреляцию, оцененную через регрессию '
                      '(Robust_correlation)')
        else:
            advice = ''

        corr_dict = {
            'corr_p': corr_p,
            'corr_s': corr_s,
            'corr_k': corr_k,
            'rob_corr': rob_corr,
            'advice': advice
        }

        return corr_dict
