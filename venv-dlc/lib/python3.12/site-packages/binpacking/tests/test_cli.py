"""Tests for the binpacking CLI binary."""

import os
import subprocess
import sys
import tempfile
import pytest
from io import StringIO
from unittest.mock import patch

from binpacking import binpacking_binary

def run_cli(*args):
    """Run the binpacking CLI by importing and calling main().

    This approach avoids subprocess issues with output capture.
    Returns (exit_code, stdout, stderr).
    """

    old_argv = sys.argv
    stdout_capture = StringIO()
    stderr_capture = StringIO()

    try:
        sys.argv = ['binpacking'] + list(args)
        with patch('sys.stdout', stdout_capture), patch('sys.stderr', stderr_capture):
            try:
                binpacking_binary.main()
                exit_code = 0
            except SystemExit as e:
                exit_code = e.code if e.code is not None else 0
            except Exception as e:
                stderr_capture.write(str(e))
                exit_code = 1
    finally:
        sys.argv = old_argv

    stdout = stdout_capture.getvalue()
    stderr = stderr_capture.getvalue()
    return exit_code, stdout + stderr, stderr


class TestCliHelp:
    """Tests for CLI help output."""

    def test_help_flag(self):
        """--help shows usage information."""
        code, stdout, stderr = run_cli('--help')
        assert code == 0
        assert 'Usage:' in stdout or 'usage:' in stdout.lower()
        assert '-f' in stdout or '--filepath' in stdout
        assert '-V' in stdout or '--volume' in stdout
        assert '-N' in stdout or '--n-bin' in stdout

    def test_h_flag(self):
        """Short -h flag works."""
        code, stdout, stderr = run_cli('-h')
        assert code == 0
        assert 'Usage:' in stdout or 'usage:' in stdout.lower()


class TestCliValidation:
    """Tests for CLI input validation.

    Note: The current CLI implementation has inconsistent exit codes.
    Some errors raise exceptions (exit code 1), others use sys.exit(1),
    and some error paths don't set exit codes properly.
    These tests document the current behavior.
    """

    def test_missing_weight_column(self, sample_csv_with_header):
        """Missing weight column raises exception (shown in stderr)."""
        code, stdout, stderr = run_cli(
            '-f', sample_csv_with_header,
            '-N', '2',
        )
        # Current behavior: raises Exception, exit code is 1
        assert code == 1 or 'Exception' in stderr or 'weight column' in stdout.lower()

    def test_neither_v_nor_n(self, sample_csv_with_header):
        """Error when neither -V nor -N specified."""
        code, stdout, stderr = run_cli(
            '-f', sample_csv_with_header,
            '-c', 'count',
            '-H',
        )
        # Current behavior: prints message and exits with 1
        assert code == 1 or 'Neither' in stdout

    def test_both_v_and_n(self, sample_csv_with_header):
        """Error when both -V and -N specified."""
        code, stdout, stderr = run_cli(
            '-f', sample_csv_with_header,
            '-c', 'count',
            '-H',
            '-V', '100',
            '-N', '2',
        )
        # Current behavior: prints message and exits with 1
        assert code == 1 or 'Both' in stdout


class TestCliConstantBinNumber:
    """Tests for constant bin number mode (-N)."""

    def test_basic_n_mode(self, sample_csv_with_header):
        """Basic -N mode works."""
        code, stdout, stderr = run_cli(
            '-f', sample_csv_with_header,
            '-c', 'count',
            '-H',
            '-N', '2',
        )
        assert code == 0
        assert 'Bin' in stdout and 'Weight' in stdout

        # Cleanup generated files
        base, ext = os.path.splitext(sample_csv_with_header)
        for i in range(2):
            output_file = f"{base}_{i}{ext}"
            if os.path.exists(output_file):
                os.unlink(output_file)

    def test_n_mode_with_bounds(self, sample_csv_with_header):
        """N mode with bounds."""
        code, stdout, stderr = run_cli(
            '-f', sample_csv_with_header,
            '-c', 'count',
            '-H',
            '-N', '2',
            '-l', '4',
            '-u', '15',
        )
        assert code == 0

        # Cleanup
        base, ext = os.path.splitext(sample_csv_with_header)
        for i in range(2):
            output_file = f"{base}_{i}{ext}"
            if os.path.exists(output_file):
                os.unlink(output_file)


