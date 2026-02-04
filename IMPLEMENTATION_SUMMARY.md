# Schema Migration System - Implementation Summary

## What Was Implemented

A **JSON-based database schema migration system** that automatically:
- ✅ Compares JSON schema definitions with actual database
- ✅ Generates ALTER TABLE queries automatically
- ✅ Creates new tables from JSON definitions
- ✅ Adds/modifies/removes columns safely
- ✅ Creates/manages indexes
- ✅ Tracks all migrations in history
- ✅ Supports multiple databases with separate users

---

## Files Created/Modified

### 1. Python Migration Script
**File**: `.github/scripts/schema_migrator.py`

- Reads JSON schema files
- Connects to database
- Compares structures
- Generates SQL migrations
- Applies changes with rollback
- Saves migration history

**Key Classes**:
- `SchemaMigrator` - Main migration engine
- Supports dry-run mode for testing

### 2. Updated Pipeline
**File**: `.github/workflows/production_pipeline.yml`

**Changes**:
- `build-database` job now copies JSON schemas instead of SQL files
- New `🔄 Apply Schema Migrations` step runs the Python script
- Supports environment variables: DB_PASS, DB_USER, DB_USER_PASS
- Migrations run after static sites sync but before verification

**New Flow**:
```
Plan → Build (DB) → Deploy (setup) → Sync Schemas → Run Migrations → Verify
```

### 3. Example Schema Repository
**Location**: `example-schema-repo/`

**Structure**:
```
├── db-config.json          # Database metadata
├── schema/
│   ├── users.json          # Table definition
│   ├── products.json       # Table definition
│   └── [more tables...]
└── README.md               # Documentation
```

**Example db-config.json**:
```json
{
  "database_name": "app_db",
  "database_user": "app_user",
  "secret_name": "DB_APP_PASSWORD",
  "description": "Main application database"
}
```

**Example Table Schema (users.json)**:
```json
{
  "table_name": "users",
  "columns": [
    {
      "name": "id",
      "type": "INT",
      "primary_key": true,
      "auto_increment": true
    },
    {
      "name": "username",
      "type": "VARCHAR(255)",
      "unique": true,
      "nullable": false
    }
  ],
  "indexes": [
    {"name": "idx_username", "columns": ["username"]}
  ]
}
```

### 4. Setup Scripts
**File**: `scripts/init-schema-repo.sh`

- Quick template generator for new database schema repos
- Creates default structure
- Includes example tables

### 5. Documentation
**Files Created**:
- `SCHEMA_MIGRATION_GUIDE.md` - Complete setup & usage guide
- `example-schema-repo/README.md` - How migrations work

---

## Column Definition Format

### Supported Properties

| Property | Type | Required | Example | Notes |
|----------|------|----------|---------|-------|
| name | string | ✅ | "username" | Column name |
| type | string | ✅ | "VARCHAR(255)" | MySQL data type |
| primary_key | boolean | ❌ | true | Set as PRIMARY KEY |
| auto_increment | boolean | ❌ | true | AUTO_INCREMENT |
| nullable | boolean | ❌ | false | Allow NULL (default: true) |
| unique | boolean | ❌ | true | UNIQUE constraint |
| default | string/number | ❌ | "CURRENT_TIMESTAMP" | Default value |

### Data Type Examples

```
INT, BIGINT, SMALLINT
DECIMAL(10,2), FLOAT, DOUBLE
VARCHAR(255), CHAR(50)
TEXT, LONGTEXT
DATETIME, DATE, TIME
BOOLEAN
JSON
ENUM('option1', 'option2')
```

---

## How Migrations Are Generated

### CREATE TABLE (New Table)
```json
{
  "table_name": "users",
  "columns": [
    {"name": "id", "type": "INT", "primary_key": true, "auto_increment": true},
    {"name": "username", "type": "VARCHAR(255)", "unique": true}
  ]
}
```

**Generates**:
```sql
CREATE TABLE IF NOT EXISTS users (
  id INT PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(255) UNIQUE
);
```

### ADD COLUMN
```json
// Add to columns array
{"name": "email", "type": "VARCHAR(255)", "unique": true}
```

**Generates**:
```sql
ALTER TABLE users ADD COLUMN email VARCHAR(255) UNIQUE;
```

### MODIFY COLUMN (Type Change)
```json
// Change existing column type
{"name": "age", "type": "INT"}  // was: SMALLINT
```

**Generates**:
```sql
ALTER TABLE users MODIFY COLUMN age INT;
```

### CREATE INDEX
```json
"indexes": [
  {"name": "idx_username", "columns": ["username"]},
  {"name": "idx_email_user", "columns": ["email", "username"]}
]
```

**Generates**:
```sql
CREATE INDEX idx_username ON users (username);
CREATE INDEX idx_email_user ON users (email, username);
```

---

## Deployment Workflow

### 1. Planning Phase
- Detects database apps in `apps.json`
- Prepares matrix for parallel builds

### 2. Build Phase (build-database job)
- Clones database-schema repo
- Reads `db-config.json` and `schema/*.json` files
- Uploads as artifacts

