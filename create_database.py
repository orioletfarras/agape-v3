#!/usr/bin/env python3
"""Script to create the database in Aurora MySQL"""

import pymysql
import sys

# Aurora connection details
HOST = "database-2.cluster-csf25ija4rhk.eu-south-2.rds.amazonaws.com"
USER = "admin"
PASSWORD = "Pwn20141130!"
DATABASE = "agape_v3"

def create_database():
    """Create database if it doesn't exist"""
    try:
        # Connect without specifying database
        connection = pymysql.connect(
            host=HOST,
            user=USER,
            password=PASSWORD,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

        with connection:
            with connection.cursor() as cursor:
                # Create database if not exists
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DATABASE} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                print(f"✓ Database '{DATABASE}' created successfully (or already exists)")

                # Show databases
                cursor.execute("SHOW DATABASES")
                databases = cursor.fetchall()
                print("\n📋 Available databases:")
                for db in databases:
                    print(f"  - {db['Database']}")

            connection.commit()

        print(f"\n✓ Successfully connected to Aurora MySQL at {HOST}")
        return True

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return False

if __name__ == "__main__":
    success = create_database()
    sys.exit(0 if success else 1)
