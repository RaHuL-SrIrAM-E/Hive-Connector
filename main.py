import argparse
import csv
import logging
from pathlib import Path
from typing import Optional

from hive_connector import load_config, get_query_from_config, run_hive_query


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a SQL query against Hive using configuration from config file.",
        epilog="""
Examples:
  # Run query using InputQuery1 configuration
  python3 main.py --config config.yaml --tag InputQuery1

  # Short form
  python3 main.py -t InputQuery1

  # With custom output file
  python3 main.py --tag InputQuery2 --output results.csv

  # Using different config file
  python3 main.py --config my_config.yaml --tag InputQuery1
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to the Hive YAML config file containing credentials and query (default: config.yaml)",
    )
    parser.add_argument(
        "--tag",
        "-t",
        type=str,
        default=None,
        help="Tag name of the configuration to use (e.g., InputQuery1, InputQuery2). Required when config file uses tagged configurations. Each tag contains its own connection settings and query.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Path to the output CSV file. If not provided, output name is derived from query_file in config (e.g., abc.sql -> abc.csv), or defaults to output.csv",
    )
    return parser.parse_args()


def determine_output_path(config: dict, config_path: str, explicit_output: Optional[str]) -> Path:
    """
    Determine the output CSV file path based on config and command line arguments.

    Parameters
    ----------
    config : dict
        Configuration dictionary.
    config_path : str
        Path to the config file.
    explicit_output : Optional[str]
        Explicitly provided output path from command line.

    Returns
    -------
    Path
        Path to the output CSV file.
    """
    if explicit_output:
        # Command line argument takes highest priority
        return Path(explicit_output)

    if "output" in config:
        # Use output path from config
        output_path = Path(config["output"])
        # Resolve relative paths relative to config file location
        if not output_path.is_absolute():
            config_dir = Path(config_path).parent
            output_path = (config_dir / output_path).resolve()
        return output_path

    # Try to derive from query_file
    query_file = config.get("query_file")
    if query_file:
        config_dir = Path(config_path).parent
        query_file_path = (config_dir / query_file).resolve()
        return query_file_path.with_suffix(".csv")

    # Default fallback
    return Path("output.csv")


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    args = parse_args()

    try:
        # Load configuration for the specified tag
        config = load_config(args.config, tag=args.tag)
        
        # Get query from config
        query = get_query_from_config(config, args.config)
        
        # Determine output path
        output_path = determine_output_path(config, args.config, args.output)

        # Execute query
        columns, rows = run_hive_query(query, config=config)

    except Exception as exc:  # noqa: BLE001
        logging.error("Failed to run query: %s", exc)
        raise SystemExit(1) from exc

    if not rows:
        print("Query executed successfully. No rows returned.")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        if columns:
            writer.writerow(columns)
        for row in rows:
            writer.writerow(row)

    print(f"Query executed successfully. Wrote {len(rows)} rows to '{output_path}'.")


if __name__ == "__main__":
    main()


