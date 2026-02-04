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
            # If database doesn't exist, create it first
            if "Unknown database" in str(e):
                print(f"⚠️ Database {self.db_name} doesn't exist, creating...")
                if self.create_database():
                    return self.connect()
            print(f"❌ Connection failed: {e}")
            return False

    def create_database(self):
        """Create database if it doesn't exist"""
        try:
            temp_conn = mysql.connector.connect(
                host=self.db_host,
                user=self.db_user,
                password=self.db_pass
            )
            cursor = temp_conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{self.db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci")
            cursor.close()
            temp_conn.close()
            print(f"✅ Database created: {self.db_name}")
            return True
        except Error as e:
            print(f"❌ Could not create database: {e}")
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

    def get_foreign_keys(self, table_name):
        """Get current foreign keys for a table"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(f"""
                SELECT CONSTRAINT_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
                FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                WHERE TABLE_NAME = '{table_name}' AND REFERENCED_TABLE_NAME IS NOT NULL
            """)
            fks = cursor.fetchall()
            cursor.close()
            return fks
        except Error as e:
            print(f"⚠️ Could not fetch foreign keys for {table_name}: {e}")
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
        """Parse all JSON schema files from directory (supports both dict and list formats)"""
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
                            # Normalize schema format: convert dict columns to list if needed
                            if isinstance(schema.get('columns'), dict):
                                columns_list = []
                                for col_name, col_def in schema['columns'].items():
                                    col_obj = {'name': col_name}
                                    col_obj.update(col_def)
                                    columns_list.append(col_obj)
                                schema['columns'] = columns_list
                            
                            # Normalize indexes format if dict
                            if isinstance(schema.get('indexes'), dict):
                                indexes_list = []
                                for idx_name, idx_def in schema['indexes'].items():
                                    idx_obj = {'name': idx_name}
                                    idx_obj.update(idx_def)
                                    indexes_list.append(idx_obj)
                                schema['indexes'] = indexes_list
                            
                            schemas[table_name] = schema
                            print(f"📖 Parsed schema: {table_name}")
                except json.JSONDecodeError as e:
                    print(f"❌ Invalid JSON in {filename}: {e}")
        return schemas

    def generate_create_table(self, table_name, schema):
        """Generate CREATE TABLE SQL from JSON schema with full constraint support"""
        columns_sql = []
        primary_keys = []
        constraints = []

        for col_name, col_def in schema.get('columns', {}).items() if isinstance(schema.get('columns'), dict) else enumerate(schema.get('columns', [])):
            # Handle dict format
            if isinstance(schema.get('columns'), dict):
                col_obj = {'name': col_name}
                col_obj.update(col_def)
            else:
                col_obj = col_def

            col_sql = f"`{col_obj['name']}` {col_obj['type']}"

            if col_obj.get('primary_key'):
                primary_keys.append(col_obj['name'])
                col_sql += " PRIMARY KEY"

            if col_obj.get('auto_increment'):
                col_sql += " AUTO_INCREMENT"

            if not col_obj.get('nullable', True):
                col_sql += " NOT NULL"

            if col_obj.get('unique') and not col_obj.get('primary_key'):
                col_sql += " UNIQUE"

            if 'default' in col_obj:
                default_val = col_obj['default']
                if default_val in ['CURRENT_TIMESTAMP', 'NULL']:
                    col_sql += f" DEFAULT {default_val}"
                else:
                    col_sql += f" DEFAULT '{default_val}'"

            columns_sql.append(col_sql)

            # Collect foreign keys
            if col_obj.get('foreign_key'):
                refs = col_obj.get('references', {})
                ref_table = refs.get('table')
                ref_column = refs.get('column')
                if ref_table and ref_column:
                    constraint_name = f"fk_{table_name}_{col_obj['name']}"
                    constraints.append(f"CONSTRAINT `{constraint_name}` FOREIGN KEY (`{col_obj['name']}`) REFERENCES `{ref_table}` (`{ref_column}`)")

        # Add indexes
        indexes = schema.get('indexes', {})
        for idx_name, idx_def in (indexes.items() if isinstance(indexes, dict) else enumerate(indexes)):
            if isinstance(indexes, dict):
                idx_obj = {'name': idx_name}
                idx_obj.update(idx_def)
            else:
                idx_obj = idx_def

            cols = ", ".join([f"`{c}`" for c in idx_obj.get('columns', [])])
            idx_type = idx_obj.get('type', 'KEY').upper()

            if idx_type == "UNIQUE":
                constraints.append(f"UNIQUE KEY `{idx_obj['name']}` ({cols})")
            elif idx_type == "PRIMARY":
                pass  # Already handled
            else:
                constraints.append(f"KEY `{idx_obj['name']}` ({cols})")

        # Build final SQL
        sql = f"CREATE TABLE IF NOT EXISTS `{table_name}` (\n  "
        all_parts = columns_sql + constraints
        sql += ",\n  ".join(all_parts)
        sql += f"\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;"

        return sql

    def generate_add_column(self, table_name, column):
        """Generate ALTER TABLE ADD COLUMN"""
        col_name = column.get('name', column) if isinstance(column, dict) else column
        col_def_obj = column if isinstance(column, dict) else {}
        
        col_sql = f"`{col_name}` {col_def_obj.get('type', 'VARCHAR(255)')}"

        if not col_def_obj.get('nullable', True):
            col_sql += " NOT NULL"

        if col_def_obj.get('unique'):
            col_sql += " UNIQUE"

        if 'default' in col_def_obj:
            default_val = col_def_obj['default']
            if default_val in ['CURRENT_TIMESTAMP', 'NULL']:
                col_sql += f" DEFAULT {default_val}"
            else:
                col_sql += f" DEFAULT '{default_val}'"

        return f"ALTER TABLE `{table_name}` ADD COLUMN {col_sql};"

    def generate_modify_column(self, table_name, column):
        """Generate ALTER TABLE MODIFY COLUMN"""
        col_name = column.get('name', column) if isinstance(column, dict) else column
        col_def_obj = column if isinstance(column, dict) else {}
        
        col_sql = f"`{col_name}` {col_def_obj.get('type', 'VARCHAR(255)')}"

        if not col_def_obj.get('nullable', True):
            col_sql += " NOT NULL"

        if col_def_obj.get('unique'):
            col_sql += " UNIQUE"

        if 'default' in col_def_obj:
            default_val = col_def_obj['default']
            if default_val in ['CURRENT_TIMESTAMP', 'NULL']:
                col_sql += f" DEFAULT {default_val}"
            else:
                col_sql += f" DEFAULT '{default_val}'"

        return f"ALTER TABLE `{table_name}` MODIFY COLUMN {col_sql};"

    def generate_drop_column(self, table_name, column_name):
        """Generate ALTER TABLE DROP COLUMN"""
        return f"ALTER TABLE `{table_name}` DROP COLUMN `{column_name}`;"
f isinstance(index, dict):
            index_name = index.get('name', f"idx_{table_name}_{index.get('columns', ['id'])[0]}")
            columns = ', '.join([f"`{col}`" for col in index.get('columns', [])])
            index_type = index.get('type', 'NORMAL')
        else:
            index_name = f"idx_{table_name}_{index}"
            columns = f"`{index}`"
            index_type = "NORMAL"
        
        if index_type.upper() == "UNIQUE":
            return f"CREATE UNIQUE INDEX `{index_name}` ON `{table_name}` ({columns});"
        else:
            return f"CREATE INDEX `{index_name}` ON `{table_name}` ({columns});"

    def generate_drop_index(self, table_name, index_name):
        """Generate DROP INDEX"""
        return f"DROP INDEX `{index_name}` ON `{table_name}`;"

    def generate_add_foreign_key(self, table_name, column_name, ref_table, ref_column):
        """Generate ALTER TABLE ADD FOREIGN KEY"""
        constraint_name = f"fk_{table_name}_{column_name}"
        return f"ALTER TABLE `{table_name}` ADD CONSTRAINT `{constraint_name}` FOREIGN KEY (`{column_name}`) REFERENCES `{ref_table}` (`{ref_column}`);"

    def generate_drop_foreign_key(self, table_name, constraint_name):
        """Generate ALTER TABLE DROP FOREIGN KEY"""
        return f"ALTER TABLE `{table_name}` DROP FOREIGN KEY `{constraint_name}`
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
                schema_cols = schema.get('columns', {})
                
                # Normalize schema columns format
                if isinstance(schema_cols, list):
                    schema_cols = {col['name']: col for col in schema_cols}

                # 1. Add missing columns
                for col_name, col_def in schema_cols.items():
                    if col_name not in current_cols:
                        sql = self.generate_add_column(table_name, {**col_def, 'name': col_name})
                        migrations.append({
                            'type': 'add_column',
                            'table': table_name,
                            'column': col_name,
                            'sql': sql,
                            'description': f"Add column {col_name} to {table_name}"
                        })
                        print(f"➕ ADD COLUMN: {table_name}.{col_name}")

                # 2. Modify existing columns (type changes, nullable changes, etc.)
                for col_name, col_def in schema_cols.items():
                    if col_name in current_cols:
                        db_col = current_cols[col_name]
                        db_type = db_col['Type']
                        schema_type = col_def.get('type', 'VARCHAR(255)')
                        
                        # Check if type changed or nullable changed
                        needs_modify = False
                        if db_type != schema_type:
                            needs_modify = True
                        
                        if needs_modify:
                            sql = self.generate_modify_column(table_name, {**col_def, 'name': col_name})
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

                # 3. Drop columns not in schema
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

                # 4. Handle indexes
                current_indexes = self.get_table_indexes(table_name)
                schema_indexes = schema.get('indexes', {})
                
                # Normalize indexes format
                if isinstance(schema_indexes, list):
                    schema_indexes = {idx['name']: idx for idx in schema_indexes}

                # Add missing indexes
                for idx_name, idx_def in schema_indexes.items():
                    if not any(idx['Key_name'] == idx_name for idx in current_indexes):
                        sql = self.generate_create_index(table_name, {**idx_def, 'name': idx_name})
                        migrations.append({
                            'type': 'create_index',
                            'table': table_name,
                            'index': idx_name,
                            'sql': sql,
                            'description': f"Create index {idx_name} on {table_name}"
                        })
                        print(f"📊 CREATE INDEX: {idx_name} on {table_name}")

                # Drop removed indexes
                for idx in current_indexes:
                    idx_name = idx['Key_name']
                    if idx_name not in ['PRIMARY'] and idx_name not in schema_indexes:
                        sql = self.generate_drop_index(table_name, idx_name)
                        migrations.append({
                            'type': 'drop_index',
                            'table': table_name,
                            'index': idx_name,
                            'sql': sql,
                            'description': f"Drop index {idx_name} from {table_name}"
                        })
                        print(f"🗑️ DROP INDEX: {idx_name} from {table_name}")

                # 5. Handle foreign keys
                current_fks = self.get_foreign_keys(table_name)
                schema_fks = {}
                
                # Collect expected foreign keys from schema
                for col_name, col_def in schema_cols.items():
                    if col_def.get('foreign_key'):
                        refs = col_def.get('references', {})
                        ref_table = refs.get('table')
                        ref_column = refs.get('column')
                        if ref_table and ref_column:
                            fk_name = f"fk_{table_name}_{col_name}"
                            schema_fks[fk_name] = {
                                'column': col_name,
                                'ref_table': ref_table,
                                'ref_column': ref_column
                            }

                # Add missing foreign keys
                for fk_name, fk_def in schema_fks.items():
                    if not any(fk['CONSTRAINT_NAME'] == fk_name for fk in current_fks):
                        sql = self.generate_add_foreign_key(
                            table_name,
                            fk_def['column'],
                            fk_def['ref_table'],
                            fk_def['ref_column']
                        )
                        migrations.append({
                            'type': 'add_foreign_key',
                            'table': table_name,
                            'constraint': fk_name,
                            'sql': sql,
                            'description': f"Add foreign key {fk_name}"
                        })
                        print(f"🔗 ADD FOREIGN KEY: {fk_name}")

                # Drop removed foreign keys
                for fk in current_fks:
                    fk_name = fk['CONSTRAINT_NAME']
                    if fk_name not in schema_fks:
                        sql = self.generate_drop_foreign_key(table_name, fk_name)
                        migrations.append({
                            'type': 'drop_foreign_key',
                            'table': table_name,
                            'constraint': fk_name,
                            'sql': sql,
                            'description': f"Drop foreign key {fk_name}"
                        })
                        print(f"🔓 DROP FOREIGN KEY: {fk_name}")

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

    def run(self, sche

    def migrate(self, schema_dir, dry_run=False):
        """Alias for run() method - called by pipeline"""
        return self.run(schema_dir, dry_run=dry_run, save_history=True)ma_dir, dry_run=False, save_history=False):
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
