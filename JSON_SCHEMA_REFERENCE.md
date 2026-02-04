# Quick Reference - JSON Schema Format

## Minimal Table Definition

```json
{
  "table_name": "users",
  "columns": [
    {"name": "id", "type": "INT", "primary_key": true, "auto_increment": true},
    {"name": "name", "type": "VARCHAR(255)"}
  ]
}
```

## Full Table Definition

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
      "name": "password_hash",
      "type": "VARCHAR(255)",
      "nullable": false
    },
    {
      "name": "created_at",
      "type": "DATETIME",
      "nullable": false,
      "default": "CURRENT_TIMESTAMP"
    },
    {
      "name": "is_active",
      "type": "BOOLEAN",
      "nullable": false,
      "default": true
    }
  ],
  "indexes": [
    {"name": "idx_username", "columns": ["username"]},
    {"name": "idx_email", "columns": ["email"]},
    {"name": "idx_created", "columns": ["created_at"]}
  ]
}
```

---

## Column Type Cheat Sheet

### Numbers
```
INT              -2 billion to +2 billion
BIGINT           -9 quintillion to +9 quintillion
SMALLINT         -32k to +32k
DECIMAL(10,2)    Exact: 10 total digits, 2 after decimal
FLOAT            Approximate: 4 bytes
DOUBLE           Approximate: 8 bytes
```

### Text
```
VARCHAR(255)     Variable length (up to 255 chars)
CHAR(50)         Fixed length (50 chars)
TEXT             Up to 64KB text
LONGTEXT         Up to 4GB text
```

### Dates & Time
```
DATETIME         2024-01-15 14:30:45
DATE             2024-01-15
TIME             14:30:45
TIMESTAMP        Auto-updates on change
```

### Other
```
BOOLEAN          true/false
JSON             {"key": "value"}
ENUM('a','b')    One of specified values
UUID             Unique identifier
```

---

## Column Properties

| Property | Values | Default | Use |
|----------|--------|---------|-----|
| `name` | string | - | Column name |
| `type` | string | - | Data type |
| `primary_key` | true/false | false | Primary key |
| `auto_increment` | true/false | false | Auto ID |
| `nullable` | true/false | true | Allow NULL |
| `unique` | true/false | false | Must be unique |
| `default` | string/number | - | Default value |

---

## Common Defaults

```json
// Auto-increment timestamp
{"name": "created_at", "type": "DATETIME", "default": "CURRENT_TIMESTAMP"}

// Optional field
{"name": "phone", "type": "VARCHAR(20)", "nullable": true}

// Default false
{"name": "is_active", "type": "BOOLEAN", "default": false}

// Default 0
{"name": "count", "type": "INT", "default": 0}

