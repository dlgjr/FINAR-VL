"""NumPy-accelerated bin packing algorithms.

This module provides the same API as the main binpacking module,
but uses NumPy for better performance on large datasets.

Usage:
    from binpacking.numpy import to_constant_volume, to_constant_bin_number

Requires numpy to be installed:
    pip install binpacking[numpy]
"""

from typing import Any, Callable, overload

try:
    import numpy as np
except ImportError as e:
    raise ImportError(
        "NumPy is required for binpacking.numpy. "
        "Install it with: pip install binpacking[numpy]"
    ) from e

from binpacking.utilities import load_csv, save_csvs, print_binsizes


@overload
def to_constant_volume(
    d: dict[str, float],
    V_max: float,
    weight_pos: int | None = None,
    key: Callable[[Any], float] | None = None,
    lower_bound: float | None = None,
    upper_bound: float | None = None,
) -> list[dict[str, float]]: ...


@overload
def to_constant_volume(
    d: list[float],
    V_max: float,
    weight_pos: int | None = None,
    key: Callable[[Any], float] | None = None,
    lower_bound: float | None = None,
    upper_bound: float | None = None,
) -> list[list[float]]: ...


def to_constant_volume(
    d: dict[str, float] | list[float] | list[Any],
    V_max: float,
    weight_pos: int | None = None,
    key: Callable[[Any], float] | None = None,
    lower_bound: float | None = None,
    upper_bound: float | None = None,
) -> list[dict[str, float]] | list[list[float]] | list[list[Any]]:
    """
    Distribute items to minimum number of bins with fixed maximum volume.

    NumPy-accelerated version for better performance on large datasets.

    Parameters
    ----------
    d : iterable
        list containing weights,
        OR dictionary where each (key,value)-pair carries the weight as value,
        OR list of tuples where one entry in the tuple is the weight
    V_max : float
        Fixed bin volume
    weight_pos : int, optional
        if d is a list of tuples, the position of the weight in a tuple
    key : callable, optional
        if d is a list, this key function extracts the weight for an item
    lower_bound : float, optional
        weights under this bound are not considered
    upper_bound : float, optional
        weights exceeding this bound are not considered

    Returns
    -------
    bins : list
        A list of bins, each containing items from the input.
    """
    isdict = isinstance(d, dict)

    if not hasattr(d, '__len__'):
        raise TypeError("d must be iterable")

    # Handle empty input
    if len(d) == 0:
        if isdict:
            return [{}]
        else:
            return [[]]

    if not isdict and hasattr(d[0], '__len__'):
        if weight_pos is not None:
            key = lambda x: x[weight_pos]
        if key is None:
            raise ValueError("Must provide weight_pos or key for tuple list")

    if not isdict and key:
        new_dict = {i: val for i, val in enumerate(d)}
        d = {i: key(val) for i, val in enumerate(d)}
        isdict = True
        is_tuple_list = True
    else:
        is_tuple_list = False

    if isdict:
        # get keys and values (weights)
        keys_vals = d.items()
        keys = np.array([k for k, v in keys_vals])
        vals = np.array([v for k, v in keys_vals])

        # sort weights decreasingly
        ndcs = np.argsort(vals)[::-1]

        weights = vals[ndcs]
        keys = keys[ndcs]

        bins: list[Any] = [{}]
    else:
        weights = np.sort(np.array(d))[::-1]
        bins = [[]]

    # find the valid indices
    if lower_bound is not None and upper_bound is not None and lower_bound >= upper_bound:
        raise Exception("lower_bound is greater or equal to upper_bound")

    if lower_bound is not None and upper_bound is not None:
        valid_ndcs = np.nonzero(np.logical_and(weights >= lower_bound, weights <= upper_bound))[0]
    elif lower_bound is not None:
        valid_ndcs = np.nonzero(weights >= lower_bound)[0]
    elif upper_bound is not None:
        valid_ndcs = np.nonzero(weights <= upper_bound)[0]
    else:
        valid_ndcs = np.arange(len(weights), dtype=int)

    weights = weights[valid_ndcs]

    if isdict:
        keys = keys[valid_ndcs]

    # prepare array containing the current weight of the bins
    weight_sum = [0.]

    # iterate through the weight list, starting with heaviest
    for item, weight in enumerate(weights):

        if isdict:
            key = keys[item]

        # find candidate bins where the weight might fit
        candidate_bins = [i for i in range(len(weight_sum)) if weight_sum[i] + weight <= V_max]

        # if there are candidates where it fits
        if len(candidate_bins) > 0:
            # find the emptiest bin where this item fits (Least Loaded Fit)
            candidate_weights = [weight_sum[i] for i in candidate_bins]
            candidate_index = int(np.argmin(candidate_weights))
            b = candidate_bins[candidate_index]

        # if this weight doesn't fit in any existent bin
        elif item > 0:
            # open a new bin
            b = len(weight_sum)
            weight_sum.append(0.)
            if isdict:
                bins.append({})
            else:
                bins.append([])

        # if we are at the very first item, use the empty bin already open
        else:
            b = 0

        # put it in
        if isdict:
            bins[b][key] = weight
        else:
            bins[b].append(float(weight))

        # increase weight sum of the bin and continue with next item
        weight_sum[b] += weight

    if not is_tuple_list:
        return bins
    else:
        new_bins = []
        for b in range(len(bins)):
            new_bins.append([])
            for _key in bins[b]:
                new_bins[b].append(new_dict[_key])
        return new_bins


