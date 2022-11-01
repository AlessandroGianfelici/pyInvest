import pandas as pd
import os


def load_symbols(filename : str):
    filepath = os.path.join(os.path.dirname(__file__), 'symbols', filename)
    return pd.read_csv(filepath)

def load_borsa_italiana_stocks_symbols():
    return load_symbols('borsa_italiana.csv')

def load_yaml(filename: str) -> dict:
    """
    Utility function to load a yaml file into a pyhon dict
    Parameters:
    - filename: str -> fullpath of the yaml file
    """
    assert filename.endswith("yaml") or filename.endswith(
        "yml"
    ), "Not a yaml extention!"
    with open(filename, "r", encoding="utf-8") as handler:
        return yaml.load(handler, Loader=yaml.FullLoader)