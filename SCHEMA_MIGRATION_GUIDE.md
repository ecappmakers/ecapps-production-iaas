# Schema Migration System - Setup Guide

## What You Get

✅ **JSON-based schema definitions** - No SQL coding required  
✅ **Automatic schema comparison** - Detects what changed  
✅ **Auto-generated migrations** - ALTER TABLE queries created automatically  
✅ **Safe deployments** - Dry-run shows changes before applying  
✅ **Migration history** - Track all changes with timestamps  
✅ **Multiple databases** - Each database has its own user & config  

---

## 1. Setup Your Database Schema Repository

### Structure

```
database-schema/
├── db-config.json
├── schema/
│   ├── users.json
│   ├── products.json
│   └── orders.json
└── README.md
```

### Create db-config.json

```json
{
  "database_name": "app_db",
  "database_user": "app_user",
  "secret_name": "DB_APP_PASSWORD",
  "description": "Main application database"
}
```

### Create Table Schemas (in schema/ folder)

**schema/users.json:**
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
      "nullable": false,
      "unique": true
    },
    {
      "name": "email",
      "type": "VARCHAR(255)",
      "nullable": false,
      "unique": true
    }
  ],
  "indexes": [
    { "name": "idx_username", "columns": ["username"] },
    { "name": "idx_email", "columns": ["email"] }
  ]
}
```

---

## 2. Add GitHub Secrets

For each database, add a secret with the password:

- `DB_APP_PASSWORD` = `your_secure_password_here`

The script will use this secret to create the database user during migration.

---

## 3. Update apps.json

```json
{
  "name": "database-schema",
  "type": "database",
  "repo_url": "ecappmakers/database-schema",
  "branch": "main",
  "build_cmd": null,
  "output_dir": "./",
  "target_file": "schema.sql"  // ← This field is ignored now (use JSON instead)
}
```

The pipeline will automatically:
1. Clone your database schema repo
2. Read all JSON files from `schema/` directory
3. Compare with existing database
4. Generate and apply migrations

---

## 4. How to Modify Schema

### Add a New Column

Edit **schema/users.json**:
```json
{
  "table_name": "users",
  "columns": [
    // ... existing columns ...
    {
      "name": "phone",
      "type": "VARCHAR(20)",
      "nullable": true,
      "unique": true
    }
  ]
}
```

**Result**: Pipeline generates and applies:
```sql
ALTER TABLE users ADD COLUMN phone VARCHAR(20) UNIQUE;
```

### Change Column Type

Edit **schema/products.json**:
```json
{
  "table_name": "products",
  "columns": [
    {
      "name": "price",
      "type": "DECIMAL(12,2)"  // Changed from DECIMAL(10,2)
    }
  ]
}
```

**Result**: Pipeline applies:
```sql
ALTER TABLE products MODIFY COLUMN price DECIMAL(12,2);
```

### Create New Table

1. Create **schema/orders.json**:
```json
{
  "table_name": "orders",
  "columns": [
    {
      "name": "id",
      "type": "INT",
      "primary_key": true,
      "auto_increment": true
    },
    {
      "name": "user_id",
      "type": "INT",
      "nullable": false
    },
    {
      "name": "total_amount",
      "type": "DECIMAL(10,2)",
      "nullable": false
    }
  ]
}
```

**Result**: Pipeline creates the table on next deployment.

### Add Index

Edit any table's JSON:
```json
{
  "table_name": "orders",
  "columns": [ ... ],
  "indexes": [
    { "name": "idx_user_id", "columns": ["user_id"] },
    { "name": "idx_amount", "columns": ["total_amount"] }
  ]
}
```

---

## 5. Multiple Databases Setup

### Create Multiple Database Entries in apps.json

```json
{
  "apps": [
    {
      "name": "app-database",
      "type": "database",
      "repo_url": "ecappmakers/database-schema",
      "branch": "main",
      "build_cmd": null,
      "output_dir": "./"
    },
    {
      "name": "analytics-database",
      "type": "database",
      "repo_url": "ecappmakers/analytics-schema",
      "branch": "main",
      "build_cmd": null,
      "output_dir": "./"
    }
  ]
}
```

### Create Separate Repos

**database-schema repo:**
```
db-config.json (database_name: "app_db")
schema/users.json
schema/products.json
```

**analytics-schema repo:**
```
db-config.json (database_name: "analytics_db")
schema/events.json
schema/metrics.json
```

### Add Secrets for Each Database

- `DB_APP_PASSWORD` = password for app_user
- `DB_ANALYTICS_PASSWORD` = password for analytics_user

---

## 6. Deployment Flow

When you push to production branch:

1. ✅ **Plan** - Detects all database apps
2. ✅ **Build** - Clones repos, extracts JSON schemas
3. ✅ **Compare** - Compares with current database
4. ✅ **Generate** - Creates ALTER TABLE queries
5. ✅ **Apply** - Runs migrations (with rollback support)
6. ✅ **Track** - Saves migration history
7. ✅ **Verify** - Confirms database is operational

---

## 7. Column Type Reference

| Type | Example | Use Case |
|------|---------|----------|
| INT | `"INT"` | Integers (age, count) |
| BIGINT | `"BIGINT"` | Large integers (IDs) |
| DECIMAL | `"DECIMAL(10,2)"` | Money (price: $1234.56) |
| VARCHAR | `"VARCHAR(255)"` | Variable-length text |
| TEXT | `"TEXT"` | Long text (description) |
| DATETIME | `"DATETIME"` | Date & time |
| DATE | `"DATE"` | Date only |
| BOOLEAN | `"BOOLEAN"` | True/False |
| JSON | `"JSON"` | JSON data |

---

## 8. Common Patterns

### User Table
```json
{
  "table_name": "users",
  "columns": [
    { "name": "id", "type": "INT", "primary_key": true, "auto_increment": true },
    { "name": "username", "type": "VARCHAR(255)", "unique": true },
    { "name": "email", "type": "VARCHAR(255)", "unique": true },
    { "name": "password_hash", "type": "VARCHAR(255)" },
    { "name": "created_at", "type": "DATETIME", "default": "CURRENT_TIMESTAMP" }
  ]
}
```

### Product Table
```json
{
  "table_name": "products",
  "columns": [
    { "name": "id", "type": "INT", "primary_key": true, "auto_increment": true },
    { "name": "name", "type": "VARCHAR(255)" },
    { "name": "price", "type": "DECIMAL(10,2)" },
    { "name": "stock", "type": "INT", "default": 0 },
    { "name": "created_at", "type": "DATETIME", "default": "CURRENT_TIMESTAMP" }
  ]
}
```

---

## 9. What Happens on Deployment

**Console Output Example:**
```
🔍 Comparing schemas...

