#file test_moneyed_classes.py

from decimal import Decimal, localcontext
import pytest  # Works with less code, more consistency than unittest.

from moneyed.classes import Currency, Money, MoneyComparisonError, Broker, BrokerException, CURRENCIES, DEFAULT_CURRENCY
from moneyed import classes
from moneyed.localization import format_money


class SimpleBroker(Broker):

    def get_exchange_rate(self, from_currency, to_currency):
        if (from_currency, to_currency) == (CURRENCIES['USD'], CURRENCIES['EUR']):
            return Decimal.from_float(1.0 / 1.3)
        if (from_currency, to_currency) == (CURRENCIES['EUR'], CURRENCIES['USD']):
            return Decimal.from_float(1.3)
        return super(SimpleBroker, self).get_exchange_rate(from_currency, to_currency)


classes.set_broker(SimpleBroker())


class TestCurrency:

    def setup_method(self, method):
        self.default_curr_code = 'XYZ'
        self.default_curr = CURRENCIES[self.default_curr_code]

    def test_init(self):
        usd_countries = CURRENCIES['USD'].countries
        US_dollars = Currency(code='USD', numeric='840', name='US Dollar', countries=['AMERICAN SAMOA', 'BRITISH INDIAN OCEAN TERRITORY', 'ECUADOR', 'GUAM', 'MARSHALL ISLANDS', 'MICRONESIA', 'NORTHERN MARIANA ISLANDS', 'PALAU', 'PUERTO RICO', 'TIMOR-LESTE', 'TURKS AND CAICOS ISLANDS', 'UNITED STATES MINOR OUTLYING ISLANDS', 'VIRGIN ISLANDS (BRITISH)', 'VIRGIN ISLANDS (U.S.)'])
        assert US_dollars.code == 'USD'
        assert US_dollars.countries == usd_countries
        assert US_dollars.name == 'US Dollar'
        assert US_dollars.numeric == '840'

    def test_repr(self):
        assert str(self.default_curr) == self.default_curr_code