### 3. Deploy Phase
```
A. Setup Infrastructure
   ↓
B. Wait for Database Ready
   ↓
C. Sync Schema JSON Files
   ↓
D. Run Migrations
   ├── Connect to database
   ├── Parse JSON schemas
   ├── Compare with current schema
   ├── Generate ALTER TABLE queries
   └── Apply migrations (with rollback)
   ↓
E. Verify Database
   └── Check tables, databases, and structure
```

### 4. Output
```
🔄 Starting schema migrations...
   🔧 Migrating database: app_db
   📖 Parsed schema: users
   📖 Parsed schema: products
   
   ➕ CREATE TABLE: users
   ➕ ADD COLUMN: products.description
   🔄 MODIFY COLUMN: products.price
   📊 CREATE INDEX: idx_username
   
   📋 Generated 4 migration(s)
   
   [1/4] Create table: users
   [2/4] Add column products.description
   [3/4] Modify column products.price
   [4/4] Create index idx_username
   
   ✅ All migrations applied successfully!
   💾 Migration history saved
```

---

## Setting Up Your Database Schema Repository

### Quick Start

1. **Create new repo** (e.g., `database-schema`)

2. **Run init script** (or manually create structure):
   ```bash
   bash scripts/init-schema-repo.sh
   ```

3. **Create db-config.json**:
   ```json
   {
     "database_name": "app_db",
     "database_user": "app_user",
     "secret_name": "DB_APP_PASSWORD"
   }
   ```

4. **Create schema files** in `schema/` directory:
   - `users.json`
   - `products.json`
   - etc.

5. **Add GitHub secret** in repo settings:
   - Secret name: `DB_APP_PASSWORD`
   - Value: Your secure password

6. **Update apps.json** in main repo:
   ```json
   {
     "name": "database-schema",
     "type": "database",
     "repo_url": "ecappmakers/database-schema",
     "branch": "main",
     "build_cmd": null,
     "output_dir": "./"
   }
   ```

7. **Deploy**: Push to production branch and watch migrations happen!

---

## Multiple Databases

### Setup Multiple Database Apps

**apps.json**:
```json
{
  "apps": [
    {
      "name": "app-db",
      "type": "database",
      "repo_url": "ecappmakers/database-schema",
      "branch": "main",
      "build_cmd": null,
      "output_dir": "./"
    },
    {
      "name": "analytics-db",
      "type": "database",
      "repo_url": "ecappmakers/analytics-schema",
      "branch": "main",
      "build_cmd": null,
      "output_dir": "./"
    }
  ]
}
```

### Each Repo Has Its Own Config

**database-schema repo**:
```
db-config.json (database_name: "app_db", secret_name: "DB_APP_PASSWORD")
schema/users.json
schema/products.json
```

**analytics-schema repo**:
```
db-config.json (database_name: "analytics_db", secret_name: "DB_ANALYTICS_PASSWORD")
schema/events.json
schema/metrics.json
```

### Add Secrets for Each

- `DB_APP_PASSWORD` = password for app_db
- `DB_ANALYTICS_PASSWORD` = password for analytics_db

---

## Safety Features

### ✅ Dry-Run Mode
```bash
python3 schema_migrator.py --host localhost --user root --password pass --database app_db --schema-dir ./schema --dry-run
```

Shows migrations without applying them.

### ✅ Rollback Support
Each migration is tracked in `migration_history.json` for auditing and recovery.

### ✅ Transaction Safety
Migrations run within database transactions and roll back on failure.

### ✅ Idempotent Migrations
Safe to run multiple times (CREATE IF NOT EXISTS, etc.)

---

## Command Reference

### Run Migrations Manually

```bash
python3 /opt/ecapps-hosting/.github/scripts/schema_migrator.py \
  --host localhost \
  --user root \
  --password your_password \
  --database app_db \
  --schema-dir /opt/ecapps-hosting/data/schemas/app_db \
  --dry-run
```

### Check Migration History

```bash
cat /opt/ecapps-hosting/migration_history.json
```

### Inspect Current Database Schema

```bash
docker exec main_db mysql -u root -p$DB_PASS app_db -e "DESCRIBE users;"
```

---

## Troubleshooting

### Migration Failed - How to Recover

1. **Check logs**: Pipeline shows detailed error messages
2. **Review history**: Check `migration_history.json`
3. **Fix schema**: Correct the JSON definition
4. **Re-run**: Push again to retry

### Can't Modify Column (Data Incompatibility)

Add `nullable: true` first, then migrate data manually if needed:
```json
{"name": "phone", "type": "INT", "nullable": true}
```

### Foreign Keys Not Supported Yet

Current version handles basic schema. For foreign keys, add them manually after initial setup.

---

## What's Next

Future enhancements could include:
- Foreign key definitions
- Stored procedures & views
- Partition management
- Automatic backup before migrations
- Rollback UI
- Schema versioning & tags

---

## Summary

You now have a **production-grade schema migration system** that:
1. ✅ Replaces SQL with JSON
2. ✅ Compares automatically
3. ✅ Generates migrations safely
4. ✅ Tracks history
5. ✅ Supports multiple databases
6. ✅ Integrates with your CI/CD pipeline

The migration script (`schema_migrator.py`) is reusable and can be run standalone for local testing or production fixes. 🚀
