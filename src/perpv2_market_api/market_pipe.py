import json
import polars as pl
import requests
import os
import time


from dotenv import load_dotenv
from dataclasses import dataclass
from perpv2_market_api.struct_parser import extract_names, flatten_list
from perpv2_market_api.data_structs import SNXMarketSummaryStruct, PerpV2Directory, MarketDetails
from typing import List
from web3 import Web3


SNX_DECIMALS = 10**18


@dataclass
class SNXMarketPipe:
    """
    SNXMarket calls external functions from Synthetix V2 contracts.
    The output is saved to a list of tuple data.
    """
    load_dotenv()
    node = Web3(Web3.HTTPProvider(os.getenv("OPTIMISM_RPC")))

    def get_all_market_summaries(self, block: int = 0) -> dict[str]:
        """
        get_all_market_summaries() retrieves a summary of SNX V2 market data from the PerpetualsV2MarketData contract
        for a given block and timestamp.

        Args:
            block (int): The historical block number to retrieve data from. If 0, the most recent block
                                    will be used. (Default: 0)

        Returns:
            dict: A dictionary containing block, timestamp, and a list of market data dictionaries.
        """
        file: str = os.path.abspath("abi/PerpsV2MarketData.json")

        with open(file) as f:
            abi = json.load(f)

        contract = self.node.eth.contract(
            address="0x340B5d664834113735730Ad4aFb3760219Ad9112",  # PerpV2MarketData
            abi=abi
        )

        block, timestamp = self._get_block(block)

        MAX_RETRIES = 15
        RETRY_INTERVAL = 2
        for retry in range(MAX_RETRIES):
            try:
                output_data = contract.functions.allMarketSummaries().call(block_identifier=block)
            except ValueError as ve:
                if 'timeout' in str(ve).lower() and retry < MAX_RETRIES - 1:
                    # print the ValueError
                    print(f'ValueError: {ve}')
                    print(
                        f"Retry attempt {retry+1}/{MAX_RETRIES} after {RETRY_INTERVAL} seconds...")
                    time.sleep(RETRY_INTERVAL)
                else:
                    raise

        # Flatten the tuples in the list
        flattened_data_array = []
        # extract function output names from abi.
        names = extract_names(abi, 'allMarketSummaries')

        for market in output_data:
            flattened_data = flatten_list(market)
            flattened_data_array.append(dict(zip(names, flattened_data)))

        return {
            "block": block,
            "timestamp": timestamp,
            "results": flattened_data_array
        }

    def get_market_details(self, market: str, block: int = 0, ) -> dict[str]:
        """
        Retrieves details of a specific market from the PerpV2MarketData contract.

        Args:
            market (str, optional): The market identifier for retrieving details.
            block (int, optional): The historical block number to query data from.
                Defaults to the latest block.

        Returns:
            dict: A dictionary with the following keys:
                - "block": The block number from which the data was retrieved.
                - "timestamp": The timestamp (Unix time) of the retrieved block.
                - "market_details": A dictionary with market details. Keys correspond to output names
                                    from the contract's ABI, and values represent corresponding data.

        Raises:
            FileNotFoundError: If the ABI file for the PerpsV2MarketData contract is not found.
            ConnectionError: If there is an issue connecting to the Ethereum node.
            ValueError: If the specified block is less than 0.
            KeyError: If the market identifier (market) is not found in the contract.
            Exception: For any other unexpected errors during the contract function call.
        """
        file = os.path.abspath("abi/PerpsV2MarketData.json")

        with open(file) as f:
            abi = json.load(f)

        contract = self.node.eth.contract(
            address="0x340B5d664834113735730Ad4aFb3760219Ad9112",  # PerpV2MarketData
            abi=abi
        )

        block, timestamp = self._get_block(block)

        output_data = contract.functions.marketDetails(
            market).call(block_identifier=block)

        # extract function output names from abi.
        names = extract_names(abi, 'marketDetails')

        # Flatten the tuples in the list
        flattened_data = flatten_list(output_data)

        # print(f"names length: {len(names)}")
        # print(f"length of flattened data: {len(flattened_data)}")

        # create a dictionary from names and flattened_data
        flattened_market_details = dict(zip(names, flattened_data))

        return {
            "block": block,
            "timestamp": timestamp,
            "results": flattened_market_details
        }

    def get_proxy_perp_addresses(self):
        """
        Fetches the latest proxy addresses for SNX Markets from GitHub.
        This function should be periodically called to keep the markets up-to-date.

        Saves the market addresses to `data/perp_market_addresses.json`
        """
        url = 'https://raw.githubusercontent.com/Synthetixio/synthetix/develop/publish/deployed/mainnet-ovm/deployment.json'
        r = requests.get(url)
        if r.status_code == 200:
            try:
                data = r.json()

                # save to file. if data.json doesn't exist, create the file first
                # assumes data folder exists already.
                if os.path.exists('data/data.json'):
                    with open('data/perp_market_addresses.json', 'r') as f:
                        json.dump(data, f)
                else:
                    with open('data/perp_market_addresses.json', 'w') as f:
                        json.dump(data, f)

            except json.decoder.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
        else:
            print(f"Request failed with status code {r.status_code}")

    def load_proxy_perp_addresses(self) -> List[PerpV2Directory]:
        """
        Loads proxy perp market data from a file and organizes it into memory as `PerpV2Directory` objects.

        Returns:
        `List[PerpV2Directory]`: List of PerpV2Directory objects containing market data.
        """
        # load json from data folder
        with open('data/perp_market_addresses.json', 'r') as f:
            data = json.load(f)

        # filter for key strings that start with PerpsV2Proxy
        perps_address_list: List[PerpV2Directory] = []
        for key in data['targets'].keys():
            if key.startswith('PerpsV2Proxy'):
                perpv2_directory = PerpV2Directory(
                    data['targets'][key]['name'],
                    data['targets'][key]['address'],
                    data['targets'][key]['source'],
                    data['targets'][key]['timestamp'],
                    data['targets'][key]['txn'],
                    data['targets'][key]['network'],
                    data['targets'][key]['constructorArgs'],
                )

                perps_address_list.append(perpv2_directory)
        return perps_address_list

    def clean_market_details(self, market_data: dict) -> MarketDetails:
        return MarketDetails(
            market=market_data['market'],
            baseAsset=market_data['baseAsset'].decode("utf-8").split('\x00')[0],
            marketKey=market_data['marketKey'].decode("utf-8").split('\x00')[0],
            takerFee=market_data['takerFee'] / SNX_DECIMALS,
            makerFee=market_data['makerFee'] / SNX_DECIMALS,
            takerFeeDelayedOrder=market_data['takerFeeDelayedOrder'] / SNX_DECIMALS,
            makerFeeDelayedOrder=market_data['makerFeeDelayedOrder'] / SNX_DECIMALS,
            takerFeeOffchainDelayedOrder=market_data['takerFeeOffchainDelayedOrder'] / SNX_DECIMALS,
            makerFeeOffchainDelayedOrder=market_data['makerFeeOffchainDelayedOrder'] / SNX_DECIMALS,
            maxLeverage=market_data['maxLeverage'] / SNX_DECIMALS,
            maxMarketValue=market_data['maxMarketValue'] / SNX_DECIMALS,
            maxFundingVelocity=market_data['maxFundingVelocity'] / SNX_DECIMALS,
            skewScale=market_data['skewScale'] / SNX_DECIMALS,
            marketSize=market_data['marketSize'] / SNX_DECIMALS,
            long=market_data['long'] / SNX_DECIMALS,
            short=market_data['short'] / SNX_DECIMALS,
            marketDebt=market_data['marketDebt'] / SNX_DECIMALS,
            marketSkew=market_data['marketSkew'] / SNX_DECIMALS,
            price=market_data['price'] / SNX_DECIMALS,
            invalid=market_data['invalid']
        )

    def update_market_param_df(self) -> List[MarketDetails]:
        """
        Call this periodically to retrieve a list of the most up to date market parameters. Loops through
        all market addresses and returns `List[pl.DataFrame]`
        """

        perps_addresses_list = self.load_proxy_perp_addresses()

        final_data = []

        for market in perps_addresses_list:
            raw_data = self.get_market_details(market=market.address)
            market_summary = self.clean_market_details(raw_data['results'])
            final_data.append(market_summary)

        return final_data

    def _get_block(self, block_num: int = 0):
        """
        _get_block() returns the block number and timestamp for a given block number.

        Note - Sometimes a ValueError: `header not found` error occurs. As a remedy, _get_block()
        will retry to get the latest block header indefinitely until the block number
        is confirmed to be a valid block number.
        """

        num = None

        while not isinstance(num, int):
            match block_num:
                case 0:
                    num = self.node.eth.get_block('latest').number
                    timestamp = self.node.eth.get_block('latest').timestamp
                case _:
                    num = self.node.eth.get_block(block_num).number
                    timestamp = self.node.eth.get_block(block_num).timestamp

        return num, timestamp


