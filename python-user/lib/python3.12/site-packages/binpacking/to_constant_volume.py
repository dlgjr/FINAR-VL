from typing import Any, Callable, Iterable, overload

from binpacking.utilities import (
    load_csv,
    save_csvs,
    print_binsizes,
    get,
    argmin,
    revargsort,
)


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
    """Load a CSV file, bin-pack rows by weight column, write output CSVs."""
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


@overload
def to_constant_volume(
    d: Iterable[Any],
    V_max: float,
    weight_pos: int | None = None,
    key: Callable[[Any], float] | None = None,
    lower_bound: float | None = None,
    upper_bound: float | None = None,
) -> list[list[Any]]: ...


def to_constant_volume(
    d: dict[str, float] | list[float] | Iterable[Any],
    V_max: float,
    weight_pos: int | None = None,
    key: Callable[[Any], float] | None = None,
    lower_bound: float | None = None,
    upper_bound: float | None = None,
) -> list[dict[str, float]] | list[list[float]] | list[list[Any]]:
    """
    Distribute items to minimum number of bins with fixed maximum volume.

    Parameters
    ----------
    d : iterable
        list containing weights,
        OR dictionary where each (key,value)-pair carries the weight as value,
        OR list of tuples where one entry in the tuple is the weight. The position of
        this weight has to be given in optional variable weight_pos
    V_max : float
        Fixed bin volume
    weight_pos : int, optional
        if d is a list of tuples, this integer number gives the position of the weight in a tuple
    key : callable, optional
        if d is a list, this key function grabs the weight for an item
    lower_bound : float, optional
        weights under this bound are not considered
    upper_bound : float, optional
        weights exceeding this bound are not considered

    Returns
    -------
    bins : list
        A list. Each entry is a list of items or
        a dict of items, depending on the type of ``d``.
    """
    isdict = isinstance(d, dict)

    if not hasattr(d, '__len__'):
        raise TypeError("d must be iterable")

    # Handle empty input
    if len(d) == 0:  # type: ignore[arg-type]
        if isdict:
            return [{}]
        else:
            return [[]]

    if not isdict and hasattr(d[0], '__len__'):  # type: ignore[index]
        if weight_pos is not None:
            key = lambda x: x[weight_pos]
        if key is None:
            raise ValueError("Must provide weight_pos or key for tuple list")

    if not isdict and key:
        new_dict = {i: val for i, val in enumerate(d)}  # type: ignore[arg-type]
        d = {i: key(val) for i, val in enumerate(d)}  # type: ignore[arg-type, union-attr]
        isdict = True
        is_tuple_list = True
    else:
        is_tuple_list = False

    if isdict:
        # get keys and values (weights)
        keys_vals = d.items()  # type: ignore[union-attr]
        keys = [k for k, v in keys_vals]
        vals = [v for k, v in keys_vals]

        # sort weights decreasingly
        ndcs = revargsort(vals)

        weights = get(vals, ndcs)
        keys = get(keys, ndcs)

        bins: list[Any] = [{}]
    else:
        weights = sorted(d, key=lambda x: -x)  # type: ignore[arg-type]
        bins = [[]]

    # find the valid indices
    # First check for invalid bounds
    if lower_bound is not None and upper_bound is not None and lower_bound >= upper_bound:
        raise Exception("lower_bound is greater or equal to upper_bound")

    if lower_bound is not None and upper_bound is not None:
        valid_ndcs = filter(lambda i: lower_bound <= weights[i] <= upper_bound, range(len(weights)))
    elif lower_bound is not None:
        valid_ndcs = filter(lambda i: lower_bound <= weights[i], range(len(weights)))
    elif upper_bound is not None:
        valid_ndcs = filter(lambda i: weights[i] <= upper_bound, range(len(weights)))
    else:
        valid_ndcs = range(len(weights))  # type: ignore[assignment]

    valid_ndcs = list(valid_ndcs)

    weights = get(weights, valid_ndcs)

    if isdict:
        keys = get(keys, valid_ndcs)

    # the total volume is the sum of all weights
    V_total = sum(weights)

    # prepare array containing the current weight of the bins
    weight_sum = [0.]

    # iterate through the weight list, starting with heaviest
    for item, weight in enumerate(weights):

        if isdict:
            key = keys[item]  # type: ignore[assignment]

        # find candidate bins where the weight might fit
        candidate_bins = list(filter(lambda i: weight_sum[i] + weight <= V_max, range(len(weight_sum))))

        # if there are candidates where it fits
        if len(candidate_bins) > 0:
            # find the emptiest bin where this item fits (Least Loaded Fit)
            candidate_index = argmin(get(weight_sum, candidate_bins))
            b = candidate_bins[candidate_index]

        # if this weight doesn't fit in any existent bin
        elif item > 0:
            # note! if this is the very first item then there is already an
            # empty bin open so we don't need to open another one.

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
            bins[b].append(weight)

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


if __name__ == "__main__":
    import numpy as np

    a = np.random.power(0.01, size=10000)
    V_max = 1.

    bins = to_constant_volume(a, V_max)

    a = np.sort(a)[::-1]
    print(a[:10])
    print([np.sum(b) for b in bins])
    print(a.sum(), sum([np.sum(b) for b in bins]))

    w = [np.sum(b) for b in bins]

    import matplotlib.pyplot as pl
    pl.plot(np.arange(len(w)), w)

    b = {'a': 10, 'b': 10, 'c': 11, 'd': 1, 'e': 2, 'f': 7}
    V_max = max(b.values())

    bins = to_constant_volume(b, V_max)
    print(bins)

    import time
    start = time.time()
    for i in range(100):
        bins = to_constant_volume(a, V_max)
    end = time.time()
    print("needed", end - start, "sec")

    c = [('a', 10, 'foo'), ('b', 10, 'log'), ('c', 11), ('d', 1, 'bar'), ('e', 2, 'bommel'), ('f', 7, 'floggo')]
    V_max = max(c, key=lambda x: x[1])[1]

    bins = to_constant_volume(c, V_max, weight_pos=1)
    print(bins)

    import time
    start = time.time()
    for i in range(100):
        bins = to_constant_volume(a, V_max)
    end = time.time()
    print("needed", end - start, "sec")

    pl.show()
