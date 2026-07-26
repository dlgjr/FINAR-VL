from typing import Any, Callable, Iterable, overload

from binpacking.utilities import (
    load_csv,
    save_csvs,
    print_binsizes,
    get,
    argmin,
    revargsort,
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
    """Load a CSV file, bin-pack rows to N bins, write output CSVs."""
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


@overload
def to_constant_bin_number(
    d: Iterable[Any],
    N_bin: int,
    weight_pos: int | None = None,
    key: Callable[[Any], float] | None = None,
    lower_bound: float | None = None,
    upper_bound: float | None = None,
) -> list[list[Any]]: ...


def to_constant_bin_number(
    d: dict[str, float] | list[float] | Iterable[Any],
    N_bin: int,
    weight_pos: int | None = None,
    key: Callable[[Any], float] | None = None,
    lower_bound: float | None = None,
    upper_bound: float | None = None,
) -> list[dict[str, float]] | list[list[float]] | list[list[Any]]:
    """
    Distribute items to a fixed number of bins with balanced weights.

    Parameters
    ----------
    d : iterable
        list containing weights,
        OR dictionary where each (key,value)-pair carries the weight as value,
        OR list of tuples where one entry in the tuple is the weight. The position of
        this weight has to be given in optional variable weight_pos
    N_bin : int
        Number of bins to distribute items to.
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
        A list of length ``N_bin``. Each entry is a list of items or
        a dict of items, depending on the type of ``d``.
    """
    isdict = isinstance(d, dict)

    if not hasattr(d, '__len__'):
        raise TypeError("d must be iterable")

    # Handle empty input
    if len(d) == 0:  # type: ignore[arg-type]
        if isdict:
            return [{} for _ in range(N_bin)]
        else:
            return [[] for _ in range(N_bin)]

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

        bins: list[Any] = [{} for i in range(N_bin)]
    else:
        weights = sorted(d, key=lambda x: -x)  # type: ignore[arg-type]
        bins = [[] for i in range(N_bin)]

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

    # prepare array containing the current weight of the bins
    weight_sum = [0. for _ in range(N_bin)]

    # iterate through the weight list, starting with heaviest
    # Pure LPT: always place in the bin with lowest weight sum
    for item, weight in enumerate(weights):

        if isdict:
            key = keys[item]  # type: ignore[assignment]

        # put next value in bin with lowest weight sum
        b = argmin(weight_sum)

        # place the item
        if isdict:
            bins[b][key] = weight
        else:
            bins[b].append(weight)

        # update weight sum of the bin
        weight_sum[b] += weight

    if not is_tuple_list:
        return bins
    else:
        new_bins = []
        for b in range(N_bin):
            new_bins.append([])
            for key in bins[b]:  # type: ignore[assignment]
                new_bins[b].append(new_dict[key])
        return new_bins


if __name__ == "__main__":
    import pylab as pl
    import numpy as np

    a = np.random.power(0.01, size=1000)
    N_bin = 9

    bins = to_constant_bin_number(a, N_bin)
    weight_sums = [np.sum(b) for b in bins]

    # show max values of a and weight sums of the bins
    print(np.sort(a)[-1:-11:-1], weight_sums)

    # plot distribution
    pl.plot(np.arange(N_bin), [np.sum(b) for b in bins])
    pl.ylim([0, max([np.sum(b) for b in bins]) + 0.1])

    b = {'a': 10, 'b': 10, 'c': 11, 'd': 1, 'e': 2, 'f': 7}
    bins = to_constant_bin_number(b, 4)
    print("===== dict\n", b, "\n", bins)

    lower_bound = None
    upper_bound = None

    b = [('a', 10), ('b', 10), ('c', 11), ('d', 1), ('e', 2), ('f', 7, 'foo')]
    bins = to_constant_bin_number(b, 4, weight_pos=1, lower_bound=lower_bound, upper_bound=upper_bound)
    print("===== list of tuples\n", b, "\n", bins)

    pl.show()
