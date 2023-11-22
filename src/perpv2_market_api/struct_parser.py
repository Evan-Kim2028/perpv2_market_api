

# Helper module with functions to parse struct name data to label and flatten blockchain data from web3py.


def get_function_components(abi, function: str) -> list[dict]:
    """
    extract function components from abi by searching for function name
    """

    function_components = []

    for i in range(len(abi)):
        try:
            if abi[i]['name'] == function:
                function_components = abi[i]['outputs'][0]['components']
        except KeyError:
            # print(f"KeyError: {abi[i]} does not have 'outputs' key. \nAvailable keys: {abi[i].keys()}")
            pass
    
    match function_components:
        case []:
            print(f"Error: {function} not found in abi.")
            return []
        case _:
            return function_components

def extract_names(abi, function: str) -> list[str]:
    """
    Extract function output names from abi. Parse through abi structure to extract names from function components
    """

    data = get_function_components(abi, function)


    output_names = []
    
    def extract_names_recursive(data: list[dict]):
        """Handles recursive search to account for possible doubly nested structs"""
        match data:
            case []:
                print(f"Error: data is empty: {data}.")
                return []
            case _:
                for elem in data:
                    output_names.append(elem['name'])
                    # if components exists, then name is a struct type and needs to be recursed to get struct field names.
                    if 'components' in elem: 
                        output_names.pop()
                        extract_names_recursive(elem['components'])


    extract_names_recursive(data)             

    return output_names


def flatten_list(data: list) -> list:
    """
    flattens a list with nested tuples into a list recursively
    """
    flattened_data = []
    for item in data:
        if isinstance(item, tuple):
            flattened_data.extend(flatten_list(item))
        else:
            flattened_data.append(item)
    return flattened_data