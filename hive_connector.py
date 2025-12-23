import logging
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

try:
    import jaydebeapi
except ImportError as exc:
    raise ImportError(
        "JayDeBeApi is not installed. Please install it with: pip install JayDeBeApi JPype1"
    ) from exc

try:
    import jpype
except ImportError:
    jpype = None  # jpype might not be directly importable, but jaydebeapi uses it internally


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


def load_config(config_path: str = "config.yaml", tag: Optional[str] = None) -> Dict[str, Any]:
    """
    Load Hive connection configuration from a YAML file.
    Supports both flat config structure and named tag-based configurations.

    Parameters
    ----------
    config_path : str
        Path to the YAML configuration file.
    tag : Optional[str]
        Tag name to load specific configuration. If None, loads flat config structure.

    Returns
    -------
    Dict[str, Any]
        Dictionary with configuration values for the specified tag or flat config.
    """
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            all_configs = yaml.safe_load(f) or {}
    except FileNotFoundError as exc:
        logger.error("Config file not found at path '%s'", config_path)
        raise FileNotFoundError(f"Config file not found: {config_path}") from exc

    # If tag is specified, load that specific configuration
    if tag:
        if tag not in all_configs:
            available_tags = ", ".join(all_configs.keys()) if all_configs else "none"
            raise ValueError(
                f"Tag '{tag}' not found in config file '{config_path}'. "
                f"Available tags: {available_tags}"
            )
        config = all_configs[tag]
        if not isinstance(config, dict):
            raise ValueError(f"Tag '{tag}' in config file must contain a dictionary of settings")
        logger.info("Loaded configuration for tag '%s'", tag)
    else:
        # Load flat config structure (backward compatibility)
        config = all_configs

    # Validate required keys
    required_keys = ["hive_jdbc_url", "hive_driver_class", "username", "password"]
    missing = [k for k in required_keys if k not in config]
    if missing:
        tag_info = f" (tag: {tag})" if tag else ""
        raise ValueError(
            f"Missing required config keys in {config_path}{tag_info}: {', '.join(missing)}"
        )

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


def configure_ssl_settings(config: Dict[str, Any]) -> None:
    """
    Configure SSL/TLS settings for Java/JDBC connections.
    Sets Java system properties for truststore and SSL verification.

    Parameters
    ----------
    config : Dict[str, Any]
        Configuration dictionary that may contain SSL settings.
    """
    if jpype is None:
        logger.warning("jpype not available - SSL settings will be ignored. Install JPype1 for SSL support.")
        return

    # Check if SSL configuration is provided
    truststore_path = config.get("truststore_path")
    truststore_password = config.get("truststore_password", "")
    truststore_type = config.get("truststore_type", "JKS")
    disable_ssl_verification = config.get("disable_ssl_verification", False)

    # Ensure JVM is started
    if not jpype.isJVMStarted():
        jpype.startJVM(jpype.getDefaultJVMPath())

    if disable_ssl_verification:
        logger.warning("SSL certificate verification is DISABLED. This is not recommended for production!")
        # Note: Completely disabling SSL verification requires custom TrustManager
        # For now, we'll set empty truststore which may help in some cases
        jpype.java.lang.System.setProperty("javax.net.ssl.trustStore", "")
        jpype.java.lang.System.setProperty("javax.net.ssl.trustStorePassword", "")

    if truststore_path:
        truststore_path_obj = Path(truststore_path)
        if not truststore_path_obj.exists():
            raise FileNotFoundError(f"Truststore file not found: {truststore_path}")
        
        if not truststore_path_obj.is_absolute():
            raise ValueError(f"Truststore path must be absolute: {truststore_path}")

        logger.info("Configuring SSL truststore: %s (type: %s)", truststore_path, truststore_type)
        
        # Set Java system properties for SSL
        jpype.java.lang.System.setProperty("javax.net.ssl.trustStore", str(truststore_path_obj))
        jpype.java.lang.System.setProperty("javax.net.ssl.trustStorePassword", truststore_password)
        jpype.java.lang.System.setProperty("javax.net.ssl.trustStoreType", truststore_type)
        
        # Additional SSL properties (may be needed for client certificates)
        if config.get("keystore_path"):
            keystore_path_obj = Path(config["keystore_path"])
            keystore_password = config.get("keystore_password", truststore_password)
            keystore_type = config.get("keystore_type", truststore_type)
            jpype.java.lang.System.setProperty("javax.net.ssl.keyStore", str(keystore_path_obj))
            jpype.java.lang.System.setProperty("javax.net.ssl.keyStorePassword", keystore_password)
            jpype.java.lang.System.setProperty("javax.net.ssl.keyStoreType", keystore_type)


def get_hive_connection(config: Dict[str, Any]):
    """
    Create and return a Hive connection using JDBC.

    Parameters
    ----------
    config : Dict[str, Any]
        Configuration dictionary with keys: hive_jdbc_url, hive_driver_class,
        username, password. May also contain SSL settings.

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

    # Configure SSL settings if provided (must be done before connecting)
    if config.get("truststore_path") or config.get("disable_ssl_verification"):
        # Ensure JPype is started
        if not jpype.isJVMStarted():
            # Start JVM if not already started
            jpype.startJVM(jpype.getDefaultJVMPath())
        configure_ssl_settings(config)

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
        if "pkix" in error_msg or "certificate" in error_msg or "ssl" in error_msg:
            raise RuntimeError(
                f"SSL/Certificate error: {exc}\n"
                "This is usually a PKIX certificate validation issue. Solutions:\n"
                "1. Provide a truststore_path in config with the CA certificate\n"
                "2. Import the server's certificate into a Java truststore\n"
                "3. (Not recommended) Set disable_ssl_verification: true in config\n"
                "\n"
                "To create a truststore:\n"
                "  keytool -import -alias hive-cert -file server.crt -keystore truststore.jks -storepass changeit"
            ) from exc
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


def run_hive_query(query: str, config: Dict[str, Any]) -> Tuple[List[str], List[Tuple[Any, ...]]]:
    """
    Run a query against Hive and return the results.

    Parameters
    ----------
    query : str
        The SQL query to execute.
    config : Dict[str, Any]
        Configuration dictionary with connection settings.

    Returns
    -------
    Tuple[List[str], List[Tuple[Any, ...]]]
        A tuple of (column_names, rows).
    """
    logger.info("Running Hive query")

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
    config = load_config("config.yaml", tag="InputQuery1")
    query = get_query_from_config(config, "config.yaml")
    cols, data = run_hive_query(query, config=config)
    print("Columns:", cols)
    for row in data:
        print(row)


