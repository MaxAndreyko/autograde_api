import pandas as pd

def dict_to_df(send_data: dict) -> pd.DataFrame:
    """Transforms input dictionary to pandas dataframe

    Parameters
    ----------
    send_data : dict
        Input dictionary

    Returns
    -------
    pd.DataFrame
        Pandas dataframe formed from input dict
    """
    return pd.DataFrame(send_data, index=[0])


def form_send_request_body(k1: int, k2: int, k3: dict) -> dict:
    """Forms output request body with score predictions

    Parameters
    ----------
    k1 : int
        K1-criterion score
    k2 : int
        K2-criterion score
    k3 : dict
        K3-criterion score with comments

    Returns
    -------
    dict
        Predicted scores dictionary
    """
    body = {
        "k1": str(k1),
        "k2": k2,
        "k3": k3
    }
    return body