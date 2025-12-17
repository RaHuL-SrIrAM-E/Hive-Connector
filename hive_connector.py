import logging
import os
import shutil
from typing import Any, Dict, List, Tuple

import yaml

try:
    import jaydebeapi
except ImportError as exc:
    raise ImportError(
        "JayDeBeApi is not installed. Please install it with: pip install JayDeBeApi JPype1"
    ) from exc


logger = logging.getLogger(__name__)


def check_java_available() -> bool:
    """
    Check if Java is installed and available in the system PATH.

    Returns
    -------
    bool
        True if Java is available, False otherwise.
    """
    java_path = shutil.which("java")
    if java_path:
        logger.info("Java found at: %s", java_path)
        return True
    logger.warning("Java not found in PATH. JayDeBeApi requires Java to be installed.")
    return False


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


def get_query_from_config(config: Dict[str, Any], config_path: str = "config.yaml") -> str:
    """
    Get SQL query from configuration file.
    Supports both inline 'query' and 'query_file' options.

    Parameters
    ----------
    config : Dict[str, Any]
        Configuration dictionary.
    config_path : str
        Path to the config file (used for resolving relative paths in query_file).

    Returns
    -------
    str
        The SQL query string.
    """
    query_file = config.get("query_file")
    query = config.get("query")

    # Priority: query_file > query
    if query_file:
        # Resolve path relative to config file location
        config_dir = Path(config_path).parent
        query_file_path = (config_dir / query_file).resolve()
        
        if not query_file_path.exists():
            raise FileNotFoundError(f"Query file not found: {query_file_path}")
        
        with query_file_path.open("r", encoding="utf-8") as f:
            query_text = f.read().strip()
        
        if not query_text:
            raise ValueError(f"Query file is empty: {query_file_path}")
        
        logger.info("Loaded query from file: %s", query_file_path)
        return query_text

    if query:
        query_text = query.strip()
        if not query_text:
            raise ValueError("Query in config file is empty")
        logger.info("Loaded query from config file")
        return query_text

    raise ValueError(
        "No query specified in config file. Please provide either 'query' (inline SQL) "
        "or 'query_file' (path to SQL file) in the config file."
    )


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
    # Check if Java is available before attempting connection
    if not check_java_available():
        raise RuntimeError(
            "Java is not installed or not in PATH. "
            "Please install Java (JDK 8 or later) and ensure it's in your system PATH. "
            "You can verify by running: java -version"
        )

    jdbc_url = config["hive_jdbc_url"]
    driver_class = config["hive_driver_class"]
    username = config["username"]
    password = config["password"]
    # Optional: path to Hive JDBC driver JAR file
    driver_jar = config.get("hive_driver_jar")

    try:
        if driver_jar:
            # If JAR path is provided, use it
            if not os.path.exists(driver_jar):
                raise FileNotFoundError(f"Hive JDBC driver JAR not found at: {driver_jar}")
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
        # Provide more helpful error messages for common issues
        error_msg = str(exc).lower()
        if "jpype" in error_msg or "java" in error_msg:
            raise RuntimeError(
                f"Java/JDBC connection error: {exc}\n"
                "This usually means:\n"
                "1. Java is not installed - install JDK 8 or later\n"
                "2. JPype1 is not properly installed - try: pip install --upgrade JPype1\n"
                "3. JAVA_HOME environment variable is not set correctly"
            ) from exc
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


