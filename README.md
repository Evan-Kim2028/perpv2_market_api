# perpv2_market_api

This is an API for fetching Synthetix Perps v2 market data. Mirrors the data found on [polynomial markets](https://trade.polynomial.fi/markets)

### Installation
To install the required files, clone the repository, make a virtual environment via `python3 -m venv .venv`, activate the environment `source .venv/bin/activate` and install required libraries via `pip install -e .` To setup the node endpoint, make a `.env` file and set the variable like this `OPTIMISM_RPC='https://rpc.ankr.com/optimism'`. Note that this is a free archive rpc endpoint from ankr. See more information [here](https://www.ankr.com/rpc/chains/optimism).

### Usage
The important examples are in the `examples` folder. 

- `get_v2_market_addresses.py` - get proxy adresses for all perps v2 markets, saves as a .json file to the `data` folder.
- `get_marketv2_params.py` - get market parameters directly from the github repository. Saves as a .json file to the `data` folder. Note these params only reflect the most current market parameters.
- `data_notebook.ipynb` - example notebook that shows querying the perpsv2 market data, param data, and calculating the premium/discount price. Data is transformed using polars dataframes. 