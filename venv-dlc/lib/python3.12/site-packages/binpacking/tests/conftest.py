"""Shared fixtures and utilities for binpacking tests."""

import os
import tempfile
import pytest


@pytest.fixture
def sample_weights_list():
    """Sample list of weights for testing."""
    return [10, 10, 11, 1, 2, 7]


@pytest.fixture
def sample_weights_dict():
    """Sample dictionary of weights for testing."""
    return {'a': 10, 'b': 10, 'c': 11, 'd': 1, 'e': 2, 'f': 7}


@pytest.fixture
def sample_tuple_list():
    """Sample list of tuples with weights for testing."""
    return [
        ('a', 10, 'foo'),
        ('b', 10, 'log'),
        ('c', 11),
        ('d', 1, 'bar'),
        ('e', 2, 'bommel'),
        ('f', 7, 'floggo'),
    ]


@pytest.fixture
def temp_csv_file():
    """Create a temporary CSV file for testing."""
    fd, path = tempfile.mkstemp(suffix='.csv')
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def sample_csv_with_header(temp_csv_file):
    """Create a sample CSV file with header."""
    content = """name,count,category
apple,10,fruit
banana,5,fruit
carrot,8,vegetable
date,3,fruit
eggplant,12,vegetable
"""
    with open(temp_csv_file, 'w') as f:
        f.write(content)
    return temp_csv_file


@pytest.fixture
def sample_csv_without_header(temp_csv_file):
    """Create a sample CSV file without header."""
    content = """apple,10,fruit
banana,5,fruit
carrot,8,vegetable
date,3,fruit
eggplant,12,vegetable
"""
    with open(temp_csv_file, 'w') as f:
        f.write(content)
    return temp_csv_file