// No default, required
{"name": "email", "type": "VARCHAR(255)", "nullable": false}
```

---

## Table Structure Examples

### Users Table
```json
{
  "table_name": "users",
  "columns": [
    {"name": "id", "type": "INT", "primary_key": true, "auto_increment": true},
    {"name": "username", "type": "VARCHAR(100)", "unique": true},
    {"name": "email", "type": "VARCHAR(255)", "unique": true},
    {"name": "password_hash", "type": "VARCHAR(255)"},
    {"name": "profile_image", "type": "VARCHAR(255)", "nullable": true},
    {"name": "created_at", "type": "DATETIME", "default": "CURRENT_TIMESTAMP"},
    {"name": "updated_at", "type": "DATETIME", "nullable": true}
  ],
  "indexes": [
    {"name": "idx_username", "columns": ["username"]},
    {"name": "idx_email", "columns": ["email"]}
  ]
}
```

### Products Table
```json
{
  "table_name": "products",
  "columns": [
    {"name": "id", "type": "INT", "primary_key": true, "auto_increment": true},
    {"name": "sku", "type": "VARCHAR(50)", "unique": true},
    {"name": "name", "type": "VARCHAR(255)"},
    {"name": "description", "type": "TEXT", "nullable": true},
    {"name": "price", "type": "DECIMAL(10,2)"},
    {"name": "cost", "type": "DECIMAL(10,2)"},
    {"name": "stock", "type": "INT", "default": 0},
    {"name": "is_available", "type": "BOOLEAN", "default": true},
    {"name": "created_at", "type": "DATETIME", "default": "CURRENT_TIMESTAMP"}
  ],
  "indexes": [
    {"name": "idx_sku", "columns": ["sku"]},
    {"name": "idx_name", "columns": ["name"]},
    {"name": "idx_price", "columns": ["price"]}
  ]
}
```

### Orders Table
```json
{
  "table_name": "orders",
  "columns": [
    {"name": "id", "type": "INT", "primary_key": true, "auto_increment": true},
    {"name": "order_number", "type": "VARCHAR(50)", "unique": true},
    {"name": "user_id", "type": "INT"},
    {"name": "total_amount", "type": "DECIMAL(10,2)"},
    {"name": "tax_amount", "type": "DECIMAL(10,2)", "default": 0},
    {"name": "shipping_amount", "type": "DECIMAL(10,2)", "default": 0},
    {"name": "status", "type": "ENUM('pending','processing','shipped','delivered','cancelled')", "default": "pending"},
    {"name": "notes", "type": "TEXT", "nullable": true},
    {"name": "created_at", "type": "DATETIME", "default": "CURRENT_TIMESTAMP"},
    {"name": "updated_at", "type": "DATETIME", "nullable": true}
  ],
  "indexes": [
    {"name": "idx_user_id", "columns": ["user_id"]},
    {"name": "idx_order_number", "columns": ["order_number"]},
    {"name": "idx_status", "columns": ["status"]},
    {"name": "idx_created", "columns": ["created_at"]}
  ]
}
```

---

## Common Patterns

### Email Field
```json
{
  "name": "email",
  "type": "VARCHAR(255)",
  "unique": true,
  "nullable": false
}
```

### Status Field
```json
{
  "name": "status",
  "type": "ENUM('active','inactive','pending')",
  "default": "pending"
}
```

### Soft Delete
```json
{
  "name": "deleted_at",
  "type": "DATETIME",
  "nullable": true
}
```

### Timestamps
```json
{
  "name": "created_at",
  "type": "DATETIME",
  "default": "CURRENT_TIMESTAMP"
},
{
  "name": "updated_at",
  "type": "DATETIME",
  "nullable": true
}
```

### JSON Data
```json
{
  "name": "metadata",
  "type": "JSON",
  "nullable": true
}
```

---

## Multi-Column Index

```json
"indexes": [
  {
    "name": "idx_user_email",
    "columns": ["user_id", "email"]
  }
]
```

This is faster for queries like:
```sql
WHERE user_id = 5 AND email = 'test@example.com'
```

---

## db-config.json Template

```json
{
  "database_name": "app_db",
  "database_user": "app_user",
  "secret_name": "DB_APP_PASSWORD",
  "description": "Main application database"
}
```

---

## Adding New Table

1. Create `schema/new_table.json`
2. Copy template and customize
3. Commit & push
4. ✅ Done! Pipeline creates it

## Modifying Table

1. Edit `schema/table_name.json`
2. Add/modify/remove columns
3. Commit & push
4. ✅ Done! Pipeline applies changes

---

## Tips & Tricks

### Use Meaningful Names
```json
// ✅ Good
{"name": "user_id", "type": "INT"}
{"name": "created_at", "type": "DATETIME"}

// ❌ Avoid
{"name": "uid", "type": "INT"}
{"name": "c_date", "type": "DATETIME"}
```

### Index Wisely
```json
// ✅ Index columns used in WHERE/JOIN
"indexes": [
  {"name": "idx_user_id", "columns": ["user_id"]},
  {"name": "idx_status", "columns": ["status"]}
]
```

### Use Defaults
```json
// ✅ Explicit defaults
{"name": "is_active", "type": "BOOLEAN", "default": true}
{"name": "created_at", "type": "DATETIME", "default": "CURRENT_TIMESTAMP"}

// ❌ Let developers handle
{"name": "is_active", "type": "BOOLEAN"}
```

---

## Validation Checklist

- ✅ Each table has unique `table_name`
- ✅ Each column has `name` and `type`
- ✅ Primary key defined (usually `id INT AUTO_INCREMENT`)
- ✅ Important fields are `nullable: false`
- ✅ Unique fields marked `unique: true`
- ✅ Indexes for frequently queried columns
- ✅ Valid JSON (use jsonlint.com to verify)

---

**Ready to use!** Copy any pattern above and customize for your tables. 🚀
