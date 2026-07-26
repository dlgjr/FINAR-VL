"""Tests for to_constant_volume function."""

import pytest
from binpacking.to_constant_volume import to_constant_volume


class TestBasicFunctionality:
    """Basic functionality tests for to_constant_volume."""

    def test_exact_fit(self):
        """Items that exactly fill bins."""
        values = [1, 2, 1]
        bins = to_constant_volume(values, 2)
        assert len(bins) == 2

    def test_no_fit(self):
        """Items larger than bin capacity each get their own bin."""
        values = [42, 24]
        bins = to_constant_volume(values, 20)
        assert bins == [[42], [24]]

    def test_single_item_fits(self):
        """Single item that fits in one bin."""
        values = [5]
        bins = to_constant_volume(values, 10)
        assert bins == [[5]]

    def test_single_item_exact(self):
        """Single item exactly equals bin capacity."""
        values = [10]
        bins = to_constant_volume(values, 10)
        assert bins == [[10]]

    def test_all_items_same_weight(self):
        """All items have the same weight."""
        values = [5, 5, 5, 5]
        bins = to_constant_volume(values, 10)
        # Each bin can hold 2 items of weight 5
        assert len(bins) == 2
        for b in bins:
            assert sum(b) <= 10

    def test_greedy_least_loaded_fit(self):
        """Verify Least Loaded Fit produces balanced bins."""
        values = [1, 5, 3, 2, 4]
        bins = to_constant_volume(values, 6)
        # After sorting: [5, 4, 3, 2, 1]
        # Least Loaded Fit places each item in the emptiest bin that fits
        # 5 -> bin 0 (sum=5)
        # 4 -> bin 1 (sum=4) - bin 1 is emptiest
        # 3 -> bin 2 (sum=3) - bin 2 is emptiest
        # 2 -> bin 2 (sum=5) - bin 2 is emptiest that fits
        # 1 -> bin 1 (sum=5) - bin 1 is emptiest that fits
        # Result: perfectly balanced bins with sums [5, 5, 5]
        assert all(sum(b) <= 6 for b in bins)
        assert bins == [[5], [4, 1], [3, 2]]



class TestDictInput:
    """Tests for dictionary input."""

    def test_dict_basic(self, sample_weights_dict):
        """Dictionary input returns list of dicts."""
        bins = to_constant_volume(sample_weights_dict, 11)
        assert all(isinstance(b, dict) for b in bins)
        # Total weight should be preserved
        total_original = sum(sample_weights_dict.values())
        total_bins = sum(sum(b.values()) for b in bins)
        assert total_original == total_bins

    def test_dict_keys_preserved(self, sample_weights_dict):
        """Dictionary keys are preserved in output."""
        bins = to_constant_volume(sample_weights_dict, 100)
        all_keys = set()
        for b in bins:
            all_keys.update(b.keys())
        assert all_keys == set(sample_weights_dict.keys())

    def test_dict_single_item(self):
        """Single item dictionary."""
        d = {'only': 5}
        bins = to_constant_volume(d, 10)
        assert bins == [{'only': 5}]


class TestTupleListInput:
    """Tests for list of tuples input."""

    def test_weight_pos(self):
        """Tuple list with weight_pos parameter."""
        values = [
            [1, 'x'],
            [2, 'y'],
            [1, 'z'],
        ]
        bins = to_constant_volume(values, 2, weight_pos=0)
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
        bins = to_constant_volume(values, 6, key=lambda x: x['y'])

        for bin_ in bins:
            for item in bin_:
                assert 'x' in item
                assert 'y' in item

    def test_tuple_list_preserves_structure(self, sample_tuple_list):
        """Tuple list items preserve their full structure."""
        bins = to_constant_volume(sample_tuple_list, 20, weight_pos=1)
        for bin_ in bins:
            for item in bin_:
                assert isinstance(item, tuple)
                assert len(item) >= 2  # At least (name, weight)


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
        V_max = 11

        # upper_bound=11 includes items with weight <= 11 (inclusive)
        # Least Loaded Fit spreads items evenly across bins
        bins = to_constant_volume(c, V_max, weight_pos=1, upper_bound=11)
        bins = [sorted(_bin, key=lambda x: x[0]) for _bin in bins]
        assert bins == [
            [('c', 11)],
            [('a', 10, 'foo')],
            [('b', 10, 'log')],
            [('d', 1, 'bar'), ('e', 2, 'bommel'), ('f', 7, 'floggo')],
        ]

        # lower_bound=1 includes items with weight >= 1 (inclusive)
        bins = to_constant_volume(c, V_max, weight_pos=1, lower_bound=1)
        bins = [sorted(_bin, key=lambda x: x[0]) for _bin in bins]
        assert bins == [
            [('c', 11)],
            [('a', 10, 'foo')],
            [('b', 10, 'log')],
            [('d', 1, 'bar'), ('e', 2, 'bommel'), ('f', 7, 'floggo')],
        ]

        # Both bounds (inclusive on both ends)
        bins = to_constant_volume(c, V_max, weight_pos=1, lower_bound=1, upper_bound=11)
        bins = [sorted(_bin, key=lambda x: x[0]) for _bin in bins]
        assert bins == [
            [('c', 11)],
            [('a', 10, 'foo')],
            [('b', 10, 'log')],
            [('d', 1, 'bar'), ('e', 2, 'bommel'), ('f', 7, 'floggo')],
        ]

    def test_lower_bound_only(self):
        """Only lower_bound specified."""
        values = [1, 2, 3, 4, 5]
        bins = to_constant_volume(values, 10, lower_bound=2)
        flat = [w for b in bins for w in b]
        # lower_bound=2 means weights >= 2 are included (inclusive)
        assert 1 not in flat
        assert 2 in flat
        assert 3 in flat

    def test_upper_bound_only(self):
        """Only upper_bound specified."""
        values = [1, 2, 3, 4, 5]
        bins = to_constant_volume(values, 10, upper_bound=4)
        flat = [w for b in bins for w in b]
        # upper_bound=4 means weights <= 4 are included (inclusive)
        assert 5 not in flat
        assert 4 in flat
        assert 3 in flat

    def test_bounds_filter_all(self):
        """Bounds that filter out all items."""
        values = [1, 2, 3]
        bins = to_constant_volume(values, 10, lower_bound=5)
        # All items have weight < 5, so all are filtered
        flat = [w for b in bins for w in b]
        assert flat == []

    def test_bounds_equal_raises(self):
        """When lower_bound == upper_bound, Exception is raised."""
        values = [1, 2, 3, 6, 7]
        with pytest.raises(Exception, match="greater or equal"):
            to_constant_volume(values, 10, lower_bound=5, upper_bound=5)

    def test_bounds_lower_greater_than_upper_raises(self):
        """When lower_bound > upper_bound, Exception is raised."""
        values = [1, 2, 3, 6, 7]
        with pytest.raises(Exception, match="greater or equal"):
            to_constant_volume(values, 10, lower_bound=6, upper_bound=5)

    def test_both_bounds_inclusive(self):
        """Both bounds should be inclusive together."""
        values = [1, 5, 10, 15, 20]
        bins = to_constant_volume(values, 100, lower_bound=5, upper_bound=15)
        flat = [w for b in bins for w in b]
        assert 5 in flat, "weight=5 should be included (== lower_bound)"
        assert 10 in flat
        assert 15 in flat, "weight=15 should be included (== upper_bound)"
        assert 1 not in flat
        assert 20 not in flat

    def test_bounds_with_dict(self):
        """Bounds should be inclusive for dict input."""
        d = {'a': 1, 'b': 5, 'c': 10, 'd': 15}
        bins = to_constant_volume(d, 100, lower_bound=5, upper_bound=10)
        all_weights = []
        for b in bins:
            all_weights.extend(b.values())
        assert 5 in all_weights, "weight=5 should be included"
        assert 10 in all_weights, "weight=10 should be included"
        assert 1 not in all_weights
        assert 15 not in all_weights


