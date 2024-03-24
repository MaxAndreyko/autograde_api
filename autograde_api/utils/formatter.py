from typing import Dict, Union

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
    body = {"k1": str(k1), "k2": k2, "k3": k3}
    return body


def format_prediction_request(data: Dict[str, str]) -> str:
    """Formats prediction request strings

    Args:
        data (Dict[str, str]): Raw prediction request with "Question" and "Text"

    Returns:
        str: Formatted prediction request
    """
    formatted_values = [
        "<b>Вопрос:</b><br>" + data["Question"].replace("\n", "<br>"),
        "<b>Ответ:</b><br>" + data["Text"].replace("\n", "<br>"),
    ]
    return "<br><br><br>".join(formatted_values)


def format_prediction_result(data: Dict[str, Union[int, str]]) -> str:
    """Formats prediction request strings

    Args:
        data (Dict[str, str]): Raw prediction result with scores and comments

    Returns:
        str: Formatted prediction result
    """
    formatted_values = [
        "<b>Критерий 1:</b> " + str(data["k1"]),
        "<b>Критерий 2:</b> " + str(data["k2"]),
        "<b>Критерий 3:</b> " + str(data["k3"]),
        "<b>Комментарии:</b><br>" + data["comments"].replace("\n", "<br>"),
    ]
    return "<br>".join(formatted_values)
