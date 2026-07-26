"""Tests for NumPy-accelerated bin packing algorithms.

These tests verify that the numpy module produces the same results
as the pure Python implementation.
"""

import pytest

# Skip all tests if numpy is not installed
np = pytest.importorskip("numpy")

from binpacking.numpy import to_constant_volume, to_constant_bin_number
from binpacking import to_constant_volume as py_to_constant_volume
from binpacking import to_constant_bin_number as py_to_constant_bin_number


class TestNumpyConstantVolume:
    """Tests for numpy to_constant_volume."""

    def test_basic_list(self):
        """Basic list input."""
        values = [1, 2, 3, 4, 5]
        bins = to_constant_volume(values, 5)
        assert all(sum(b) <= 5 for b in bins)
        assert sum(sum(b) for b in bins) == 15

    def test_matches_pure_python(self):
        """NumPy version produces same results as pure Python."""
        values = [10, 10, 11, 1, 2, 7]
        V_max = 11

        np_bins = to_constant_volume(values, V_max)
        py_bins = py_to_constant_volume(values, V_max)

        # Same number of bins
        assert len(np_bins) == len(py_bins)
        # Same total weight
        np_total = sum(sum(b) for b in np_bins)
        py_total = sum(sum(b) for b in py_bins)
        assert np_total == py_total

    def test_dict_input(self):
        """Dictionary input."""
        d = {'a': 10, 'b': 5, 'c': 3}
        bins = to_constant_volume(d, 10)
        assert all(isinstance(b, dict) for b in bins)
        total = sum(sum(b.values()) for b in bins)
        assert total == 18

    def test_tuple_list_input(self):
        """Tuple list with weight_pos."""
        tuples = [('a', 10), ('b', 5), ('c', 3)]
        bins = to_constant_volume(tuples, 10, weight_pos=1)
        assert all(isinstance(b, list) for b in bins)

    def test_empty_list(self):
        """Empty list returns empty bin."""
        bins = to_constant_volume([], 10)
        assert bins == [[]]

    def test_empty_dict(self):
        """Empty dict returns empty dict bin."""
        bins = to_constant_volume({}, 10)
        assert bins == [{}]

    def test_bounds(self):
        """Bounds filtering works."""
        values = [1, 5, 10, 15]
        bins = to_constant_volume(values, 100, lower_bound=5, upper_bound=10)
        flat = [w for b in bins for w in b]
        assert 1 not in [int(x) for x in flat]
        assert 15 not in [int(x) for x in flat]
        assert 5 in [int(x) for x in flat]
        assert 10 in [int(x) for x in flat]

    def test_bounds_equal_raises(self):
        """Equal bounds raises exception."""
        with pytest.raises(Exception, match="greater or equal"):
            to_constant_volume([1, 2, 3], 10, lower_bound=5, upper_bound=5)


class TestNumpyConstantBinNumber:
    """Tests for numpy to_constant_bin_number."""

    def test_basic_list(self):
        """Basic list input."""
        values = [10, 10, 10, 10]
        bins = to_constant_bin_number(values, 4)
        assert len(bins) == 4
        assert sum(sum(b) for b in bins) == 40

    def test_matches_pure_python(self):
        """NumPy version produces same results as pure Python."""
        values = [10, 10, 11, 1, 2, 7]
        N_bin = 4

        np_bins = to_constant_bin_number(values, N_bin)
        py_bins = py_to_constant_bin_number(values, N_bin)

        # Same number of bins
        assert len(np_bins) == len(py_bins) == N_bin
        # Same total weight
        np_total = sum(sum(b) for b in np_bins)
        py_total = sum(sum(b) for b in py_bins)
        assert np_total == py_total

    def test_dict_input(self):
        """Dictionary input."""
        d = {'a': 10, 'b': 10, 'c': 11, 'd': 1}
        bins = to_constant_bin_number(d, 3)
        assert len(bins) == 3
        assert all(isinstance(b, dict) for b in bins)

    def test_tuple_list_input(self):
        """Tuple list with weight_pos."""
        tuples = [('a', 10), ('b', 5), ('c', 3)]
        bins = to_constant_bin_number(tuples, 2, weight_pos=1)
        assert len(bins) == 2

    def test_empty_list(self):
        """Empty list returns N empty bins."""
        bins = to_constant_bin_number([], 3)
        assert len(bins) == 3
        assert all(b == [] for b in bins)

    def test_empty_dict(self):
        """Empty dict returns N empty dict bins."""
        bins = to_constant_bin_number({}, 3)
        assert len(bins) == 3
        assert all(b == {} for b in bins)

    def test_bounds(self):
        """Bounds filtering works."""
        values = [1, 5, 10, 15]
        bins = to_constant_bin_number(values, 3, lower_bound=5, upper_bound=10)
        flat = [w for b in bins for w in b]
        assert 1 not in [int(x) for x in flat]
        assert 15 not in [int(x) for x in flat]

    def test_bounds_equal_raises(self):
        """Equal bounds raises exception."""
        with pytest.raises(Exception, match="greater or equal"):
            to_constant_bin_number([1, 2, 3], 2, lower_bound=5, upper_bound=5)


class TestNumpyLargeDatasets:
    """Test performance characteristics with larger datasets."""

    def test_large_list_constant_volume(self):
        """Handle large list for constant volume."""
        values = list(range(1, 1001))  # 1 to 1000
        bins = to_constant_volume(values, 5000)
        total = sum(sum(b) for b in bins)
        assert total == sum(values)

    def test_large_list_constant_bin_number(self):
        """Handle large list for constant bin number."""
        values = list(range(1, 1001))
        bins = to_constant_bin_number(values, 10)
        assert len(bins) == 10
        total = sum(sum(b) for b in bins)
        assert total == sum(values)
