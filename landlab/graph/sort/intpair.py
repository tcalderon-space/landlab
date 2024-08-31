from collections.abc import Collection
from collections.abc import Iterable
from collections.abc import Mapping

import numpy as np
from numpy.typing import ArrayLike

from landlab.graph.sort.ext.intpair import fill_offsets_to_sorted_blocks
from landlab.graph.sort.ext.intpair import find_pair
from landlab.graph.sort.ext.intpair import find_pairs
from landlab.graph.sort.ext.intpair import find_rolling_pairs_2d

from .ext._deprecated_sparse import map_pairs_to_values as _map_pairs_to_values
from .ext._deprecated_sparse import (
    map_rolling_pairs_to_values as _map_rolling_pairs_to_values,
)
from .ext._deprecated_sparse import pair_isin as _pair_isin


class IntPairs(Collection):
    def __init__(
        self,
        pairs: ArrayLike,
        sorter: ArrayLike | None = None,
        sorted: bool = False,
    ):
        pairs = np.atleast_2d(pairs)

        if sorter is None and not sorted:
            sorter = np.argsort(pairs[:, 0])

        if sorter is not None:
            pairs = pairs[sorter]

        self._data = pairs
        self._offsets = np.empty(pairs.max() + 2, dtype=int)

        fill_offsets_to_sorted_blocks(self._data[:, 0], self._offsets)

    def __contains__(self, pair) -> bool:
        pairs = np.atleast_2d(pair)
        result = np.asarray([-1], dtype=int)

        find_pairs(self._data, self._offsets, pairs, result)

        return result[0] >= 0

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self) -> tuple[int, int]:
        for pair in self._data:
            yield tuple(pair)

    def _find_pairs(self, pairs, out=None, wraparound=False):
        pairs = np.atleast_2d(pairs)

        if wraparound:
            shape = (pairs.shape[0], pairs.shape[1])
        else:
            shape = (pairs.shape[0], pairs.shape[1] - 1)
        result = np.full(shape, -1, dtype=int)

        # find_pairs(self._data, self._offsets, pairs, result)

        find_rolling_pairs_2d(self._data, self._offsets, pairs, result, int(wraparound))

        return result

    def contains_keys(self, pairs, wraparound=False):
        return self._find_pairs(pairs, wraparound=wraparound) >= 0


class IntPairMapping(Mapping, IntPairs):
    def __init__(
        self,
        pairs: ArrayLike,
        values: ArrayLike,
        sorter: ArrayLike | None = None,
        sorted: bool = False,
    ) -> None:
        pairs = np.atleast_2d(pairs)

        if sorter is None and not sorted:
            sorter = np.argsort(pairs[:, 0])

        if sorter is not None:
            pairs = pairs[sorter]
            values = values[sorter]

        self._values = values
        self._data = pairs
        self._offsets = np.empty(pairs.max() + 2, dtype=int)

        fill_offsets_to_sorted_blocks(self._data[:, 0], self._offsets)

    def __getitem__(self, key: Iterable[int]):
        ind = find_pair(self._data, self._offsets, key[0], key[1])
        if ind == -1:
            ind = find_pair(self._data, self._offsets, key[1], key[0])
        if ind == -1:
            raise KeyError(key)
        else:
            return self._values[ind]

    def get_items(self, keys, out=None, wraparound=False):
        keys = np.atleast_2d(keys)

        if wraparound:
            shape = (keys.shape[0], keys.shape[1])
        else:
            shape = (keys.shape[0], keys.shape[1] - 1)

        if out is None:
            out = np.empty(shape, dtype=self._values.dtype)

        result = np.full(shape, -1, dtype=int)

        find_rolling_pairs_2d(
            self._data,
            self._offsets,
            keys,
            result,
            int(wraparound),
        )

        out[:] = self._values[result]
        out[result == -1] = -1

        return out


def pair_isin(src, pairs, out=None, sorter=None, sorted=False):
    if not sorted and sorter is None:
        sorter = np.argsort(src[:, 0])
    if sorter is not None:
        src = src[sorter]

    offsets = np.empty(pairs.max() + 2, dtype=int)
    fill_offsets_to_sorted_blocks(src[:, 0], offsets)

    result = np.empty(len(pairs), dtype=int)

    find_pairs(src, offsets, pairs, result)

    if out is None:
        out = result >= 0
    else:
        out[:] = result >= 0

    return out


