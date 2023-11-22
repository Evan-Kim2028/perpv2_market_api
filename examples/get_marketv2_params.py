import json

from perpv2_market_api.market_pipe import SNXMarketPipe

pipe = SNXMarketPipe()
# pipe.update_market_param_df()

perps_addresses_list = pipe.load_proxy_perp_addresses()

updated_params = pipe.update_market_param_df()

updated_params_dict: list[dict] = [market.to_dict() for market in updated_params]

# Specify the file path
file_path = 'data/perp_market_params.json'

# Write the list of dictionaries to a JSON file
with open(file_path, 'w') as json_file:
    json.dump(updated_params_dict, json_file, indent=2)

# Confirm the successful write
print(f"Data successfully saved to {file_path}")
