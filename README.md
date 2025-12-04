## Python Hive Connector

This is a small Python utility to run SQL queries against a Hive server, with
connection details stored in a simple YAML configuration file.

### 1. Prerequisites

**Java is required**: This connector uses JDBC, which requires Java to be installed on your system.

- **Install Java**: Download and install JDK 8 or later from [Oracle](https://www.oracle.com/java/technologies/downloads/) or [OpenJDK](https://openjdk.org/)
- **Verify installation**: Run `java -version` in your terminal to confirm Java is installed
- **Set JAVA_HOME** (optional but recommended): Set the `JAVA_HOME` environment variable to point to your Java installation directory

**On macOS** (using Homebrew):
```bash
brew install openjdk
```

**On Linux** (Ubuntu/Debian):
```bash
sudo apt-get update
sudo apt-get install default-jdk
```

**On Windows**: Download and install from the Oracle or OpenJDK website, then add Java to your PATH.

### 2. Install Python dependencies

From the project root:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**Note**: If you encounter errors about JPype1 or Java, make sure:
1. Java is installed and accessible via `java -version`
2. You've installed all dependencies: `pip install --upgrade JPype1 JayDeBeApi`

### 3. Configure Hive connection

Edit `config.yaml` and replace the dummy values with your actual Hive JDBC credentials:

- **hive_jdbc_url**: Full JDBC URL for Hive (e.g., `jdbc:hive2://hostname:port/database`)
- **hive_driver_class**: JDBC driver class name (typically `org.apache.hive.jdbc.HiveDriver`)
- **username**: Your Hive username
- **password**: Your Hive password
- **hive_driver_jar** (optional): Path to the Hive JDBC driver JAR file if not in classpath

Example:

```yaml
hive_jdbc_url: "jdbc:hive2://hive-server.example.com:10000/default"
hive_driver_class: "org.apache.hive.jdbc.HiveDriver"
username: "your-username"
password: "your-password"
# Optional: uncomment and set if you need to specify the JAR path
# hive_driver_jar: "/path/to/hive-jdbc-3.1.2-standalone.jar"
```

**Note**: You'll need the Hive JDBC driver JAR file. You can download it from your Hive distribution or Apache Hive releases. If the JAR is in your Java classpath, you don't need to specify `hive_driver_jar`. Otherwise, provide the full path to the JAR file.

### 4. Run a query and get a CSV

You can pass a query directly on the command line and it will be written to a CSV file
(`output.csv` by default):

```bash
python main.py --query "SELECT * FROM your_table LIMIT 10" --output results.csv
```

If you omit `--output`, the file `output.csv` will be created in the current directory.

Or omit `--query` and type/paste a multi-line query, then finish with Ctrl+D; the results
will still be written to the CSV file:

```bash
python main.py
```

To use a different config file:

```bash
python main.py --config path/to/another_config.yaml --query "SELECT 1"
```

### 5. Troubleshooting

**Error: "can't find org.jpype.jar support library" or similar JPype errors**

This usually means:
1. **Java is not installed**: Install JDK 8 or later and ensure it's in your PATH
2. **JPype1 is not properly installed**: Try `pip install --upgrade JPype1`
3. **JAVA_HOME is not set**: Set the `JAVA_HOME` environment variable to your Java installation directory

**To verify Java installation:**
```bash
java -version
```

**To set JAVA_HOME (macOS/Linux):**
```bash
export JAVA_HOME=$(/usr/libexec/java_home)  # macOS
# or
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64  # Linux (adjust path as needed)
```

**To set JAVA_HOME (Windows):**
```cmd
set JAVA_HOME=C:\Program Files\Java\jdk-11
```

### 6. Logging and errors

The scripts use Python's built-in logging to print informational messages and errors
to the console (at the `INFO` level by default). If something goes wrong while loading
the config, connecting to Hive, or running the query, an error message will be printed
and the program will exit with a non-zero status code.


