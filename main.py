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
    parser.add_argument(
        "--query",
        type=str,
        required=False,
        help="SQL query to run. If not provided, reads from stdin.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="output.csv",
        help="Path to the output CSV file (default: output.csv)",
    )
    return parser.parse_args()


def get_query_from_input(initial_query: Optional[str]) -> str:
    if initial_query:
        return initial_query

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
    query = get_query_from_input(args.query)

    try:
        columns, rows = run_hive_query(query, config_path=args.config)
    except Exception as exc:  # noqa: BLE001
        logging.error("Failed to run query: %s", exc)
        raise SystemExit(1) from exc

    if not rows:
        print("Query executed successfully. No rows returned.")
        return

    output_path = Path(args.output)
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


