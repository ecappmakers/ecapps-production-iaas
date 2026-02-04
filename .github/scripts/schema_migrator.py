#!/usr/bin/env python3
"""
Schema Migration Tool
Compares JSON schema definitions with database and generates migration SQL
"""

import json
import os
import sys
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import argparse
import re


class SchemaMigrator:
    def __init__(self, db_host, db_user, db_pass, db_name):
        self.db_host = db_host
        self.db_user = db_user
        self.db_pass = db_pass
        self.db_name = db_name
        self.connection = None
        self.migration_sql = []
        self.dry_run = False

    def connect(self):
        """Connect to database"""
        try:
            self.connection = mysql.connector.connect(
                host=self.db_host,
                user=self.db_user,
                password=self.db_pass,
                database=self.db_name
            )
            print(f"✅ Connected to {self.db_name}")
            return True
        except Error as e:
            print(f"❌ Connection failed: {e}")
            return False

    def disconnect(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()

    def get_table_structure(self, table_name):
        """Fetch current table structure from database"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(f"DESCRIBE `{table_name}`")
            columns = cursor.fetchall()
            cursor.close()
            return {col['Field']: col for col in columns}
        except Error as e:
            print(f"⚠️ Could not fetch structure for {table_name}: {e}")
            return {}

    def get_all_tables(self):
        """Get list of all tables in database"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SHOW TABLES")
            tables = [row[0] for row in cursor.fetchall()]
            cursor.close()
            return tables
        except Error as e:
            print(f"❌ Failed to get tables: {e}")
            return []

    def get_table_indexes(self, table_name):
        """Get current indexes for a table"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(f"SHOW INDEXES FROM `{table_name}`")
            indexes = cursor.fetchall()
            cursor.close()
            return indexes
        except Error as e:
            print(f"⚠️ Could not fetch indexes for {table_name}: {e}")
            return []

    def parse_schema_files(self, schema_dir):
        """Parse all JSON schema files from directory"""
        schemas = {}
        if not os.path.isdir(schema_dir):
            print(f"⚠️ Schema directory not found: {schema_dir}")
            return schemas

        for filename in os.listdir(schema_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(schema_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        schema = json.load(f)
                        table_name = schema.get('table_name')
                        if table_name:
                            schemas[table_name] = schema
                            print(f"📖 Parsed schema: {table_name}")
                except json.JSONDecodeError as e:
                    print(f"❌ Invalid JSON in {filename}: {e}")
        return schemas

    def generate_create_table(self, table_name, schema):
        """Generate CREATE TABLE SQL from JSON schema"""
        columns_sql = []
        primary_keys = []

        for col in schema.get('columns', []):
            col_def = f"`{col['name']}` {col['type']}"

            if col.get('primary_key'):
                primary_keys.append(col['name'])
                col_def += " PRIMARY KEY"

            if col.get('auto_increment'):
                col_def += " AUTO_INCREMENT"

            if not col.get('nullable', True):
                col_def += " NOT NULL"

            if col.get('unique'):
                col_def += " UNIQUE"

            if 'default' in col:
                default_val = col['default']
                if default_val in ['CURRENT_TIMESTAMP', 'NULL']:
                    col_def += f" DEFAULT {default_val}"
                else:
                    col_def += f" DEFAULT '{default_val}'"

            columns_sql.append(col_def)

        sql = f"CREATE TABLE IF NOT EXISTS `{table_name}` (\n  "
        sql += ",\n  ".join(columns_sql)
        sql += "\n);"

        return sql

    def generate_add_column(self, table_name, column):
        """Generate ALTER TABLE ADD COLUMN"""
        col_def = f"`{column['name']}` {column['type']}"

        if not column.get('nullable', True):
            col_def += " NOT NULL"

        if column.get('unique'):
            col_def += " UNIQUE"

        if 'default' in column:
            default_val = column['default']
            if default_val in ['CURRENT_TIMESTAMP', 'NULL']:
                col_def += f" DEFAULT {default_val}"
            else:
                col_def += f" DEFAULT '{default_val}'"

        return f"ALTER TABLE `{table_name}` ADD COLUMN {col_def};"

    def generate_modify_column(self, table_name, column):
        """Generate ALTER TABLE MODIFY COLUMN"""
        col_def = f"`{column['name']}` {column['type']}"

        if not column.get('nullable', True):
            col_def += " NOT NULL"

        if column.get('unique'):
            col_def += " UNIQUE"

        if 'default' in column:
            default_val = column['default']
            if default_val in ['CURRENT_TIMESTAMP', 'NULL']:
                col_def += f" DEFAULT {default_val}"
            else:
                col_def += f" DEFAULT '{default_val}'"

        return f"ALTER TABLE `{table_name}` MODIFY COLUMN {col_def};"

    def generate_drop_column(self, table_name, column_name):
        """Generate ALTER TABLE DROP COLUMN"""
        return f"ALTER TABLE `{table_name}` DROP COLUMN `{column_name}`;"

    def generate_create_index(self, table_name, index):
        """Generate CREATE INDEX"""
        index_name = index.get('name', f"idx_{table_name}_{index['columns'][0]}")
        columns = ', '.join([f"`{col}`" for col in index['columns']])
        index_type = index.get('type', 'NORMAL')
        
        return f"CREATE INDEX `{index_name}` ON `{table_name}` ({columns});"

    def compare_and_generate_migrations(self, schemas):
        """Compare JSON schemas with database and generate migrations"""
        print("\n🔍 Comparing schemas...\n")
        
        existing_tables = self.get_all_tables()
        migrations = []

        for table_name, schema in schemas.items():
            if table_name not in existing_tables:
                # Create new table
                sql = self.generate_create_table(table_name, schema)
                migrations.append({
                    'type': 'create_table',
                    'table': table_name,
                    'sql': sql,
                    'description': f"Create table: {table_name}"
                })
                print(f"➕ CREATE TABLE: {table_name}")

            else:
                # Compare existing table
                current_cols = self.get_table_structure(table_name)
                schema_cols = {col['name']: col for col in schema.get('columns', [])}

                # Add missing columns
                for col_name, col_def in schema_cols.items():
                    if col_name not in current_cols:
                        sql = self.generate_add_column(table_name, col_def)
                        migrations.append({
                            'type': 'add_column',
                            'table': table_name,
                            'column': col_name,
                            'sql': sql,
                            'description': f"Add column {col_name} to {table_name}"
                        })
                        print(f"➕ ADD COLUMN: {table_name}.{col_name}")

                # Modify existing columns (type changes)
                for col_name, col_def in schema_cols.items():
                    if col_name in current_cols:
                        db_type = current_cols[col_name]['Type']
                        schema_type = col_def['type']
                        if db_type != schema_type:
                            sql = self.generate_modify_column(table_name, col_def)
                            migrations.append({
                                'type': 'modify_column',
                                'table': table_name,
                                'column': col_name,
                                'from_type': db_type,
                                'to_type': schema_type,
                                'sql': sql,
                                'description': f"Modify column {table_name}.{col_name}: {db_type} → {schema_type}"
                            })
                            print(f"🔄 MODIFY COLUMN: {table_name}.{col_name} ({db_type} → {schema_type})")

                # Remove columns not in schema
                for col_name in current_cols:
                    if col_name not in schema_cols:
                        sql = self.generate_drop_column(table_name, col_name)
                        migrations.append({
                            'type': 'drop_column',
                            'table': table_name,
                            'column': col_name,
                            'sql': sql,
                            'description': f"Drop column {col_name} from {table_name}"
                        })
                        print(f"➖ DROP COLUMN: {table_name}.{col_name}")

                # Check indexes
                current_indexes = self.get_table_indexes(table_name)
                schema_indexes = {idx['name']: idx for idx in schema.get('indexes', [])}

                for idx_name, idx_def in schema_indexes.items():
                    if not any(idx['Key_name'] == idx_name for idx in current_indexes):
                        sql = self.generate_create_index(table_name, idx_def)
                        migrations.append({
                            'type': 'create_index',
                            'table': table_name,
                            'index': idx_name,
                            'sql': sql,
                            'description': f"Create index {idx_name} on {table_name}"
                        })
                        print(f"📊 CREATE INDEX: {idx_name} on {table_name}")

        return migrations

    def apply_migrations(self, migrations, dry_run=False):
        """Apply generated migrations"""
        if not migrations:
            print("\n✅ No migrations needed!")
            return True

        print(f"\n📋 Generated {len(migrations)} migration(s)\n")

        if dry_run:
            print("🏃 DRY RUN MODE - No changes will be applied\n")
            for i, migration in enumerate(migrations, 1):
                print(f"{i}. {migration['description']}")
                print(f"   SQL: {migration['sql']}\n")
            return True

        try:
            cursor = self.connection.cursor()
            for i, migration in enumerate(migrations, 1):
                print(f"[{i}/{len(migrations)}] {migration['description']}")
                cursor.execute(migration['sql'])
            self.connection.commit()
            cursor.close()
            print("\n✅ All migrations applied successfully!")
            return True

        except Error as e:
            print(f"\n❌ Migration failed: {e}")
            self.connection.rollback()
            return False

    def save_migration_history(self, migrations, output_file):
        """Save migration history to file"""
        history = {
            'timestamp': datetime.now().isoformat(),
            'total_migrations': len(migrations),
            'migrations': migrations
        }
        
        try:
            with open(output_file, 'w') as f:
                json.dump(history, f, indent=2)
            print(f"\n💾 Migration history saved to {output_file}")
        except IOError as e:
            print(f"⚠️ Could not save migration history: {e}")

    def run(self, schema_dir, dry_run=False, save_history=False):
        """Run the complete migration process"""
        if not self.connect():
            return False

        schemas = self.parse_schema_files(schema_dir)
        if not schemas:
            print("❌ No schema files found!")
            return False

        migrations = self.compare_and_generate_migrations(schemas)
        
        if save_history and migrations:
            history_file = os.path.join(os.path.dirname(schema_dir), 'migration_history.json')
            self.save_migration_history(migrations, history_file)

        success = self.apply_migrations(migrations, dry_run=dry_run)
        self.disconnect()
        return success


def main():
    parser = argparse.ArgumentParser(description='Database Schema Migrator')
    parser.add_argument('--host', required=True, help='Database host')
    parser.add_argument('--user', required=True, help='Database user')
    parser.add_argument('--password', required=True, help='Database password')
    parser.add_argument('--database', required=True, help='Database name')
    parser.add_argument('--schema-dir', required=True, help='Directory with JSON schema files')
    parser.add_argument('--dry-run', action='store_true', help='Show migrations without applying')
    parser.add_argument('--save-history', action='store_true', help='Save migration history')

    args = parser.parse_args()

    migrator = SchemaMigrator(args.host, args.user, args.password, args.database)
    success = migrator.run(args.schema_dir, dry_run=args.dry_run, save_history=args.save_history)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
