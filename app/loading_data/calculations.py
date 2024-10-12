import asyncio
from datetime import datetime, date, timedelta

import QuantLib as ql
import pandas as pd


df = pd.read_excel('total_df.xlsx')
df = df.head(1)


face_value = df['nominal_rub'].values[0]
coupon_rate = df['COUPONPERCENT'].values[0]

maturity_date_str = df['MATDATE'].values[0]
date_obj = datetime.strptime(maturity_date_str, '%Y-%m-%d')
maturity_date = ql.Date(date_obj.day, date_obj.month, date_obj.year)

yesterday = date.today() - timedelta(days=1)
settlement_date = ql.Date(yesterday.day, yesterday.month, yesterday.year)
days_to_settlement = ql.Date.today() - settlement_date

day_count = ql.Actual365Fixed() # Конвенция подсчета дней
calendar = ql.Russia()
frequency = ql.Annual # Частота выплаты купонов
yield_curve = ql.YieldTermStructureHandle(ql.FlatForward(settlement_date, 0.03, day_count)) # Кривая доходности

# Создание облигации
bond = ql.FixedRateBond(
  days_to_settlement,
  maturity_date,
  face_value,
  calendar,
  frequency,
  [coupon_rate],
  day_count
)

# Расчет справедливой стоимости
fair_value = bond.NPV(yield_curve)
print(fair_value)

# Расчет дюрации
duration = bond.duration(yield_curve)
print(duration)

# Расчет модифицированной дюрации
modified_duration = bond.duration(yield_curve, ql.Duration.Modified)
print(modified_duration)

# Создание объекта ql.Handle<ql.YieldTermStructure>
# yield_curve_handle = ql.YieldTermStructureHandle(yield_curve)
# Расчет доходности к погашению
# yield_to_maturity = bond.yield(fair_value, yield_curve_handle)

# Расчет текущей доходности
current_yield = (bond.nextCouponRate() * face_value) / fair_value
print(current_yield)

# Расчет кредитного спреда
# credit_spread = (bond.yield(fair_value, yield_curve) - yield_curve.zeroRate(bond.maturityDate(), day_count))