class TestCliConstantVolume:
    """Tests for constant volume mode (-V)."""

    def test_basic_v_mode(self, sample_csv_with_header):
        """Basic -V mode works."""
        code, stdout, stderr = run_cli(
            '-f', sample_csv_with_header,
            '-c', 'count',
            '-H',
            '-V', '15',
        )
        assert code == 0
        assert 'Bin' in stdout and 'Weight' in stdout

        # Cleanup generated files (may be variable number)
        base, ext = os.path.splitext(sample_csv_with_header)
        for i in range(10):  # Clean up up to 10 potential files
            output_file = f"{base}_{i}{ext}"
            if os.path.exists(output_file):
                os.unlink(output_file)

    def test_v_mode_with_bounds(self, sample_csv_with_header):
        """V mode with bounds."""
        code, stdout, stderr = run_cli(
            '-f', sample_csv_with_header,
            '-c', 'count',
            '-H',
            '-V', '20',
            '-l', '3',
            '-u', '11',
        )
        assert code == 0

        # Cleanup
        base, ext = os.path.splitext(sample_csv_with_header)
        for i in range(10):
            output_file = f"{base}_{i}{ext}"
            if os.path.exists(output_file):
                os.unlink(output_file)


class TestCliColumnSpecification:
    """Tests for weight column specification."""

    def test_column_by_index(self, sample_csv_without_header):
        """Column specified by numeric index."""
        code, stdout, stderr = run_cli(
            '-f', sample_csv_without_header,
            '-c', '1',
            '-N', '2',
        )
        assert code == 0

        # Cleanup
        base, ext = os.path.splitext(sample_csv_without_header)
        for i in range(2):
            output_file = f"{base}_{i}{ext}"
            if os.path.exists(output_file):
                os.unlink(output_file)

    def test_column_by_name(self, sample_csv_with_header):
        """Column specified by name."""
        code, stdout, stderr = run_cli(
            '-f', sample_csv_with_header,
            '-c', 'count',
            '-H',
            '-N', '2',
        )
        assert code == 0

        # Cleanup
        base, ext = os.path.splitext(sample_csv_with_header)
        for i in range(2):
            output_file = f"{base}_{i}{ext}"
            if os.path.exists(output_file):
                os.unlink(output_file)


class TestCliDelimiter:
    """Tests for custom delimiter."""

    def test_tab_delimiter(self, temp_csv_file):
        """Tab delimiter specified as 'tab'."""
        content = "name\tcount\tcategory\napple\t10\tfruit\nbanana\t5\tfruit\n"
        with open(temp_csv_file, 'w') as f:
            f.write(content)

        code, stdout, stderr = run_cli(
            '-f', temp_csv_file,
            '-c', 'count',
            '-H',
            '-N', '2',
            '-d', 'tab',
        )
        assert code == 0

        # Cleanup
        base, ext = os.path.splitext(temp_csv_file)
        for i in range(2):
            output_file = f"{base}_{i}{ext}"
            if os.path.exists(output_file):
                os.unlink(output_file)

    def test_semicolon_delimiter(self, temp_csv_file):
        """Semicolon delimiter."""
        content = "name;count;category\napple;10;fruit\nbanana;5;fruit\n"
        with open(temp_csv_file, 'w') as f:
            f.write(content)

        code, stdout, stderr = run_cli(
            '-f', temp_csv_file,
            '-c', 'count',
            '-H',
            '-N', '2',
            '-d', ';',
        )
        assert code == 0

        # Cleanup
        base, ext = os.path.splitext(temp_csv_file)
        for i in range(2):
            output_file = f"{base}_{i}{ext}"
            if os.path.exists(output_file):
                os.unlink(output_file)
