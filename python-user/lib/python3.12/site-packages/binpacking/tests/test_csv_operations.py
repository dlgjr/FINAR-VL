"""Tests for CSV loading and saving operations."""

import os
import tempfile
import pytest
from binpacking.utilities import load_csv, save_csvs, print_binsizes


class TestLoadCsv:
    """Tests for load_csv function."""

    def test_with_header_column_by_name(self, sample_csv_with_header):
        """Load CSV with header, column specified by name."""
        data, weight_col, header = load_csv(
            sample_csv_with_header,
            weight_column='count',
            has_header=True,
        )
        assert header == ['name', 'count', 'category']
        assert weight_col == 1  # 'count' is at index 1
        assert len(data) == 5
        # Check that weights are converted to float
        assert all(isinstance(row[1], float) for row in data)

    def test_with_header_column_by_index(self, sample_csv_with_header):
        """Load CSV with header, column specified by index."""
        data, weight_col, header = load_csv(
            sample_csv_with_header,
            weight_column=1,
            has_header=True,
        )
        assert weight_col == 1
        assert header == ['name', 'count', 'category']
        assert len(data) == 5

    def test_without_header(self, sample_csv_without_header):
        """Load CSV without header."""
        data, weight_col, header = load_csv(
            sample_csv_without_header,
            weight_column=1,
            has_header=False,
        )
        assert header is None
        assert weight_col == 1
        assert len(data) == 5
        # First row is data, not header
        assert data[0][0] == 'apple'

    def test_weight_values_correct(self, sample_csv_with_header):
        """Verify weight values are parsed correctly."""
        data, weight_col, _ = load_csv(
            sample_csv_with_header,
            weight_column='count',
            has_header=True,
        )
        weights = [row[weight_col] for row in data]
        assert weights == [10.0, 5.0, 8.0, 3.0, 12.0]

    def test_string_column_without_header_raises(self, sample_csv_without_header):
        """String column name without header should raise."""
        with pytest.raises(Exception) as excinfo:
            load_csv(
                sample_csv_without_header,
                weight_column='count',
                has_header=False,
            )
        assert 'useless' in str(excinfo.value).lower()

    def test_column_not_in_header_raises(self, sample_csv_with_header):
        """Non-existent column name should raise."""
        with pytest.raises(Exception) as excinfo:
            load_csv(
                sample_csv_with_header,
                weight_column='nonexistent',
                has_header=True,
            )
        assert 'not found' in str(excinfo.value).lower()

    def test_custom_delimiter(self, temp_csv_file):
        """CSV with custom delimiter."""
        content = "name;count;category\napple;10;fruit\nbanana;5;fruit\n"
        with open(temp_csv_file, 'w') as f:
            f.write(content)

        data, weight_col, header = load_csv(
            temp_csv_file,
            weight_column='count',
            has_header=True,
            delim=';',
        )
        assert header == ['name', 'count', 'category']
        assert len(data) == 2

    def test_custom_quotechar(self, temp_csv_file):
        """CSV with quoted fields."""
        content = "name,count,category\n'apple, red',10,fruit\nbanana,5,fruit\n"
        with open(temp_csv_file, 'w') as f:
            f.write(content)

        data, weight_col, header = load_csv(
            temp_csv_file,
            weight_column=1,
            has_header=True,
            quotechar="'",
        )
        assert data[0][0] == 'apple, red'


