"""Tests for to_constant_bin_number function."""

import pytest
from binpacking.to_constant_bin_number import to_constant_bin_number


class TestBasicFunctionality:
    """Basic functionality tests for to_constant_bin_number."""

    def test_only_zero_weights(self):
        """All zero weights go to the first bin."""
        values = [0, 0, 0]
        bins = to_constant_bin_number(values, 4)
        assert bins == [[0, 0, 0], [], [], []]

    def test_single_item_single_bin(self):
        """Single item into single bin."""
        values = [5]
        bins = to_constant_bin_number(values, 1)
        assert bins == [[5]]

    def test_single_item_multiple_bins(self):
        """Single item distributed to N bins."""
        values = [5]
        bins = to_constant_bin_number(values, 3)
        # Only one item, so it goes to bin 0
        assert len(bins) == 3
        total_weight = sum(sum(b) for b in bins)
        assert total_weight == 5

    def test_even_distribution(self):
        """Items should be distributed to balance weights."""
        values = [10, 10, 10, 10]
        bins = to_constant_bin_number(values, 4)
        # Perfect distribution: one item per bin
        weights = [sum(b) for b in bins]
        assert weights == [10, 10, 10, 10]

    def test_uneven_distribution(self):
        """Items distributed to minimize variance."""
        values = [10, 10, 11, 1, 2, 7]
        values_reversed = values[::-1]
        for vals in [values, values_reversed]:
            bins = to_constant_bin_number(vals, 4)
            # Should get reasonably balanced bins
            assert len(bins) == 4
            total = sum(sum(b) for b in bins)
            assert total == 41  # Sum of all weights

    def test_more_bins_than_items(self):
        """More bins than items."""
        values = [5, 10]
        bins = to_constant_bin_number(values, 5)
        assert len(bins) == 5
        # Some bins should be empty
        non_empty = [b for b in bins if b]
        assert len(non_empty) <= 2


class TestDictInput:
    """Tests for dictionary input."""

    def test_dict_basic(self, sample_weights_dict):
        """Dictionary input returns list of dicts."""
        bins = to_constant_bin_number(sample_weights_dict, 3)
        assert all(isinstance(b, dict) for b in bins)
        assert len(bins) == 3

    def test_dict_keys_preserved(self, sample_weights_dict):
        """Dictionary keys are preserved."""
        bins = to_constant_bin_number(sample_weights_dict, 2)
        all_keys = set()
        for b in bins:
            all_keys.update(b.keys())
        assert all_keys == set(sample_weights_dict.keys())

    def test_dict_single_bin(self):
        """All items in single bin."""
        d = {'a': 10, 'b': 20, 'c': 5}
        bins = to_constant_bin_number(d, 1)
        assert len(bins) == 1
        assert sum(bins[0].values()) == 35


class TestTupleListInput:
    """Tests for list of tuples input."""

    def test_weight_pos(self):
        """Tuple list with weight_pos parameter."""
        values = [
            [1, 'x'],
            [2, 'y'],
            [1, 'z'],
        ] # this also tests whether list of lists works
        bins = to_constant_bin_number(values, 2, weight_pos=0)
        for bin_ in bins:
            for item in bin_:
                assert isinstance(item[0], int)
                assert isinstance(item[1], str)

    def test_key_func(self):
        """Tuple list with key function."""
        values = [
            {'x': 'a', 'y': 1},
            {'x': 'b', 'y': 5},
            {'x': 'b', 'y': 3},
        ]
        bins = to_constant_bin_number(values, 2, key=lambda x: x['y'])

        for bin_ in bins:
            for item in bin_:
                assert 'x' in item
                assert 'y' in item

    def test_tuple_preserves_structure(self, sample_tuple_list):
        """Tuple list items preserve their full structure."""
        bins = to_constant_bin_number(sample_tuple_list, 3, weight_pos=1)
        for bin_ in bins:
            for item in bin_:
                assert isinstance(item, tuple)
                assert len(item) >= 2


