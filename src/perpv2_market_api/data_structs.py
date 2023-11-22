import datetime

from dataclasses import dataclass, asdict


@dataclass
class SNXMarketSummaryStruct:
    """
    Cleaned market data for an inidividual SNX Market.

    This dataclass mirrors the MarketSummaryStruct in the Solidity file:
    https://github.com/Synthetixio/synthetix/blob/113b5ffd30c549d2b15fc7c726945467a8eb17c7/contracts/PerpsV2MarketData.sol#L23


    Attributes:
        market (str): The market name or identifier.
        asset (str): The asset associated with the market.
        key (str): The key associated with the market.
        maxLeverage (float): The maximum leverage allowed for the market.
        price (float): The current price of the market.
        marketSize (float): The total size of the market.
        marketSkew (float): The skew of the market.
        marketDebt (float): The debt associated with the market.
        currentFundingRate (float): The rolling daily funding rate of the market.
        currentFundingVelocity (float): The velocity of the current funding rate change.
        takerFeeOffchainDelayedOrder (float): The taker fee for off-chain delayed orders in the market.
        makerFeeOffchainDelayedOrder (float): The maker fee for off-chain delayed orders in the market.
        block (str): The block number the data was retrieved from.
        timestamp (int): The timestamp the data was retrieved from.
    """
    market: str
    asset: str
    key: str
    maxLeverage: float
    price: float
    marketSize: float
    marketSkew: float
    marketDebt: float
    currentFundingRate: float               # 24 hr funding rate
    currentFundingVelocity: float           # proportionalSkew * maxFundingVelocity
    takerFeeOffchainDelayedOrder: float
    makerFeeOffchainDelayedOrder: float
    block: str = None
    timestamp: int = None

    # funding
    eightHrFundingRate: float = None
    eightHrFundingVelocity: float = None
    yearlyFundingRate: float = None

    # oi
    long_oi: float = None
    short_oi: float = None

    # relative market skew
    relative_market_skew: float = None

    # USD price
    marketSize_usd: float = None
    marketSkew_usd: float = None
    marketDebt_usd: float = None
    long_oi_usd: float = None
    short_oi_usd: float = None

    def __post_init__(self):
        self.calculate_oi()
        self.resample_funding_rate()
        self.calculate_relative_market_skew()
        self.convert_to_price()

    def calculate_oi(self):
        """
        Calculate the open interest of the market.
        """
        self.long_oi = (self.marketSize + self.marketSkew) / 2
        self.short_oi = self.marketSkew - self.long_oi

    def convert_to_price(self):
        """
        Convert market from base token to USD.
        """
        self.marketSize_usd = self.price * self.marketSize
        self.marketSkew_usd = self.price * self.marketSkew
        self.marketDebt_usd = self.price * self.marketDebt
        self.long_oi_usd = self.price * self.long_oi
        self.short_oi_usd = self.price * self.short_oi

    def resample_funding_rate(self):
        """
        Resample funding from 24hr to 8hr frequency.
        """
        RESAMPLE_FREQ: int = 24/8

        self.eightHrFundingRate = self.currentFundingRate / RESAMPLE_FREQ
        self.eightHrFundingVelocity = self.currentFundingVelocity / RESAMPLE_FREQ
        # 365 days in a year, 100 for percent format.
        self.yearlyFundingRate = self.currentFundingRate * 365 * 100

    def calculate_relative_market_skew(self):
        try:
            self.relative_market_skew = self.marketSkew / self.marketSize
        except ZeroDivisionError:
            self.relative_market_skew: float = 0.0  # or another appropriate value

        try:
            # ! I don't think this is a helpful variable...
            self.relative_funding_rate_to_skew = self.marketSkew / self.currentFundingRate
        except ZeroDivisionError:
            self.relative_funding_rate_to_skew: float = 0.0  # or another appropriate value

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items()}


@dataclass
class PerpV2Directory:
    """
    Raw representation of Perps v2 market data

    Source - https://raw.githubusercontent.com/Synthetixio/synthetix/develop/publish/deployed/mainnet-ovm/deployment.json
    """
    name: str
    address: str
    source: list
    timestamp: str
    txn: str
    network: str
    constructorArgs: list[str]

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items()}


@dataclass
class MarketDetails:
    """
    Raw representation of Perps v2 market data.
    Source - https://raw.githubusercontent.com/Synthetixio/synthetix/develop/publish/deployed/mainnet-ovm/deployment.json
    """
    market: str
    baseAsset: str
    marketKey: str
    takerFee: float
    makerFee: float
    takerFeeDelayedOrder: float
    makerFeeDelayedOrder: float
    takerFeeOffchainDelayedOrder: float
    makerFeeOffchainDelayedOrder: float
    maxLeverage: float
    maxMarketValue: float
    maxFundingVelocity: float
    skewScale: float
    marketSize: float
    long: float
    short: float
    marketDebt: float
    marketSkew: float
    price: float
    invalid: bool

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items()}


@dataclass
class PerpV2MarketParams:
    """
    Raw representation of Perps v2 market data.
    Source - https://raw.githubusercontent.com/Synthetixio/synthetix/develop/publish/deployed/mainnet-ovm/deployment.json
    """
    marketKey: str
    asset: str
    makerFee: float
    takerFee: float
    takerFeeDelayedOrder: float
    makerFeeDelayedOrder: float
    makerFeeOffchainDelayedOrder: float
    takerFeeOffchainDelayedOrder: float
    nextPriceConfirmWindow: int
    delayedOrderConfirmWindow: int
    minDelayTimeDelta: int
    maxDelayTimeDelta: int
    offchainDelayedOrderMinAge: int
    offchainDelayedOrderMaxAge: int
    maxLeverage: int
    maxMarketValue: int
    maxFundingVelocity: int
    skewScale: int
    offchainPriceDivergence: float
    liquidationPremiumMultiplier: float
    offchainMarketKey: float
    liquidationBufferRatio: float
    maxPD: float
    maxLiquidationDelta: float
    paused: bool
    offchainPaused: bool

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items()}
