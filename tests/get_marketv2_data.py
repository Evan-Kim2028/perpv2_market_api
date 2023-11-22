from perpv2_market_api.market_pipe import SNXMarketData
from perpv2_market_api.data_structs import SNXMarketSummaryStruct

# get current market data for the latest block
snx_pipe = SNXMarketData()

# query market data
snx_market_data: list[SNXMarketSummaryStruct] = snx_pipe.preprocess_raw_market_summary_array(
    block=112033711)

# for market in snx_market_data:
#     print('\n', market)

print(len(snx_market_data))


# convert to dataframe
df = snx_market_data


print('done')
