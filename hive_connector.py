import logging
from typing import Any, Dict, List, Tuple

import yaml
from pyhive import hive


logger = logging.getLogger(__name__)


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """
    Load Hive connection configuration from a YAML file.

    Parameters
    ----------
    config_path : str
        Path to the YAML configuration file.

    Returns
    -------
    Dict[str, Any]
        Dictionary with configuration values.
    """
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
    except FileNotFoundError as exc:
        logger.error("Config file not found at path '%s'", config_path)
        raise FileNotFoundError(f"Config file not found: {config_path}") from exc

    required_keys = ["host", "port", "username", "database", "auth"]
    missing = [k for k in required_keys if k not in config]
    if missing:
        raise ValueError(f"Missing required config keys in {config_path}: {', '.join(missing)}")

    return config


def get_hive_connection(config: Dict[str, Any]):
    """
    Create and return a Hive connection using the given config.

    Parameters
    ----------
    config : Dict[str, Any]
        Configuration dictionary with keys: host, port, username, password (optional),
        database, auth.

    Returns
    -------
    hive.Connection
        A PyHive Hive connection object.
    """
    # Password is optional depending on auth type
    password = config.get("password")

    try:
        conn = hive.Connection(
            host=config["host"],
            port=int(config["port"]),
            username=config["username"],
            password=password,
            database=config["database"],
            auth=config["auth"],
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to create Hive connection to host '%s'", config.get("host"))
        raise

    return conn


def run_hive_query(query: str, config_path: str = "config.yaml") -> Tuple[List[str], List[Tuple[Any, ...]]]:
    """
    Run a query against Hive and return the results.

    Parameters
    ----------
    query : str
        The SQL query to execute.
    config_path : str
        Path to the YAML configuration file.

    Returns
    -------
    Tuple[List[str], List[Tuple[Any, ...]]]
        A tuple of (column_names, rows).
    """
    logger.info("Running Hive query using config '%s'", config_path)
    config = load_config(config_path)

    try:
        with get_hive_connection(config) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                # Get column names from cursor description
                columns = [col[0] for col in cursor.description] if cursor.description else []
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to execute query against Hive")
        raise

    logger.info("Query succeeded, retrieved %d rows", len(rows))
    return columns, rows


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Simple manual test (edit the query as needed)
    example_query = "SELECT 1"
    cols, data = run_hive_query(example_query)
    print("Columns:", cols)
    for row in data:
        print(row)


