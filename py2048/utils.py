"""Here lie the helper functions"""
import numpy as np
from typing import Union


class NoFreeCells(ValueError):
    ...


class UnknownSessionID(FileNotFoundError):
    ...


class VisualisationError(Exception):
    ...


def mutstr(base: str, ind: int, val: str):
    if len(base) <= ind:
        raise ValueError(f"Asked to change the character nr. {ind} in a string of only {base.__len__()} chars.")
    return base[:ind] + val + base[ind + 1:]


def nparr_to_dict(data: np.ndarray) -> dict:
    """ Break a (n x n) array into n arrays of n values """
    return {f"row_{i}": [int(x) for x in row] for i, row in enumerate(data)}


def dict_to_nparr(data: dict) -> np.ndarray:
    n_row, n_col = len(data), len(data[0])
    op = np.zeros((n_row, n_row), dtype=np.int)
    for i, row in enumerate(data):
        op[i] = row
    return op


class FancyDict(dict):
    """
        A dictionary that can be invoked both by:
            instance['key'] and instance.key. For both, getting and setting values.

        It is still serializable, and can be initialized like
        ```
            a = FancyDict()
            a.key1 = value1
            a.key2 = value2
        ```
        Or
        ```
            a = FancyDict(key1=value1, key2=value2)
        ```
        Or (which is technically functionally the same as above)
        ```
            a = FancyDict(**{'key1': 'value1', 'key2': 'value2'})
        ```
    """

    def __getattr__(self, item: Union[str, int]):
        if isinstance(item, str) and item.startswith('__') and item.endswith('__'):
            super().__getattr__(item)
        return self[item]

    # def __getattribute__(self, item):
    #     if item in self:
    #         self[item]
    #     else:
    #         object.__getattribute__(self, item)

    def __setattr__(self, key, value):
        self[key] = value
