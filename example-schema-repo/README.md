# Database Schema Repository

This repository contains JSON-based database schemas that are automatically compared and migrated during deployment.

## Structure

```
.
├── db-config.json          # Database configuration
├── schema/                 # JSON schema files for each table
│   ├── users.json
│   ├── products.json
│   └── orders.json
└── README.md
```

## db-config.json

Defines database metadata:

```json
{
  "database_name": "app_db",
  "database_user": "app_user",
  "secret_name": "DB_APP_PASSWORD",
  "description": "Main application database"
}
```

- `database_name`: Name of the database (will be created if not exists)
- `database_user`: User that will be created for this database
- `secret_name`: GitHub secret name containing the user password
- `description`: Optional description

## Schema Files

Each `.json` file in `schema/` directory represents one table with full column definitions.

### Example Table Schema (users.json)

```json
{
  "table_name": "users",
  "columns": [
    {
      "name": "id",
      "type": "INT",
      "primary_key": true,
      "auto_increment": true,
      "nullable": false
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
    },
    {
      "name": "created_at",
      "type": "DATETIME",
      "nullable": false,
      "default": "CURRENT_TIMESTAMP"
    }
  ],
  "indexes": [
    {
      "name": "idx_username",
      "columns": ["username"]
    },
    {
      "name": "idx_email",
      "columns": ["email"]
    }
  ]
}
```

### Column Properties

- `name`: Column name
- `type`: MySQL data type (INT, VARCHAR(255), TEXT, DATETIME, etc.)
- `primary_key`: (optional) Set to true for primary key
- `auto_increment`: (optional) For auto-incrementing IDs
- `nullable`: (optional, default: true) Whether NULL is allowed
- `unique`: (optional) Whether column must be unique
- `default`: (optional) Default value or function (e.g., "CURRENT_TIMESTAMP")

### Indexes

Define indexes to optimize queries:

```json
"indexes": [
  {
    "name": "idx_username",
    "columns": ["username"],
    "type": "NORMAL"
  },
  {
    "name": "idx_user_email",
    "columns": ["username", "email"]
  }
]
```

## How Migrations Work

1. **Detection**: Pipeline detects schema changes
2. **Comparison**: Current database schema is compared with JSON definitions
3. **Generation**: ALTER TABLE queries are generated automatically
4. **Safety**: Dry-run shows changes before applying
5. **Application**: Migrations are applied with rollback support
6. **Tracking**: Migration history is saved for auditing

### What Gets Migrated

✅ Create new tables  
✅ Add missing columns  
✅ Modify column types  
✅ Add/remove indexes  
✅ Update constraints (nullable, unique, etc.)  

## Adding a New Table

1. Create a new JSON file in `schema/` directory
2. Define all columns and indexes
3. Commit and push
4. Pipeline will automatically create the table on next deployment

## Modifying Existing Table

1. Edit the JSON file
2. Add/modify/remove columns
3. Commit and push
4. Pipeline generates and applies ALTER TABLE statements

## Example: Add New Column

**Before** (users.json):
```json
{
  "table_name": "users",
  "columns": [
    { "name": "id", "type": "INT", "primary_key": true, "auto_increment": true },
    { "name": "username", "type": "VARCHAR(255)" }
  ]
}
```

**After**:
```json
{
  "table_name": "users",
  "columns": [
    { "name": "id", "type": "INT", "primary_key": true, "auto_increment": true },
    { "name": "username", "type": "VARCHAR(255)" },
    { "name": "email", "type": "VARCHAR(255)", "unique": true }
  ]
}
```

Pipeline will generate and apply:
```sql
ALTER TABLE users ADD COLUMN email VARCHAR(255) UNIQUE;
```

## Migration History

After each deployment, a `migration_history.json` is created containing:
- Timestamp
- Total migrations applied
- Details of each migration

This can be used for auditing and rollback if needed.

## Notes

- Migrations are idempotent (safe to run multiple times)
- Column deletions require manual approval for data safety
- Type changes are supported but may require data casting
- All migrations are logged and timestamped