@overload
def to_constant_bin_number(
    d: dict[str, float],
    N_bin: int,
    weight_pos: int | None = None,
    key: Callable[[Any], float] | None = None,
    lower_bound: float | None = None,
    upper_bound: float | None = None,
) -> list[dict[str, float]]: ...


@overload
def to_constant_bin_number(
    d: list[float],
    N_bin: int,
    weight_pos: int | None = None,
    key: Callable[[Any], float] | None = None,
    lower_bound: float | None = None,
    upper_bound: float | None = None,
) -> list[list[float]]: ...


def to_constant_bin_number(
    d: dict[str, float] | list[float] | list[Any],
    N_bin: int,
    weight_pos: int | None = None,
    key: Callable[[Any], float] | None = None,
    lower_bound: float | None = None,
    upper_bound: float | None = None,
) -> list[dict[str, float]] | list[list[float]] | list[list[Any]]:
    """
    Distribute items to a fixed number of bins with balanced weights.

    NumPy-accelerated version for better performance on large datasets.

    Parameters
    ----------
    d : iterable
        list containing weights,
        OR dictionary where each (key,value)-pair carries the weight as value,
        OR list of tuples where one entry in the tuple is the weight
    N_bin : int
        Number of bins to distribute items to.
    weight_pos : int, optional
        if d is a list of tuples, the position of the weight in a tuple
    key : callable, optional
        if d is a list, this key function extracts the weight for an item
    lower_bound : float, optional
        weights under this bound are not considered
    upper_bound : float, optional
        weights exceeding this bound are not considered

    Returns
    -------
    bins : list
        A list of length ``N_bin``, each containing items from the input.
    """
    isdict = isinstance(d, dict)

    if not hasattr(d, '__len__'):
        raise TypeError("d must be iterable")

    # Handle empty input
    if len(d) == 0:
        if isdict:
            return [{} for _ in range(N_bin)]
        else:
            return [[] for _ in range(N_bin)]

    if not isdict and hasattr(d[0], '__len__'):
        if weight_pos is not None:
            key = lambda x: x[weight_pos]
        if key is None:
            raise ValueError("Must provide weight_pos or key for tuple list")

    if not isdict and key:
        new_dict = {i: val for i, val in enumerate(d)}
        d = {i: key(val) for i, val in enumerate(d)}
        isdict = True
        is_tuple_list = True
    else:
        is_tuple_list = False

    if isdict:
        # get keys and values (weights)
        keys_vals = d.items()
        keys = np.array([k for k, v in keys_vals])
        vals = np.array([v for k, v in keys_vals])

        # sort weights decreasingly
        ndcs = np.argsort(vals)[::-1]

        weights = vals[ndcs]
        keys = keys[ndcs]

        bins: list[Any] = [{} for _ in range(N_bin)]
    else:
        weights = np.sort(np.array(d))[::-1]
        bins = [[] for _ in range(N_bin)]

    # find the valid indices
    if lower_bound is not None and upper_bound is not None and lower_bound >= upper_bound:
        raise Exception("lower_bound is greater or equal to upper_bound")

    if lower_bound is not None and upper_bound is not None:
        valid_ndcs = np.nonzero(np.logical_and(weights >= lower_bound, weights <= upper_bound))[0]
    elif lower_bound is not None:
        valid_ndcs = np.nonzero(weights >= lower_bound)[0]
    elif upper_bound is not None:
        valid_ndcs = np.nonzero(weights <= upper_bound)[0]
    else:
        valid_ndcs = np.arange(len(weights), dtype=int)

    weights = weights[valid_ndcs]

    if isdict:
        keys = keys[valid_ndcs]

    # prepare array containing the current weight of the bins
    weight_sum = np.zeros(N_bin)

    # iterate through the weight list, starting with heaviest
    # Pure LPT: always place in the bin with lowest weight sum
    for item, weight in enumerate(weights):

        if isdict:
            key = keys[item]

        # put next value in bin with lowest weight sum
        b = int(np.argmin(weight_sum))

        # place the item
        if isdict:
            bins[b][key] = weight
        else:
            bins[b].append(float(weight))

        # update weight sum of the bin
        weight_sum[b] += weight

    if not is_tuple_list:
        return bins
    else:
        new_bins = []
        for b in range(N_bin):
            new_bins.append([])
            for _key in bins[b]:
                new_bins[b].append(new_dict[_key])
        return new_bins


