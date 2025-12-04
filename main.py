import argparse
import csv
import logging
from pathlib import Path
from typing import Optional

from hive_connector import run_hive_query


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a SQL query against Hive.")
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to the Hive YAML config file (default: config.yaml)",
    )
    query_group = parser.add_mutually_exclusive_group()
    query_group.add_argument(
        "--query",
        type=str,
        help="SQL query to run directly (inline).",
    )
    query_group.add_argument(
        "--query-file",
        "--file",
        "-f",
        type=str,
        dest="query_file",
        help="Path to a file containing the SQL query to run.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Path to the output CSV file. If not provided and using --query-file, output name is derived from query file name (e.g., abc.sql -> abc.csv). Otherwise defaults to output.csv",
    )
    return parser.parse_args()


def get_query_from_input(query: Optional[str], query_file: Optional[str]) -> str:
    # Priority: query_file > query > stdin
    if query_file:
        query_path = Path(query_file)
        if not query_path.exists():
            raise FileNotFoundError(f"Query file not found: {query_file}")
        with query_path.open("r", encoding="utf-8") as f:
            query = f.read().strip()
        if not query:
            raise ValueError(f"Query file is empty: {query_file}")
        return query

    if query:
        return query

    # Fall back to stdin
    print("Enter your Hive SQL query. Finish with Ctrl+D (Unix/macOS) or Ctrl+Z then Enter (Windows):")
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass

    query = "\n".join(lines).strip()
    if not query:
        raise ValueError("No query provided.")
    return query


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    args = parse_args()
    query = get_query_from_input(args.query, args.query_file)

    # Determine output filename
    if args.output:
        # User explicitly provided output filename
        output_path = Path(args.output)
    elif args.query_file:
        # Generate output filename from query file name
        query_file_path = Path(args.query_file)
        output_path = query_file_path.with_suffix(".csv")
    else:
        # Default fallback
        output_path = Path("output.csv")

    try:
        columns, rows = run_hive_query(query, config_path=args.config)
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