def __pair_isin(src, pairs, out=None, sorter=None, sorted=False):
    """Check if integer-pairs are contained in source set.

    Parameters
    ----------
    src : ndarray of int, size *(N, 2)*
        Integer pairs that form the source set.
    pairs : ndarray of int, size *(M, 2)*
        Integer pairs to check if they are contained in the source set.
    out : ndarray of bool, size *(M,)*, optional
        Buffer to place the result. If not provided, a new array will be allocated.
    sorter : ndarray of int, size *(N,)*, optional
        Array of indices that sorts the *src*, as would be returned by *argsort*.
        If not provided, *src* is assumed to already be sorted.
    sorted : bool, optional
        Indicate if the source pairs are already sorted.

    Returns
    -------
    ndarray of bool
        Array that indicates if the pair is contained in the source set.
    """
    if not sorted and sorter is None:
        sorter = np.argsort(src[:, 0])
    if sorter is not None:
        src = src[sorter]

    result = np.empty(len(pairs), dtype=np.uint8)
    _pair_isin(np.ascontiguousarray(src), np.ascontiguousarray(pairs), result)

    if out is None:
        out = result.astype(dtype=bool, copy=False)
    else:
        out[:] = result.astype(dtype=bool, copy=False)
    return out


def map_pairs_to_values(mapping, pairs, out=None, sorter=None, sorted=False):
    """Return the values for integer pairs from a mapping.

    Parameters
    ----------
    mapping : tuple of ndarray of int
        Integer pair to value mapping as *(pairs, values)* where *pairs* is
        *ndarray* of shape *(M, 2)* and *values* an array of length *M*.
    pairs : ndarray of int of shape *(N, 2)*
        Integer pairs to get the values of.
    out : ndarray of bool, size *(N,)*, optional
        Buffer to place the result. If not provided, a new array will be allocated.
    sorter : ndarray of int, size *(M,)*, optional
        Array of indices that sorts the *src*, as would be returned by *argsort*.
        If not provided, *src* is assumed to already be sorted.
    sorted : bool, optional
        Indicate if the mapping key pairs are already sorted.

    Returns
    -------
    ndarray of int
        Array of values of the given integer pairs.

    Examples
    --------
    >>> from landlab.graph.sort.intpair import map_pairs_to_values

    >>> keys = [[0, 1], [1, 1], [2, 1], [3, 1], [4, 1]]
    >>> values = [0, 10, 20, 30, 40]
    >>> pairs = [[1, 1], [3, 1]]
    >>> map_pairs_to_values((keys, values), pairs)
    array([10, 30])
    """
    keys, values = np.asarray(mapping[0]), np.asarray(mapping[1])
    pairs = np.asarray(pairs)

    if out is None:
        out = np.empty(len(pairs), dtype=values.dtype)

    if not sorted and sorter is None:
        sorter = np.argsort(keys[:, 0])

    if sorter is not None:
        keys = keys[sorter]
        values = values[sorter]

    offsets = np.empty(pairs.max() + 2, dtype=int)
    fill_offsets_to_sorted_blocks(keys[:, 0], offsets)

    result = np.empty(len(pairs), dtype=int)

    find_pairs(keys, offsets, pairs, result)

    out[:] = values[result]
    out[result == -1] = -1

    return out


def __map_pairs_to_values(mapping, pairs, out=None, sorter=None, sorted=False):
    """Return the values for integer pairs from a mapping.

    Parameters
    ----------
    mapping : tuple of ndarray of int
        Integer pair to value mapping as *(pairs, values)* where *pairs* is
        *ndarray* of shape *(M, 2)* and *values* an array of length *M*.
    pairs : ndarray of int of shape *(N, 2)*
        Integer pairs to get the values of.
    out : ndarray of bool, size *(N,)*, optional
        Buffer to place the result. If not provided, a new array will be allocated.
    sorter : ndarray of int, size *(M,)*, optional
        Array of indices that sorts the *src*, as would be returned by *argsort*.
        If not provided, *src* is assumed to already be sorted.
    sorted : bool, optional
        Indicate if the mapping key pairs are already sorted.

    Returns
    -------
    ndarray of int
        Array of values of the given integer pairs.

    Examples
    --------
    >>> from landlab.graph.sort.intpair import map_pairs_to_values

    >>> keys = [[0, 1], [1, 1], [2, 1], [3, 1], [4, 1]]
    >>> values = [0, 10, 20, 30, 40]
    >>> pairs = [[1, 1], [3, 1]]
    >>> map_pairs_to_values((keys, values), pairs)
    array([10, 30])
    """
    keys, values = np.asarray(mapping[0]), np.asarray(mapping[1])
    pairs = np.asarray(pairs)

    if out is None:
        out = np.empty(len(pairs), dtype=values.dtype)

    if not sorted and sorter is None:
        sorter = np.argsort(keys[:, 0])
    if sorter is not None:
        keys = keys[sorter]
        values = values[sorter]

    _map_pairs_to_values(
        np.ascontiguousarray(keys), np.ascontiguousarray(values), pairs, out
    )

    return out