class TestMoney:

    def setup_method(self, method):
        self.one_million_decimal = Decimal('1000000')
        self.USD = CURRENCIES['USD']
        self.EUR = CURRENCIES['EUR']
        self.one_million_bucks = Money(amount=self.one_million_decimal,
                                       currency=self.USD)
        self.usd10 = Money(amount=10, currency=self.USD)
        self.usd13 = Money(amount=13, currency=self.USD)
        self.usd20 = Money(amount=20, currency=self.USD)
        self.eur10 = Money(amount=10, currency=self.EUR)

    def test_init(self):
        one_million_dollars = Money(amount=self.one_million_decimal,
                                    currency=self.USD)
        assert one_million_dollars.amount == self.one_million_decimal
        assert one_million_dollars.currency == self.USD

    def test_init_string_currency_code(self):
        one_million_dollars = Money(amount=self.one_million_decimal,
                                    currency='usd')
        assert one_million_dollars.amount == self.one_million_decimal
        assert one_million_dollars.currency == self.USD

    def test_init_default_currency(self):
        one_million = self.one_million_decimal
        one_million_dollars = Money(amount=one_million)  # No currency given!
        assert one_million_dollars.amount == one_million
        assert one_million_dollars.currency == DEFAULT_CURRENCY

    def test_init_float(self):
        one_million_dollars = Money(amount=1000000.0)
        assert one_million_dollars.amount == self.one_million_decimal

    def test_repr(self):
        assert repr(self.one_million_bucks) == '1000000 USD'

    def test_str(self):
        assert str(self.one_million_bucks) == 'US$1,000,000.00'

    def test_format_money(self):
        # Two decimal places by default
        assert format_money(self.one_million_bucks) == 'US$1,000,000.00'
        # No decimal point without fractional part
        assert format_money(self.one_million_bucks, decimal_places=0) == 'US$1,000,000'

    def test_add(self):
        assert (self.one_million_bucks + self.one_million_bucks
                == Money(amount='2000000', currency=self.USD))

    def test_add_zero(self):
        assert self.usd10 + 0 == self.usd10
        assert self.usd10 + 0.0 == self.usd10
        assert self.usd10 + Decimal('0') == self.usd10

    def test_add_non_money(self):
        with pytest.raises(TypeError):
            Money(1000) + 123

    def test_sum(self):
        s = sum([self.usd10, self.usd13, self.usd20])
        assert s.amount == 43
        assert s.currency == self.USD

    def test_sub(self):
        zeroed_test = self.one_million_bucks - self.one_million_bucks
        assert zeroed_test == Money(amount=0, currency=self.USD)

    def test_sub_non_money(self):
        with pytest.raises(TypeError):
            Money(1000) - 123

    def test_mul(self):
        x = Money(amount=111.33, currency=self.USD)
        assert 3 * x == Money(333.99, currency=self.USD)
        assert Money(333.99, currency=self.USD) == 3 * x

    def test_mul_bad(self):
        with pytest.raises(TypeError):
            self.one_million_bucks * self.one_million_bucks

    def test_div(self):
        x = Money(amount=50, currency=self.USD)
        y = Money(amount=2, currency=self.USD)
        assert x / y == Decimal(25)

    # IMPORTANT: mismatched currencies division raises now
    # BrokerException (if exchange rate is not available), not TypeError
    def test_div_mismatched_currencies(self):
        x = Money(amount=50, currency=self.USD)
        y = Money(amount=2, currency=CURRENCIES['CAD'])
        with pytest.raises(BrokerException):
            assert x / y == Money(amount=25, currency=self.USD)

    def test_div_by_non_Money(self):
        x = Money(amount=50, currency=self.USD)
        y = 2
        assert x / y == Money(amount=25, currency=self.USD)

    def test_rmod(self):
        assert 1 % self.one_million_bucks == Money(amount=10000,
                                                   currency=self.USD)

    def test_rmod_bad(self):
        with pytest.raises(TypeError):
            assert (self.one_million_bucks % self.one_million_bucks
                    == 1)

    def test_convert_to_default(self):
        # Currency conversions are not implemented as of 2/2011; when
        # they are working, then convert_to_default and convert_to
        # will need to be tested.
        pass

    # Note: no tests for __eq__ as it's quite thoroughly covered in
    # the assert comparisons throughout these tests.

    def test_ne(self):
        x = Money(amount=1, currency=self.USD)
        assert self.one_million_bucks != x
        
    def test_equality_to_other_types(self):
        x = Money(amount=1, currency=self.USD)
        assert self.one_million_bucks != None
        assert self.one_million_bucks != {}

    def test_not_equal_to_decimal_types(self):
        assert self.one_million_bucks != self.one_million_decimal

    def test_lt(self):
        x = Money(amount=1, currency=self.USD)
        assert x < self.one_million_bucks

    def test_lt_mistyped(self):
        x = 1.0
        with pytest.raises(MoneyComparisonError):
            assert x < self.one_million_bucks

    def test_gt(self):
        x = Money(amount=1, currency=self.USD)
        assert self.one_million_bucks > x

    def test_gt_mistyped(self):
        x = 1.0
        with pytest.raises(MoneyComparisonError):
            assert self.one_million_bucks > x

    def test_simple_currency_conversion(self):
        with localcontext() as ctx:
            # Limit precision
            ctx.prec = 10

            assert self.usd13.convert(self.EUR) == Money(amount=10, currency=self.EUR)
            assert self.usd13.convert(self.EUR).convert(self.USD) == self.usd13
            assert self.eur10.convert(self.USD).convert(self.EUR) == self.eur10

            # Conversion to the same currency doesn't change anything
            assert self.usd10.convert(self.USD) == self.usd10

    def test_addition_of_different_currencies(self):
        with localcontext() as ctx:
            # Limit precision
            ctx.prec = 10

            x1 = self.usd10 + self.eur10
            x2 = self.eur10 + self.usd13

            assert x1.amount == 23
            assert x1.currency == self.USD

            assert x2.amount == 20
            assert x2.currency == self.EUR

    def test_comparison_of_different_currencies(self):
        with localcontext() as ctx:
            # Limit precision
            ctx.prec = 10

            assert self.usd13 == self.eur10
            assert self.usd10 < self.eur10
            assert self.usd20 > self.eur10
