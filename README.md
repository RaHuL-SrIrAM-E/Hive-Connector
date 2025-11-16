## Python Hive Connector

This is a small Python utility to run SQL queries against a Hive server, with
connection details stored in a simple YAML configuration file.

### 1. Install dependencies

From the project root:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Hive connection

Edit `config.yaml` and replace the dummy values with your actual Hive details:

- **host**: Hive server hostname
- **port**: Hive server port (commonly `10000`)
- **username**: Your Hive username
- **password**: Your Hive password (if needed for your auth mechanism)
- **database**: Default database to use
- **auth**: Authentication mechanism, e.g. `NONE`, `LDAP`, `KERBEROS`, `CUSTOM`

Example:

```yaml
host: "hive-server.example.com"
port: 10000
username: "your-username"
password: "your-password"
database: "default"
auth: "NONE"
```

### 3. Run a query and get a CSV

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

### 4. Logging and errors

The scripts use Python's built-in logging to print informational messages and errors
to the console (at the `INFO` level by default). If something goes wrong while loading
the config, connecting to Hive, or running the query, an error message will be printed
and the program will exit with a non-zero status code.