def map_rolling_pairs_to_values(
    mapping,
    pairs,
    out=None,
    sorter=None,
    sorted=False,
    size_of_row=None,
    wraparound=True,
):
    keys, values = np.asarray(mapping[0]), np.asarray(mapping[1])
    pairs = np.asarray(pairs)

    if out is None:
        out = np.empty_like(pairs, dtype=int)

    if size_of_row is None:
        size_of_row = np.full(len(pairs), pairs.shape[1], dtype=int)
    else:
        size_of_row = np.asarray(size_of_row)
        out[:] = -1

    if not sorted and sorter is None:
        sorter = np.argsort(keys[:, 0])
    if sorter is not None:
        keys = keys[sorter]
        values = values[sorter]

    offsets = np.empty(pairs.max() + 2, dtype=int)
    fill_offsets_to_sorted_blocks(keys[:, 0], offsets)

    result = np.full(pairs.shape, -1, dtype=int)

    find_rolling_pairs_2d(
        keys,
        offsets,
        pairs,
        result,
        bool(wraparound),
    )

    out[:] = values[result]
    out[result == -1] = -1

    # _map_rolling_pairs_to_values(
    #     np.ascontiguousarray(keys),
    #     np.ascontiguousarray(values),
    #     np.ascontiguousarray(pairs),
    #     np.ascontiguousarray(size_of_row),
    #     out,
    # )

    return out


def __map_rolling_pairs_to_values(
    mapping, pairs, out=None, sorter=None, sorted=False, size_of_row=None
):
    """Return the values for integer pairs given as a 2D matrix of rolling
    pairs.

    Parameters
    ----------
    mapping : tuple of ndarray of int
        Integer pair to value mapping as *(pairs, values)* where *pairs* is
        *ndarray* of shape *(N, 2)* and *values* an array of length *N*.
    pairs : ndarray of int of shape *(M, L)*
        Integer pairs to get the values of.
    out : ndarray of bool, size *(M, L)*, optional
        Buffer to place the result. If not provided, a new array will be allocated.
    sorter : ndarray of int, size *(N,)*, optional
        Array of indices that sorts the *src*, as would be returned by *argsort*.
        If not provided, *src* is assumed to already be sorted.
    sorted : bool, optional
        Indicate if the mapping key pairs are already sorted.

    Returns
    -------
    ndarray of int
        Array of values of the given integer pairs.

    Examples
    --------
    >>> from landlab.graph.sort.intpair import map_rolling_pairs_to_values

    >>> keys = [[0, 1], [1, 2], [2, 3], [3, 4], [4, 0]]
    >>> values = [0, 10, 20, 30, 40]
    >>> pairs = [[0, 1, 2, 3], [0, 2, 3, 4]]
    >>> map_rolling_pairs_to_values((keys, values), pairs)
    array([[ 0, 10, 20, -1],
           [-1, 20, 30, 40]])
    """
    keys, values = np.asarray(mapping[0]), np.asarray(mapping[1])
    pairs = np.asarray(pairs)

    if out is None:
        out = np.empty_like(pairs, dtype=int)

    if size_of_row is None:
        size_of_row = np.full(len(pairs), pairs.shape[1], dtype=int)
    else:
        size_of_row = np.asarray(size_of_row)
        out[:] = -1

    if not sorted and sorter is None:
        sorter = np.argsort(keys[:, 0])
    if sorter is not None:
        keys = keys[sorter]
        values = values[sorter]

    _map_rolling_pairs_to_values(
        np.ascontiguousarray(keys),
        np.ascontiguousarray(values),
        np.ascontiguousarray(pairs),
        np.ascontiguousarray(size_of_row),
        out,
    )

    return out