class TestBounds:
    """Tests for lower_bound and upper_bound parameters."""

    def test_bounds_and_tuples(self):
        """Comprehensive bounds test with tuples."""
        c = [
            ('a', 10, 'foo'),
            ('b', 10, 'log'),
            ('c', 11),
            ('d', 1, 'bar'),
            ('e', 2, 'bommel'),
            ('f', 7, 'floggo'),
        ]
        N_bin = 4

        # upper_bound=11 includes weight <= 11 (inclusive)
        bins = to_constant_bin_number(c, N_bin, weight_pos=1, upper_bound=11)
        bins = [sorted(_bin, key=lambda x: x[0]) for _bin in bins]
        assert bins == [
            [('c', 11)],
            [('a', 10, 'foo')],
            [('b', 10, 'log')],
            [
                ('d', 1, 'bar'),
                ('e', 2, 'bommel'),
                ('f', 7, 'floggo'),
            ],
        ]

        # lower_bound=1 includes weight >= 1 (inclusive)
        bins = to_constant_bin_number(c, N_bin, weight_pos=1, lower_bound=1)
        bins = [sorted(_bin, key=lambda x: x[0]) for _bin in bins]
        assert bins == [
            [('c', 11)],
            [('a', 10, 'foo')],
            [('b', 10, 'log')],
            [
                ('d', 1, 'bar'),
                ('e', 2, 'bommel'),
                ('f', 7, 'floggo'),
            ],
        ]

        # Both bounds (inclusive)
        bins = to_constant_bin_number(c, N_bin, weight_pos=1, lower_bound=1, upper_bound=11)
        bins = [sorted(_bin, key=lambda x: x[0]) for _bin in bins]
        assert bins == [
            [('c', 11)],
            [('a', 10, 'foo')],
            [('b', 10, 'log')],
            [
                ('d', 1, 'bar'),
                ('e', 2, 'bommel'),
                ('f', 7, 'floggo'),
            ],
        ]

    def test_lower_bound_only(self):
        """Only lower_bound specified."""
        values = [1, 2, 3, 4, 5]
        bins = to_constant_bin_number(values, 3, lower_bound=2)
        flat = [w for b in bins for w in b]
        # lower_bound=2 includes weights >= 2 (inclusive)
        assert 1 not in flat
        assert 2 in flat
        assert 3 in flat

    def test_upper_bound_only(self):
        """Only upper_bound specified."""
        values = [1, 2, 3, 4, 5]
        bins = to_constant_bin_number(values, 3, upper_bound=4)
        flat = [w for b in bins for w in b]
        # upper_bound=4 includes weights <= 4 (inclusive)
        assert 5 not in flat
        assert 4 in flat
        assert 3 in flat

    def test_bounds_filter_all(self):
        """Bounds that filter out all items."""
        values = [1, 2, 3]
        bins = to_constant_bin_number(values, 3, lower_bound=5)
        # All items filtered, all bins empty
        assert all(len(b) == 0 for b in bins)

    def test_bounds_equal_raises(self):
        """When lower_bound == upper_bound, Exception is raised."""
        values = [1, 2, 3, 6, 7]
        with pytest.raises(Exception, match="greater or equal"):
            to_constant_bin_number(values, 3, lower_bound=5, upper_bound=5)

    def test_bounds_lower_greater_than_upper_raises(self):
        """When lower_bound > upper_bound, Exception is raised."""
        values = [1, 2, 3, 6, 7]
        with pytest.raises(Exception, match="greater or equal"):
            to_constant_bin_number(values, 3, lower_bound=6, upper_bound=5)

    def test_both_bounds_inclusive(self):
        """Both bounds should be inclusive together."""
        values = [1, 5, 10, 15, 20]
        bins = to_constant_bin_number(values, 3, lower_bound=5, upper_bound=15)
        flat = [w for b in bins for w in b]
        assert 5 in flat
        assert 10 in flat
        assert 15 in flat
        assert 1 not in flat
        assert 20 not in flat

    def test_bounds_with_dict(self):
        """Bounds should be inclusive for dict input."""
        d = {'a': 1, 'b': 5, 'c': 10, 'd': 15}
        bins = to_constant_bin_number(d, 2, lower_bound=5, upper_bound=10)
        all_weights = []
        for b in bins:
            all_weights.extend(b.values())
        assert 5 in all_weights
        assert 10 in all_weights
        assert 1 not in all_weights
        assert 15 not in all_weights