def csv_to_constant_volume(
    filepath: str,
    weight_column: int | str,
    V_max: float,
    has_header: bool = False,
    delim: str = ',',
    quotechar: str = '"',
    lower_bound: float | None = None,
    upper_bound: float | None = None,
    output_dir: str | None = None,
) -> None:
    """Load a CSV file, bin-pack rows by weight column, write output CSVs.

    NumPy-accelerated version.
    """
    data, weight_column, header = load_csv(
        filepath,
        weight_column,
        has_header=has_header,
        delim=delim,
        quotechar=quotechar,
    )

    bins = to_constant_volume(
        data,
        V_max,
        weight_pos=weight_column,
        lower_bound=lower_bound,
        upper_bound=upper_bound,
    )

    print_binsizes(bins, weight_column)

    save_csvs(
        bins,
        filepath,
        header,
        delim=delim,
        quotechar=quotechar,
        output_dir=output_dir,
    )


def csv_to_constant_bin_number(
    filepath: str,
    weight_column: int | str,
    N_bin: int,
    has_header: bool = False,
    delim: str = ',',
    quotechar: str = '"',
    lower_bound: float | None = None,
    upper_bound: float | None = None,
    output_dir: str | None = None,
) -> None:
    """Load a CSV file, bin-pack rows to N bins, write output CSVs.

    NumPy-accelerated version.
    """
    data, weight_column, header = load_csv(
        filepath,
        weight_column,
        has_header=has_header,
        delim=delim,
        quotechar=quotechar,
    )

    bins = to_constant_bin_number(
        data,
        N_bin,
        weight_pos=weight_column,
        lower_bound=lower_bound,
        upper_bound=upper_bound,
    )

    print_binsizes(bins, weight_column)

    save_csvs(
        bins,
        filepath,
        header,
        delim=delim,
        quotechar=quotechar,
        output_dir=output_dir,
    )


__all__ = [
    'to_constant_volume',
    'to_constant_bin_number',
    'csv_to_constant_volume',
    'csv_to_constant_bin_number',
]
