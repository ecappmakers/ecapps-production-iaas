#!/bin/bash

# Quick Template Generator for Database Schema Repository
# Run this in a new database schema repo to generate example structure

set -e

echo "📝 Creating database schema repository structure..."

# Create directories
mkdir -p schema

# Create db-config.json
cat > db-config.json << 'EOF'
{
  "database_name": "app_db",
  "database_user": "app_user",
  "secret_name": "DB_APP_PASSWORD",
  "description": "Main application database"
}
EOF

echo "✅ Created db-config.json"

# Create example users table
cat > schema/users.json << 'EOF'
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
      "name": "updated_at",
      "type": "DATETIME",
      "nullable": true
    },
    {
      "name": "is_active",
      "type": "BOOLEAN",
      "nullable": false,
      "default": true
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
    },
    {
      "name": "idx_created_at",
      "columns": ["created_at"]
    }
  ]
}
EOF

echo "✅ Created schema/users.json"

# Create example products table
cat > schema/products.json << 'EOF'
{
  "table_name": "products",
  "columns": [
    {
      "name": "id",
      "type": "INT",
      "primary_key": true,
      "auto_increment": true,
      "nullable": false
    },
    {
      "name": "name",
      "type": "VARCHAR(255)",
      "nullable": false
    },
    {
      "name": "description",
      "type": "TEXT",
      "nullable": true
    },
    {
      "name": "price",
      "type": "DECIMAL(10,2)",
      "nullable": false
    },
    {
      "name": "stock",
      "type": "INT",
      "nullable": false,
      "default": 0
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
      "name": "idx_name",
      "columns": ["name"]
    },
    {
      "name": "idx_price",
      "columns": ["price"]
    }
  ]
}
EOF

echo "✅ Created schema/products.json"

# Create README
cat > README.md << 'EOF'
# Application Database Schema

This repository contains JSON-based database schema definitions.

## Structure

- `db-config.json` - Database configuration
- `schema/` - Table definitions (each .json file = one table)

## To Add a New Table

1. Create a new `.json` file in `schema/`
2. Define table structure (see examples: users.json, products.json)
3. Commit and push
4. Pipeline will create table on next deployment

## To Modify a Table

1. Edit the table's `.json` file
2. Add/modify/remove columns
3. Commit and push
4. Pipeline generates and applies migrations

## Column Types

- INT, BIGINT, DECIMAL(10,2)
- VARCHAR(255), TEXT
- DATETIME, DATE, BOOLEAN
- JSON

See main repository documentation for details.
EOF

echo "✅ Created README.md"

echo ""
echo "🎉 Repository structure created successfully!"
echo ""
echo "Next steps:"
echo "1. Edit db-config.json with your database name and user"
echo "2. Customize schema/*.json files for your tables"
echo "3. Add DB_APP_PASSWORD secret to GitHub repo settings"
echo "4. Commit and push to trigger deployment"
echo ""