📖 Parsed schema: users
📖 Parsed schema: products

➕ CREATE TABLE: users
➕ ADD COLUMN: products.description
🔄 MODIFY COLUMN: products.price (DECIMAL(10,2) → DECIMAL(12,2))
📊 CREATE INDEX: idx_user_email on users

📋 Generated 4 migration(s)

[1/4] Create table: users
[2/4] Add column products.description
[3/4] Modify column products.price
[4/4] Create index idx_user_email

✅ All migrations applied successfully!
💾 Migration history saved
```

---

## 10. Troubleshooting

### Migration Fails - How to Recover

1. Check the migration history: `migration_history.json`
2. Review what changed
3. Fix the schema JSON
4. Commit and re-run deployment

### Can't Add Column (existing data issue)

Add `nullable: true` first, then modify later:
```json
{ "name": "new_column", "type": "VARCHAR(255)", "nullable": true }
```

### Type Conversion Issues

MySQL may need intermediate steps for type changes. You can manually execute migrations if needed.

---

## File Locations (on VPS)

```
/opt/ecapps-hosting/
├── .github/scripts/schema_migrator.py     ← Migration script
├── data/
│   ├── schemas/
│   │   ├── app_db/
│   │   │   ├── users.json
│   │   │   └── products.json
│   │   └── analytics_db/
│   │       └── events.json
│   └── mysql/                             ← Database files
├── migration_history.json                 ← Track changes
└── apps.json
```

Done! Your schema migration system is ready to use! 🚀