class TestEdgeCases:
    """Edge case tests for to_constant_volume."""

    def test_empty_list(self):
        """Empty list input returns one empty bin."""
        bins = to_constant_volume([], 10)
        assert bins == [[]]

    def test_empty_dict(self):
        """Empty dictionary input."""
        bins = to_constant_volume({}, 10)
        assert bins == [{}]  # Returns one empty bin

    def test_zero_weights(self):
        """Items with zero weight."""
        values = [0, 0, 0]
        bins = to_constant_volume(values, 10)
        # All zeros should fit in one bin
        assert len(bins) == 1
        assert bins[0] == [0, 0, 0]

    def test_mixed_zero_and_nonzero(self):
        """Mix of zero and non-zero weights."""
        values = [0, 5, 0, 3]
        bins = to_constant_volume(values, 6)
        total = sum(w for b in bins for w in b)
        assert total == 8

    def test_large_v_max(self):
        """V_max larger than sum of all weights."""
        values = [1, 2, 3, 4, 5]
        bins = to_constant_volume(values, 100)
        # All items should fit in one bin
        assert len(bins) == 1
        assert sum(bins[0]) == 15

    def test_v_max_equals_largest(self):
        """V_max equals the largest item."""
        values = [1, 2, 5, 3]
        bins = to_constant_volume(values, 5)
        # Each bin can hold at most 5
        assert all(sum(b) <= 5 for b in bins)

    def test_floats(self):
        """Float weights."""
        values = [1.5, 2.5, 3.0]
        bins = to_constant_volume(values, 4.0)
        total = sum(w for b in bins for w in b)
        assert abs(total - 7.0) < 1e-9

    def test_negative_weights(self):
        """Negative weights (unusual but should work)."""
        values = [-1, -2, 3]
        bins = to_constant_volume(values, 5)
        total = sum(w for b in bins for w in b)
        assert total == 0


class TestWeightPreservation:
    """Tests to verify all weights are preserved in output."""

    def test_list_weight_sum(self):
        """Total weight is preserved for list input."""
        values = [10, 20, 30, 15, 25]
        bins = to_constant_volume(values, 35)
        original_sum = sum(values)
        bins_sum = sum(w for b in bins for w in b)
        assert original_sum == bins_sum

    def test_dict_weight_sum(self):
        """Total weight is preserved for dict input."""
        d = {'a': 10, 'b': 20, 'c': 15}
        bins = to_constant_volume(d, 25)
        original_sum = sum(d.values())
        bins_sum = sum(sum(b.values()) for b in bins)
        assert original_sum == bins_sum

    def test_no_items_lost(self):
        """All items appear exactly once in output."""
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        bins = to_constant_volume(values, 15)
        flat = sorted(w for b in bins for w in b)
        assert flat == sorted(values)


class TestVolumeConstraint:
    """Tests to verify volume constraints are respected."""

    def test_bins_respect_volume(self):
        """Each bin respects the volume constraint."""
        values = [5, 8, 3, 7, 2, 9, 4, 1]
        V_max = 12
        bins = to_constant_volume(values, V_max)
        for b in bins:
            assert sum(b) <= V_max

    def test_bins_respect_volume_dict(self):
        """Each bin respects volume for dict input."""
        d = {'a': 5, 'b': 8, 'c': 3, 'd': 7}
        V_max = 10
        bins = to_constant_volume(d, V_max)
        for b in bins:
            assert sum(b.values()) <= V_max
