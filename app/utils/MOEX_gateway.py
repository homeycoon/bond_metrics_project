from typing import Any

import aiohttp
import pandas as pd
import numpy as np
import statsmodels.formula.api as sm

from datetime import timedelta, date, datetime
from decimal import Decimal

from scipy import stats
from scipy.stats import norm


# Исключение - слишком мало наблюдений
class NotEnoughObservations(Exception):
    pass


class MOEXGateway:
    """Класс-шлюз для работы с ISS MOEX"""
    def __init__(self):
        self.CORP_B_URL = 'https://iss.moex.com/iss/engines/stock/markets/bonds/boards/TQCB/securities.json'
        self.GOV_B_URL = 'https://iss.moex.com/iss/engines/stock/markets/bonds/boards/TQOB/securities.json'
        self.HIST_URL = 'https://iss.moex.com/iss/history/engines/stock/markets/bonds/securities/{ticker}.json?from={start_date}&till={end_date}&marketprice_board=1&start={point}'

    async def load_bond_data(self, curr_dict: dict) -> list[dict]:
        """
        Функция для загрузки данных по облигациям,
        полученных с помощью функции fetch_bond_data()

        :param curr_dict: словарь с данными о валютах и их курсах
        :return: список словарей с данными по облигациям
        """
        async with aiohttp.ClientSession() as session:
            corp_df = await self.fetch_bond_data(session=session, url=self.CORP_B_URL, curr_dict=curr_dict)
            gov_df = await self.fetch_bond_data(session=session, url=self.GOV_B_URL, curr_dict=curr_dict)
            total_df = pd.concat([corp_df, gov_df], ignore_index=True)
            bonds_dict = total_df.to_dict(orient='records')

            return bonds_dict

    async def fetch_bond_data(self, session: aiohttp.ClientSession, url: str, curr_dict: dict) -> pd.DataFrame:
        """
        Функция для получения данных по облигациям с сайта Московской биржи

        :param session: объект сессии подключения к источнику
        :param url: url источника
        :param curr_dict: словарь с данными о валютах и их курсах
        :return: датафрейм с данными об облигациях
        """
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
                        self.convert_currency_cur,
                        col_name="PREVWAPRICE",
                        key_name="FACEUNIT", curr_dict=curr_dict, axis=1
                    )
                    df['nominal_rub'] = df.apply(
                        self.convert_currency_cur,
                        col_name='FACEVALUE',
                        key_name="FACEUNIT", curr_dict=curr_dict, axis=1
                    )
                    df['accum_coupon_rub'] = df.apply(
                        self.convert_currency_cur,
                        col_name='ACCRUEDINT',
                        key_name="CURRENCYID", curr_dict=curr_dict, axis=1
                    )
                    df['coupon_value_rub'] = df.apply(
                        self.convert_currency_cur,
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

    @staticmethod
    def convert_currency_cur(row: Any, col_name: str, curr_dict: dict, key_name: str) -> Decimal | None:
        """
        Функция для конвертации данных, выраженных в ин.валюте, в рубли

        :param row: строка / запись из датафрейма
        :param col_name: наименование столбца, в котором данные перевести в рубли
        :param curr_dict: словарь с данными о валютах и их курсах
        :param key_name: наименование валюты, использованной для расчета
        :return: объект типа Decimal: сумма в рублях
        """
        currency_id = row[key_name]
        if currency_id in curr_dict and row[col_name]:
            return Decimal(Decimal(row[col_name]) * curr_dict[currency_id])
        else:
            return None

    async def load_hist_bond_data(self, ticker_1: str, ticker_2: str) -> dict:
        """
        Функция для загрузки данных по историческим ценам облигаций
        и расчет коэф.корреляции между ними

        :param ticker_1: тикер первой облигации
        :param ticker_2: тикер второй облигации
        :return: словарь с разными коэффициентами корреляции двух облигаций
        """
        async with aiohttp.ClientSession() as session:
            df1 = await self.fetch_hist_bond_data(session, ticker_1)
            df2 = await self.fetch_hist_bond_data(session, ticker_2)
            merged_df = pd.merge(df1, df2, on='trade_date', how='outer')
            merged_df = merged_df.dropna()
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

    async def fetch_hist_bond_data(self, session: aiohttp.ClientSession, ticker: str) -> pd.DataFrame:
        """
        Функция для получения данных по историческим ценам облигации
        с сайта Московской биржи (за год)

        :param session: объект сессии подключения к источнику
        :param ticker: тикер облигации
        :return: датафрейм с данными по историческим ценам облигации
        """
        end_date = datetime.today().strftime("%Y-%m-%d")
        start_date = (datetime.today() - timedelta(days=365)).strftime("%Y-%m-%d")

        df = pd.DataFrame(columns=['trade_date', 'close_price'])
        for point in ["0", "100", "200"]:
            full_url = self.HIST_URL.format(**locals())
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
