"""Tests for utility functions in utilities.py."""

import pytest
from binpacking.utilities import get, argmin, argmax, argsort, revargsort


class TestGet:
    """Tests for the get function (index list by another list)."""

    def test_basic(self):
        """Basic indexing."""
        lst = ['a', 'b', 'c', 'd', 'e']
        ndx = [0, 2, 4]
        result = get(lst, ndx)
        assert result == ['a', 'c', 'e']

    def test_reverse_order(self):
        """Indexing in reverse order."""
        lst = [10, 20, 30, 40, 50]
        ndx = [4, 3, 2, 1, 0]
        result = get(lst, ndx)
        assert result == [50, 40, 30, 20, 10]

    def test_single_index(self):
        """Single index."""
        lst = ['x', 'y', 'z']
        ndx = [1]
        result = get(lst, ndx)
        assert result == ['y']

    def test_repeated_indices(self):
        """Repeated indices."""
        lst = [1, 2, 3]
        ndx = [0, 0, 1, 1, 2, 2]
        result = get(lst, ndx)
        assert result == [1, 1, 2, 2, 3, 3]

    def test_empty_indices(self):
        """Empty index list."""
        lst = [1, 2, 3]
        ndx = []
        result = get(lst, ndx)
        assert result == []

    def test_all_indices(self):
        """All indices in order."""
        lst = ['a', 'b', 'c']
        ndx = [0, 1, 2]
        result = get(lst, ndx)
        assert result == ['a', 'b', 'c']


class TestArgmin:
    """Tests for argmin function."""

    def test_basic(self):
        """Find index of minimum."""
        lst = [5, 2, 8, 1, 9]
        assert argmin(lst) == 3  # Index of 1

    def test_first_occurrence(self):
        """Returns first occurrence when multiple minimums."""
        lst = [5, 1, 8, 1, 9]
        assert argmin(lst) == 1  # First index of 1

    def test_single_element(self):
        """Single element list."""
        lst = [42]
        assert argmin(lst) == 0

    def test_all_same(self):
        """All elements are the same."""
        lst = [5, 5, 5, 5]
        assert argmin(lst) == 0

    def test_negative_numbers(self):
        """List with negative numbers."""
        lst = [3, -1, 4, -5, 2]
        assert argmin(lst) == 3  # Index of -5

    def test_floats(self):
        """Float values."""
        lst = [1.5, 0.5, 2.5]
        assert argmin(lst) == 1


class TestArgmax:
    """Tests for argmax function."""

    def test_basic(self):
        """Find index of maximum."""
        lst = [5, 2, 8, 1, 9]
        assert argmax(lst) == 4  # Index of 9

    def test_first_occurrence(self):
        """Returns first occurrence when multiple maximums."""
        lst = [5, 9, 8, 9, 1]
        assert argmax(lst) == 1  # First index of 9

    def test_single_element(self):
        """Single element list."""
        lst = [42]
        assert argmax(lst) == 0

    def test_all_same(self):
        """All elements are the same."""
        lst = [5, 5, 5, 5]
        assert argmax(lst) == 0

    def test_negative_numbers(self):
        """List with negative numbers."""
        lst = [-3, -1, -4, -5, -2]
        assert argmax(lst) == 1  # Index of -1

    def test_floats(self):
        """Float values."""
        lst = [1.5, 2.5, 0.5]
        assert argmax(lst) == 1


class TestArgsort:
    """Tests for argsort function."""

    def test_basic(self):
        """Basic ascending sort indices."""
        lst = [30, 10, 20]
        result = argsort(lst)
        assert result == [1, 2, 0]  # 10, 20, 30

    def test_already_sorted(self):
        """Already sorted list."""
        lst = [1, 2, 3, 4, 5]
        result = argsort(lst)
        assert result == [0, 1, 2, 3, 4]

    def test_reverse_sorted(self):
        """Reverse sorted list."""
        lst = [5, 4, 3, 2, 1]
        result = argsort(lst)
        assert result == [4, 3, 2, 1, 0]

    def test_single_element(self):
        """Single element list."""
        lst = [42]
        result = argsort(lst)
        assert result == [0]

    def test_with_duplicates(self):
        """List with duplicate values."""
        lst = [3, 1, 2, 1]
        result = argsort(lst)
        # Values sorted: 1, 1, 2, 3 (indices: 1, 3, 2, 0)
        sorted_values = get(lst, result)
        assert sorted_values == [1, 1, 2, 3]

    def test_negative_numbers(self):
        """List with negative numbers."""
        lst = [1, -2, 3, -4]
        result = argsort(lst)
        sorted_values = get(lst, result)
        assert sorted_values == [-4, -2, 1, 3]

    def test_floats(self):
        """Float values."""
        lst = [1.5, 0.5, 2.5]
        result = argsort(lst)
        assert result == [1, 0, 2]


class TestRevargsort:
    """Tests for revargsort function (reverse argsort)."""

    def test_basic(self):
        """Basic descending sort indices."""
        lst = [30, 10, 20]
        result = revargsort(lst)
        assert result == [0, 2, 1]  # 30, 20, 10

    def test_already_reverse_sorted(self):
        """Already reverse sorted list."""
        lst = [5, 4, 3, 2, 1]
        result = revargsort(lst)
        assert result == [0, 1, 2, 3, 4]

    def test_ascending_sorted(self):
        """Ascending sorted list."""
        lst = [1, 2, 3, 4, 5]
        result = revargsort(lst)
        assert result == [4, 3, 2, 1, 0]

    def test_single_element(self):
        """Single element list."""
        lst = [42]
        result = revargsort(lst)
        assert result == [0]

    def test_with_duplicates(self):
        """List with duplicate values."""
        lst = [3, 1, 2, 1]
        result = revargsort(lst)
        # Values sorted descending: 3, 2, 1, 1
        sorted_values = get(lst, result)
        assert sorted_values == [3, 2, 1, 1]

    def test_negative_numbers(self):
        """List with negative numbers."""
        lst = [1, -2, 3, -4]
        result = revargsort(lst)
        sorted_values = get(lst, result)
        assert sorted_values == [3, 1, -2, -4]

    def test_floats(self):
        """Float values."""
        lst = [1.5, 0.5, 2.5]
        result = revargsort(lst)
        assert result == [2, 0, 1]

    def test_inverse_of_argsort(self):
        """revargsort should give the reverse of argsort."""
        lst = [30, 10, 50, 20, 40]
        forward = argsort(lst)
        reverse = revargsort(lst)
        # The reverse of forward indices should equal reverse indices
        assert forward[::-1] == reverse