@dataclass
class SNXMarketData:
    """
    Class for the SNX market data.
    """
    pipe = SNXMarketPipe()

    def __post_init__(self):
        pass

    def preprocess_raw_market_summary_array(self, block=0) -> list[SNXMarketSummaryStruct]:
        """
        `preprocess_raw_market_summary_array()` replaces `combine_cleaned_market_data()` and is
        used to process raw market data obtained from `SNXMarketPipe` into `list[MarketSummaryStruct].

        - Perp markets are filtered out if they are legacy v1 perps and if they do not exist on Binance.
        """

        # TODO - raw data, replace with preprocessed data
        market_data = self.pipe.get_all_market_summaries(block)

        market_summary_array = []

        for market in market_data['results']:
            # clean raw blockchain data
            market_summary: SNXMarketSummaryStruct = self.preprocess_raw_market_summary(
                market)

            # add block info
            market_summary.block = market_data['block']
            market_summary.timestamp = market_data['timestamp']

            # filters for only perps v2 markets
            if market_summary.key.endswith("PERP"):
                market_summary_array.append(market_summary)

        return market_summary_array

    def preprocess_raw_market_summary(self, market_data: dict) -> SNXMarketSummaryStruct:
        """
        formally known as `clean_market_summaries()`.

        Clean market data and return a MarketSummary struct for a single market. 
        - Decodes bytedata into strings
        - Applies decimal converesion
        """

        # cleaned dataclass instance of market data
        return SNXMarketSummaryStruct(
            market=market_data['market'],
            asset=market_data['asset'].decode("utf-8").split('\x00')[0],
            key=market_data['key'].decode("utf-8").split('\x00')[0],
            maxLeverage=market_data['maxLeverage'] / SNX_DECIMALS,
            price=market_data['price'] / SNX_DECIMALS,
            marketSize=market_data['marketSize'] / SNX_DECIMALS,
            marketSkew=market_data['marketSkew'] / SNX_DECIMALS,
            marketDebt=market_data['marketDebt'] / SNX_DECIMALS,
            currentFundingRate=market_data['currentFundingRate'] / SNX_DECIMALS,
            currentFundingVelocity=market_data['currentFundingVelocity'] / SNX_DECIMALS,
            takerFeeOffchainDelayedOrder=market_data['takerFeeOffchainDelayedOrder'] / SNX_DECIMALS,
            makerFeeOffchainDelayedOrder=market_data['makerFeeOffchainDelayedOrder'] / SNX_DECIMALS
        )

    def transform_df(self, snx_market_df: pl.DataFrame) -> pl.DataFrame:
        """
        `transform_df() is the major preprocessing dataframe step for Synthetix. Adds
        - `premium_0`, `executionPrice`, `price_impact_full_rebalance`, `relative_market_skew_corrected_percent`, 
        `total_marketSize_usd`, `marketSkew_usd`, `proportional_marketSize_usd`, `proportional_marketSkew_usd`
        """
        # calculate price impact here
        snx_market_df = snx_market_df.with_columns(
            [
                # price impact function
                (
                    (pl.col("marketSkew") / pl.col("skewScale")).alias("premium_0")
                ),  # premium is a percent value based on `skewScale`
            ]
        )

        snx_market_df = snx_market_df.with_columns(
            [
                # executionPrice
                (
                    (pl.col("price") * (1 + 0.5 * (pl.col("premium_0") + 0))).alias(
                        "executionPrice"
                    )
                ),  # premium_1 equals 0 when skew is completely rebalanced. On polynomial, this is the 'current price'. Index price is the pyth price.
            ]
        )

        snx_market_df = snx_market_df.with_columns(
            [
                (((pl.col("executionPrice") - pl.col("price")) / pl.col("price"))).alias(
                    "price_impact_full_rebalance"
                ),
            ]
        )

        # - annual funding rate calculations
        # - relative market skew relative to the current market size of a single perp market.
        snx_market_df = snx_market_df.with_columns(
            [
                pl.from_epoch("timestamp").alias("datetime"),
                (pl.col("currentFundingVelocity") * 365 * 100).alias(
                    "yearlyFundingVelocity"
                ),  # ? Could be a useful metric to implement into pipeline (8/18/23)
                # ((pl.col("relative_market_skew") * pl.col("price"))).alias("relative_market_skew_usd"),                       # ! why doesn't this automatically calculate in pipeline? (8/18/23)
                (pl.col("marketSkew") / pl.col("marketSize")).alias(
                    "relative_market_skew_corrected_percent"
                ),
            ]
        )

        # - total/aggregate market stats (in USD)
        snx_market_df = snx_market_df.with_columns(
            [
                # total_marketSize_usd
                (
                    pl.col("marketSize_usd")
                    .sum()
                    .over("block")
                    .alias("total_marketSize_usd")
                ),
                # total_marketSkew_usd
                (
                    pl.col("marketSkew_usd")
                    .sum()
                    .over("block")
                    .alias("total_marketSkew_usd")
                ),
                # total_longs_usd
                (pl.col("long_oi_usd").sum().over("block").alias("total_long_oi_usd")),
                # total_shorts_usd
                (pl.col("short_oi_usd").sum().over("block").alias("total_short_oi_usd")),
            ]
        )

        # - proportional market stats (in USD) - proportional to total/aggregate market stats
        snx_market_df = snx_market_df.with_columns(
            [
                (pl.col("marketSize_usd") / pl.col("total_marketSize_usd")).alias(
                    "proportional_marketSize_usd"
                ),
                # not sure proportional market skew makes sense as a calculation. Probably better to stick to relative market skew usd
                (pl.col("marketSkew_usd") / pl.col("total_marketSkew_usd")).alias(
                    "proportional_marketSkew_usd"
                ),  # ! marketSkew_usd in denominator is messing up this calculation because marketSkew has both negative and positive values.
                (pl.col("long_oi_usd") / pl.col("total_long_oi_usd")).alias(
                    "proportional_long_oi_usd"
                ),
                (pl.col("short_oi_usd") / pl.col("total_short_oi_usd")).alias(
                    "proportional_short_oi_usd"
                ),
            ]
        )

        # - market param transformations
        snx_market_df = snx_market_df.with_columns(
            [
                (pl.col("maxMarketValue").alias("maxMarketValue_usd")),
                (pl.col("skewScale") / pl.col("maxMarketValue")).alias(
                    "skewScale_maxMarketValue_multiplier"
                ),
            ]
        )

        return snx_market_df