class TestEdgeCases:
    """Edge case tests for to_constant_bin_number."""

    def test_empty_list(self):
        """Empty list input returns N empty bins."""
        bins = to_constant_bin_number([], 3)
        assert len(bins) == 3
        assert all(b == [] for b in bins)

    def test_empty_dict(self):
        """Empty dictionary input."""
        bins = to_constant_bin_number({}, 3)
        assert len(bins) == 3
        assert all(b == {} for b in bins)

    def test_n_bin_one(self):
        """Single bin gets all items."""
        values = [1, 2, 3, 4, 5]
        bins = to_constant_bin_number(values, 1)
        assert len(bins) == 1
        assert sum(bins[0]) == 15

    def test_floats(self):
        """Float weights."""
        values = [1.5, 2.5, 3.0, 4.0]
        bins = to_constant_bin_number(values, 2)
        total = sum(w for b in bins for w in b)
        assert abs(total - 11.0) < 1e-10

    def test_negative_weights(self):
        """Negative weights (unusual but should work)."""
        values = [-1, -2, 3, 4]
        bins = to_constant_bin_number(values, 2)
        total = sum(w for b in bins for w in b)
        assert total == 4


class TestWeightPreservation:
    """Tests to verify all weights are preserved in output."""

    def test_list_weight_sum(self):
        """Total weight is preserved for list input."""
        values = [10, 20, 30, 15, 25]
        bins = to_constant_bin_number(values, 3)
        original_sum = sum(values)
        bins_sum = sum(w for b in bins for w in b)
        assert original_sum == bins_sum

    def test_dict_weight_sum(self):
        """Total weight is preserved for dict input."""
        d = {'a': 10, 'b': 20, 'c': 15}
        bins = to_constant_bin_number(d, 2)
        original_sum = sum(d.values())
        bins_sum = sum(sum(b.values()) for b in bins)
        assert original_sum == bins_sum

    def test_no_items_lost(self):
        """All items appear exactly once in output."""
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        bins = to_constant_bin_number(values, 4)
        flat = sorted(w for b in bins for w in b)
        assert flat == sorted(values)


class TestBinCount:
    """Tests to verify correct number of bins."""

    def test_exact_bin_count(self):
        """Output always has exactly N_bin bins."""
        for n_bin in [1, 2, 3, 5, 10]:
            values = [1, 2, 3, 4, 5]
            bins = to_constant_bin_number(values, n_bin)
            assert len(bins) == n_bin

    def test_bin_count_with_dict(self):
        """Dict input produces correct bin count."""
        d = {'a': 1, 'b': 2, 'c': 3}
        for n_bin in [1, 2, 4]:
            bins = to_constant_bin_number(d, n_bin)
            assert len(bins) == n_bin


class TestBalancing:
    """Tests for weight balancing across bins."""

    def test_balanced_weights_simple(self):
        """Simple case where perfect balance is possible."""
        values = [10, 10, 10, 10]
        bins = to_constant_bin_number(values, 2)
        weights = [sum(b) for b in bins]
        # Each bin should have 20
        assert weights == [20, 20]

    def test_reasonable_balance(self):
        """Weights should be reasonably balanced."""
        values = [100, 50, 40, 30, 20, 10]  # Total: 250
        values_reversed = values[::-1]
        for vals in [values, values_reversed]:
            bins = to_constant_bin_number(vals, 5)
            weights = [sum(b) for b in bins]
            # Average would be 50 per bin
            # Should have reasonable variance
            assert max(weights) - min(weights) <= 100
