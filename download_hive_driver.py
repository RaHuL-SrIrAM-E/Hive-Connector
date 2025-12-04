#!/usr/bin/env python3
"""
Helper script to download Hive JDBC driver JAR file.
This script downloads the standalone Hive JDBC driver from Maven Central.
"""

import os
import sys
import urllib.request
from pathlib import Path


def download_file(url: str, destination: str) -> bool:
    """Download a file from URL to destination."""
    try:
        print(f"Downloading from: {url}")
        print(f"Destination: {destination}")
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(destination) if os.path.dirname(destination) else ".", exist_ok=True)
        
        # Download with progress
        def show_progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            percent = min(downloaded * 100 / total_size, 100) if total_size > 0 else 0
            print(f"\rProgress: {percent:.1f}%", end="", flush=True)
        
        urllib.request.urlretrieve(url, destination, show_progress)
        print("\n✓ Download complete!")
        return True
    except Exception as e:
        print(f"\n✗ Download failed: {e}")
        return False


def main():
    print("=" * 50)
    print("Hive JDBC Driver Download Helper")
    print("=" * 50)
    print()
    
    # Default version
    default_version = "3.1.2"
    
    print("This script will download the Hive JDBC driver from Maven Central.")
    print()
    print("Options:")
    print("1. Download standalone JAR (recommended - includes all dependencies)")
    print("2. Show manual download instructions")
    print("3. Exit")
    print()
    
    try:
        choice = input("Choose an option (1-3) [default: 1]: ").strip() or "1"
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(0)
    
    if choice == "1":
        version = input(f"Enter Hive JDBC driver version [default: {default_version}]: ").strip() or default_version
        
        # Maven Central URL for standalone JAR
        url = f"https://repo1.maven.org/maven2/org/apache/hive/hive-jdbc/{version}/hive-jdbc-{version}-standalone.jar"
        
        # Download directory
        download_dir = Path("drivers")
        download_dir.mkdir(exist_ok=True)
        
        destination = download_dir / f"hive-jdbc-{version}-standalone.jar"
        
        if destination.exists():
            overwrite = input(f"File {destination} already exists. Overwrite? (y/N): ").strip().lower()
            if overwrite != "y":
                print("Cancelled.")
                sys.exit(0)
        
        print()
        if download_file(url, str(destination)):
            abs_path = destination.absolute()
            print()
            print("=" * 50)
            print("✓ Successfully downloaded Hive JDBC driver!")
            print("=" * 50)
            print()
            print(f"Location: {abs_path}")
            print()
            print("Update your config.yaml with:")
            print(f'  hive_driver_jar: "{abs_path}"')
            print()
            print("Note: Make sure the driver version matches your Hive server version!")
        else:
            print()
            print("Download failed. Please try manual download (option 2).")
            sys.exit(1)
    
    elif choice == "2":
        print()
        print("=" * 50)
        print("Manual Download Instructions")
        print("=" * 50)
        print()
        print("1. Maven Central (Standalone JAR - Recommended):")
        print("   Visit: https://mvnrepository.com/artifact/org.apache.hive/hive-jdbc")
        print("   Look for the 'standalone' JAR file (includes all dependencies)")
        print("   Direct download example:")
        print(f"   https://repo1.maven.org/maven2/org/apache/hive/hive-jdbc/{default_version}/hive-jdbc-{default_version}-standalone.jar")
        print()
        print("2. Apache Hive Official:")
        print("   Visit: https://hive.apache.org/downloads.html")
        print("   Download the Hive binary distribution")
        print("   Extract and look for: lib/hive-jdbc-*.jar")
        print()
        print("3. Cloudera Distribution (if using Cloudera):")
        print("   Visit: https://www.cloudera.com/downloads/connectors/hive/jdbc.html")
        print()
        print("After downloading, update config.yaml with the full path to the JAR file.")
        print()
    
    elif choice == "3":
        print("Exiting.")
        sys.exit(0)
    
    else:
        print("Invalid option.")
        sys.exit(1)


if __name__ == "__main__":
    main()

