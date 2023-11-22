import solcx
import json

# Run this script to install solidity 0.5.16 and generate abis for Synthetix contracts.

# NOTE - requires the synthetix contracts to work
# ! install solidity 0.5.16:
solcx.install_solc('0.5.16')


results = solcx.compile_files(
    ["contracts/interfaces/IPerpsV2MarketConsolidated.sol"],
    output_values=["abi", "bin-runtime"],
    solc_version="0.5.16"
)


# print abi
print(results['contracts/interfaces/IPerpsV2MarketConsolidated.sol:IPerpsV2MarketConsolidated']["abi"])

print(type(
    results['contracts/interfaces/IPerpsV2MarketConsolidated.sol:IPerpsV2MarketConsolidated']["abi"]))
print('done')


# save abi to json in abi folder
with open('abi/IPerpsV2MarketConsolidated.json', 'w') as f:
    json.dump(
        results['contracts/interfaces/IPerpsV2MarketConsolidated.sol:IPerpsV2MarketConsolidated']["abi"], f)
