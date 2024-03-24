from typing import Dict, List


def get_none_keys(dict: Dict) -> List:
    """Gets keys of None values from dictionary

    Args:
        dict (Dict): Any dictionary

    Returns:
        List: List with keys of None values
    """
    return [key for key, value in dict.items() if value is None]
