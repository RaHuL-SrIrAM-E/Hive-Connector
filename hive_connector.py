import logging
from typing import Any, Dict, List, Tuple

import yaml
import jaydebeapi


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

    required_keys = ["hive_jdbc_url", "hive_driver_class", "username", "password"]
    missing = [k for k in required_keys if k not in config]
    if missing:
        raise ValueError(f"Missing required config keys in {config_path}: {', '.join(missing)}")

    return config


def get_hive_connection(config: Dict[str, Any]):
    """
    Create and return a Hive connection using JDBC.

    Parameters
    ----------
    config : Dict[str, Any]
        Configuration dictionary with keys: hive_jdbc_url, hive_driver_class,
        username, password.

    Returns
    -------
    jaydebeapi.Connection
        A JDBC connection object.
    """
    jdbc_url = config["hive_jdbc_url"]
    driver_class = config["hive_driver_class"]
    username = config["username"]
    password = config["password"]
    # Optional: path to Hive JDBC driver JAR file
    driver_jar = config.get("hive_driver_jar")

    try:
        if driver_jar:
            # If JAR path is provided, use it
            conn = jaydebeapi.connect(
                driver_class,
                jdbc_url,
                [username, password],
                driver_jar,
            )
        else:
            # Try to connect without explicit JAR (assumes it's in classpath)
            conn = jaydebeapi.connect(
                driver_class,
                jdbc_url,
                [username, password],
            )
        logger.info("Successfully connected to Hive via JDBC")
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to create Hive JDBC connection to '%s'", jdbc_url)
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

    conn = None
    try:
        conn = get_hive_connection(config)
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        # Get column names from cursor description
        columns = [col[0] for col in cursor.description] if cursor.description else []
        cursor.close()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to execute query against Hive")
        raise
    finally:
        if conn:
            conn.close()

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