class TestSaveCsvs:
    """Tests for save_csvs function."""

    def test_basic_save(self, temp_csv_file):
        """Basic save creates correct files."""
        bins = [
            [['apple', 10.0, 'fruit'], ['banana', 5.0, 'fruit']],
            [['carrot', 8.0, 'vegetable']],
        ]
        header = ['name', 'count', 'category']
        output_dir = os.path.dirname(temp_csv_file)

        save_csvs(bins, temp_csv_file, header, output_dir=output_dir)

        # Check files were created
        basename = os.path.basename(temp_csv_file)
        base, ext = os.path.splitext(basename)
        assert os.path.exists(os.path.join(output_dir, f"{base}_0{ext}"))
        assert os.path.exists(os.path.join(output_dir, f"{base}_1{ext}"))

        # Cleanup
        os.unlink(os.path.join(output_dir, f"{base}_0{ext}"))
        os.unlink(os.path.join(output_dir, f"{base}_1{ext}"))

    def test_save_content(self, temp_csv_file):
        """Verify saved content is correct."""
        bins = [
            [['apple', 10.0, 'fruit']],
        ]
        header = ['name', 'count', 'category']
        output_dir = os.path.dirname(temp_csv_file)

        save_csvs(bins, temp_csv_file, header, output_dir=output_dir)

        basename = os.path.basename(temp_csv_file)
        base, ext = os.path.splitext(basename)
        output_file = os.path.join(output_dir, f"{base}_0{ext}")

        with open(output_file, 'r') as f:
            lines = f.readlines()

        assert 'name,count,category' in lines[0]
        assert 'apple' in lines[1]

        os.unlink(output_file)

    def test_save_without_header(self, temp_csv_file):
        """Save bins without header."""
        bins = [
            [['apple', 10.0, 'fruit']],
        ]
        output_dir = os.path.dirname(temp_csv_file)

        save_csvs(bins, temp_csv_file, header=None, output_dir=output_dir)

        basename = os.path.basename(temp_csv_file)
        base, ext = os.path.splitext(basename)
        output_file = os.path.join(output_dir, f"{base}_0{ext}")

        with open(output_file, 'r') as f:
            lines = f.readlines()

        # First line should be data, not header
        assert 'apple' in lines[0]
        assert len(lines) == 1

        os.unlink(output_file)

    def test_file_numbering(self, temp_csv_file):
        """Test correct file numbering for multiple bins."""
        bins = [[[f'item{i}', float(i), 'cat']] for i in range(12)]
        header = ['name', 'count', 'category']
        output_dir = os.path.dirname(temp_csv_file)

        save_csvs(bins, temp_csv_file, header, output_dir=output_dir)

        basename = os.path.basename(temp_csv_file)
        base, ext = os.path.splitext(basename)
        # Should use 2-digit formatting for 12 bins
        assert os.path.exists(os.path.join(output_dir, f"{base}_00{ext}"))
        assert os.path.exists(os.path.join(output_dir, f"{base}_11{ext}"))

        # Cleanup
        for i in range(12):
            os.unlink(os.path.join(output_dir, f"{base}_{i:02d}{ext}"))


class TestPrintBinsizes:
    """Tests for print_binsizes function."""

    def test_basic_output(self, capsys):
        """Test basic output."""
        bins = [
            [['a', 10.0], ['b', 5.0]],
            [['c', 8.0]],
        ]
        print_binsizes(bins, weight_column=1)

        captured = capsys.readouterr()
        # Check header line
        assert 'Bin' in captured.out
        assert 'Items' in captured.out
        assert 'Weight' in captured.out
        assert '%' in captured.out
        # Check values
        assert '15.00' in captured.out  # 10 + 5
        assert '8.00' in captured.out
        assert 'Total' in captured.out
        assert '23.00' in captured.out

    def test_empty_bins(self, capsys):
        """Test with empty bins."""
        bins = [
            [['a', 10.0]],
            [],  # Empty bin
        ]
        print_binsizes(bins, weight_column=1)

        captured = capsys.readouterr()
        assert '10' in captured.out
        assert '0' in captured.out  # Empty bin has sum 0

    def test_single_bin(self, capsys):
        """Test with single bin."""
        bins = [
            [['a', 10.0], ['b', 20.0], ['c', 30.0]],
        ]
        print_binsizes(bins, weight_column=1)

        captured = capsys.readouterr()
        assert '60' in captured.out
