#!/bin/bash
# Helper script to download Hive JDBC driver
# This script downloads the Hive JDBC driver JAR file

set -e

echo "Hive JDBC Driver Download Helper"
echo "================================"
echo ""

# Default download directory
DOWNLOAD_DIR="./drivers"
DRIVER_VERSION="${1:-3.1.2}"  # Default to 3.1.2, can be overridden

echo "This script will help you download the Hive JDBC driver."
echo ""
echo "Options:"
echo "1. Download from Apache Hive (official)"
echo "2. Download from Maven Central (recommended - standalone JAR)"
echo "3. Manual download instructions"
echo ""
read -p "Choose an option (1-3): " choice

case $choice in
    1)
        echo ""
        echo "Downloading from Apache Hive..."
        echo "Please visit: https://hive.apache.org/downloads.html"
        echo "Or download directly from:"
        echo "https://archive.apache.org/dist/hive/hive-${DRIVER_VERSION}/apache-hive-${DRIVER_VERSION}-bin.tar.gz"
        echo ""
        echo "After extracting, look for: lib/hive-jdbc-${DRIVER_VERSION}-standalone.jar"
        ;;
    2)
        echo ""
        echo "Downloading standalone JAR from Maven Central..."
        mkdir -p "$DOWNLOAD_DIR"
        
        # Try to download using curl or wget
        if command -v curl &> /dev/null; then
            echo "Using curl to download..."
            curl -L -o "${DOWNLOAD_DIR}/hive-jdbc-${DRIVER_VERSION}-standalone.jar" \
                "https://repo1.maven.org/maven2/org/apache/hive/hive-jdbc/${DRIVER_VERSION}/hive-jdbc-${DRIVER_VERSION}-standalone.jar"
        elif command -v wget &> /dev/null; then
            echo "Using wget to download..."
            wget -O "${DOWNLOAD_DIR}/hive-jdbc-${DRIVER_VERSION}-standalone.jar" \
                "https://repo1.maven.org/maven2/org/apache/hive/hive-jdbc/${DRIVER_VERSION}/hive-jdbc-${DRIVER_VERSION}-standalone.jar"
        else
            echo "Error: Neither curl nor wget found. Please install one of them."
            exit 1
        fi
        
        if [ -f "${DOWNLOAD_DIR}/hive-jdbc-${DRIVER_VERSION}-standalone.jar" ]; then
            echo ""
            echo "✓ Successfully downloaded to: ${DOWNLOAD_DIR}/hive-jdbc-${DRIVER_VERSION}-standalone.jar"
            echo ""
            echo "Update your config.yaml with:"
            echo "  hive_driver_jar: \"$(pwd)/${DOWNLOAD_DIR}/hive-jdbc-${DRIVER_VERSION}-standalone.jar\""
        else
            echo "Error: Download failed"
            exit 1
        fi
        ;;
    3)
        echo ""
        echo "Manual Download Instructions:"
        echo "============================="
        echo ""
        echo "1. Apache Hive Official:"
        echo "   - Visit: https://hive.apache.org/downloads.html"
        echo "   - Download the Hive binary distribution"
        echo "   - Extract and find: lib/hive-jdbc-*.jar"
        echo ""
        echo "2. Maven Central (Standalone JAR - Recommended):"
        echo "   - Visit: https://mvnrepository.com/artifact/org.apache.hive/hive-jdbc"
        echo "   - Download the 'standalone' JAR file (includes all dependencies)"
        echo "   - Direct link example:"
        echo "     https://repo1.maven.org/maven2/org/apache/hive/hive-jdbc/${DRIVER_VERSION}/hive-jdbc-${DRIVER_VERSION}-standalone.jar"
        echo ""
        echo "3. Cloudera Distribution (if using Cloudera):"
        echo "   - Visit: https://www.cloudera.com/downloads/connectors/hive/jdbc.html"
        echo ""
        echo "After downloading, update config.yaml with the full path to the JAR file."
        ;;
    *)
        echo "Invalid option"
        exit 1
        ;;
esac

echo ""
echo "Note: Make sure the driver version matches your Hive server version!"

