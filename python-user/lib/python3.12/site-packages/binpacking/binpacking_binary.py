import argparse
import sys


def main() -> None:
    """CLI entry point for binpacking."""
    parser = argparse.ArgumentParser(
        description="Bin-pack CSV rows by weight column"
    )
    parser.add_argument(
        "-f", "--filepath",
        dest="filepath",
        default=None,
        help="path to the csv-file to be bin-packed",
    )
    parser.add_argument(
        "-V", "--volume",
        dest="V_max",
        type=float,
        default=None,
        help="maximum volume per bin (constant volume algorithm will be used)",
    )
    parser.add_argument(
        "-N", "--n-bin",
        dest="N_bin",
        type=int,
        default=None,
        help="number of bins (constant bin number algorithm will be used)",
    )
    parser.add_argument(
        "-c", "--weight-column",
        dest="weight_column",
        default=None,
        help="integer (or string) giving the column number (or column name in header) where the weight is stored",
    )
    parser.add_argument(
        "-H", "--has-header",
        action="store_true",
        dest="has_header",
        default=False,
        help="parse this option if there is a header in the csv-file",
    )
    parser.add_argument(
        "-d", "--delimiter",
        dest="delim",
        default=',',
        help='delimiter in the csv-file (use "tab" for tabs)',
    )
    parser.add_argument(
        "-q", "--quotechar",
        dest="quotechar",
        default='"',
        help="quotecharacter in the csv-file",
    )
    parser.add_argument(
        "-l", "--lower-bound",
        dest="lower_bound",
        type=float,
        default=None,
        help="weights below this bound will not be considered",
    )
    parser.add_argument(
        "-u", "--upper-bound",
        dest="upper_bound",
        type=float,
        default=None,
        help="weights exceeding this bound will not be considered",
    )
    parser.add_argument(
        "--use-numpy",
        action="store_true",
        dest="use_numpy",
        default=False,
        help="use NumPy-accelerated algorithms (requires numpy to be installed)",
    )
    parser.add_argument(
        "-o", "--output-dir",
        dest="output_dir",
        default=None,
        help="directory to write output files (default: current working directory)",
    )

    args = parser.parse_args()
    opt = vars(args)

    # Extract and remove use_numpy flag before passing to algorithm functions
    use_numpy = opt.pop("use_numpy")

    if opt["weight_column"] is None:
        print("No weight column identifier given")
        sys.exit(1)
    else:
        # if weight column is given try to convert it to a number
        try:
            opt["weight_column"] = int(opt["weight_column"])
        except ValueError:
            pass

    if opt["delim"] == "tab" or opt["delim"] == '"tab"':
        opt["delim"] = '\t'

    # Import the appropriate module based on --use-numpy flag
    if use_numpy:
        try:
            from binpacking.numpy import csv_to_constant_bin_number, csv_to_constant_volume
        except ImportError:
            print("NumPy is required for --use-numpy. Install it with: pip install binpacking[numpy]")
            sys.exit(1)
    else:
        from binpacking.to_constant_bin_number import csv_to_constant_bin_number
        from binpacking.to_constant_volume import csv_to_constant_volume

    if opt["V_max"] is None and opt["N_bin"] is None:
        print("Neither V_max nor N_bin are given. No algorithm can be used.")
        sys.exit(1)
    elif opt["V_max"] is not None and opt["N_bin"] is not None:
        print("Both V_max and N_bin are given. It's unclear which algorithm is to be used.")
        sys.exit(1)
    elif opt["V_max"] is not None and opt["N_bin"] is None:
        opt.pop("N_bin", None)
        csv_to_constant_volume(**opt)
    elif opt["V_max"] is None and opt["N_bin"] is not None:
        opt.pop("V_max", None)
        csv_to_constant_bin_number(**opt)
