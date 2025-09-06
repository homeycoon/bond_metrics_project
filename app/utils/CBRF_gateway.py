from datetime import datetime, timedelta, timezone
from decimal import Decimal

import aiohttp
import xml.etree.ElementTree as ET
import pandas as pd


class CBRFGateway:
    """Класс-шлюз для работы с ЦБ РФ"""
    def __init__(self):
        self.currency_url = "https://www.cbr.ru/scripts/XML_daily.asp?date_req="

    async def load_currency_data(self) -> list[dict]:
        """
        Функция для загрузки данных по валютам,
        полученных с помощью функции fetch_currency_data()

        :return: список валют, их кода и курса
        """
        async with aiohttp.ClientSession() as session:
            offset = timezone(timedelta(hours=3))
            current_datetime = datetime.now(offset)

            if current_datetime.weekday() in range(1, 6):
                request_date = current_datetime - timedelta(days=1)
            elif current_datetime.weekday() == 6:
                request_date = current_datetime - timedelta(days=2)
            elif current_datetime.weekday() == 0:
                request_date = current_datetime - timedelta(days=3)

            currency_dict = await self.fetch_currency_data(session=session, request_date=request_date)
            return currency_dict

    async def fetch_currency_data(self, session: aiohttp.ClientSession, request_date: datetime) -> list[dict]:
        """
        Функция для получения данных по валютам с сайта ЦБ РФ

        :param session: объект сессии подключения к источнику
        :param request_date: дата запроса
        :return: список валют, их кода и курса
        """

        async with session.get(self.currency_url + request_date.strftime('%d/%m/%Y')) as response:
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
