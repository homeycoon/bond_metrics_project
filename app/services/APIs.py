import asyncio
from datetime import timedelta, date
from decimal import Decimal

import aiohttp
import xml.etree.ElementTree as ET
import pandas as pd


CORP_B_URL = 'https://iss.moex.com/iss/engines/stock/markets/bonds/boards/TQCB/securities.json'
GOV_B_URL = 'https://iss.moex.com/iss/engines/stock/markets/bonds/boards/TQOB/securities.json'


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


async def load_currency_data():
    async with aiohttp.ClientSession() as session:
        yesterday = date.today() - timedelta(days=1)
        currency_dict = await fetch_currency_data(session=session, request_date=yesterday)
        return currency_dict


def convert_currency_cur(row, col_name, curr_dict, key_name):
    currency_id = row[key_name]
    if currency_id in curr_dict:
        return Decimal(Decimal(row[col_name]) * curr_dict[currency_id])
    else:
        return None


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
                    rows_data = dict(
                        zip(columns, [i for i in row])
                    )

                    df = pd.concat(
                    [df, pd.DataFrame([rows_data])], ignore_index=True
                    )

                df['MATDATE'] = df['MATDATE'].apply(lambda x: x if x != '0000-00-00' else None)
                df['PREVDATE'] = df['PREVDATE'].apply(lambda x: x if x != '0000-00-00' else None)
                df['NEXTCOUPON'] = df['NEXTCOUPON'].apply(lambda x: x if x != '0000-00-00' else None)
                df['PREVLEGALCLOSEPRICE'] = df['PREVLEGALCLOSEPRICE'].fillna(0)
                df['COUPONPERCENT'] = df['COUPONPERCENT'].fillna(0)

                df['prev_close_price_rub'] = df.apply(
                    convert_currency_cur,
                    col_name="PREVLEGALCLOSEPRICE",
                    key_name="CURRENCYID", curr_dict=curr_dict, axis=1
                )
                df['accum_coupon_rub'] = df.apply(
                    convert_currency_cur,
                    col_name='ACCRUEDINT',
                    key_name="CURRENCYID", curr_dict=curr_dict, axis=1
                )
                df['nominal_rub'] = df.apply(
                    convert_currency_cur,
                    col_name='LOTVALUE',
                    key_name="FACEUNIT", curr_dict=curr_dict, axis=1
                )
                df = df[['SECID', 'SECNAME', 'PREVLEGALCLOSEPRICE',
                         'LOTVALUE', 'COUPONPERCENT', 'COUPONPERIOD',
                         'ACCRUEDINT', 'FACEUNIT', 'CURRENCYID',
                         'LOTSIZE', 'ISSUESIZE', 'PREVDATE',
                         'NEXTCOUPON', 'MATDATE', 'prev_close_price_rub',
                         'nominal_rub', 'accum_coupon_rub']]
                df = df.rename(columns={'SECID': 'ticker', 'SECNAME': 'name',
                                        'PREVLEGALCLOSEPRICE': 'prev_close_price_cur',
                                        'LOTVALUE': 'nominal_cur', 'COUPONPERCENT': 'coupon_rate',
                                        'COUPONPERIOD': 'coupon_period', 'ACCRUEDINT': 'accum_coupon_cur',
                                        'FACEUNIT': 'valuta_nominal', 'CURRENCYID': 'currency_curr',
                                        'LOTSIZE': 'lot_size', 'ISSUESIZE': 'issue_size',
                                        'PREVDATE': 'prev_date', 'NEXTCOUPON': 'next_coupon_date',
                                        'MATDATE': 'maturity_date'})
                df['loading_date'] = date.today()
            return df
        else:
            raise Exception(f'API error: {response.status}')


async def load_bond_data(curr_dict):
    async with aiohttp.ClientSession() as session:
        corp_df = await fetch_bond_data(session=session, url=CORP_B_URL, curr_dict=curr_dict)
        gov_df = await fetch_bond_data(session=session, url=GOV_B_URL, curr_dict=curr_dict)
        total_df = pd.concat([corp_df, gov_df], ignore_index=True)
        bonds_dict = total_df.to_dict(orient='records')

        return bonds_dict
