# Troubleshooting Guide - Schema Migration System

## Common Issues & Solutions

---

## 🔴 Pipeline Issues

### Issue: "Schema file not found in repo"

**Error Message**:
```
❌ Error: db-config.json not found in repo!
```

**Causes**:
- Missing `db-config.json` in root
- Missing `schema/` directory

**Solutions**:
1. Ensure directory structure:
   ```
   database-schema/
   ├── db-config.json
   ├── schema/
   │   └── users.json
   └── README.md
   ```

2. Verify files exist:
   ```bash
   ls -la db-config.json
   ls -la schema/
   ```

3. Check file permissions:
   ```bash
   chmod 644 db-config.json
   chmod 644 schema/*.json
   ```

---

### Issue: "Invalid JSON in schema files"

**Error Message**:
```
❌ Invalid JSON in schema/users.json: ...
```

**Causes**:
- Syntax error in JSON
- Missing comma between properties
- Trailing comma in arrays

**Solutions**:
1. Validate JSON:
   ```bash
   python3 -m json.tool schema/users.json
   ```

2. Use online validator: https://jsonlint.com/

3. Common mistakes:
   ```json
   // ❌ Missing comma
   {
     "name": "id",
     "type": "INT"  // ← needs comma here
     "primary_key": true
   }

   // ✅ Correct
   {
     "name": "id",
     "type": "INT",
     "primary_key": true
   }
   ```

---

### Issue: "No schema files found to migrate"

**Error Message**:
```
ℹ️ No schema files found to migrate
```

**Causes**:
- `schema/` directory is empty
- JSON files not copied properly
- Wrong path

**Solutions**:
1. Create sample schema:
   ```bash
   mkdir -p schema
   cat > schema/users.json << 'EOF'
   {
     "table_name": "users",
     "columns": [
       {"name": "id", "type": "INT", "primary_key": true, "auto_increment": true},
       {"name": "email", "type": "VARCHAR(255)"}
     ]
   }
   EOF
   ```

2. Verify artifacts:
   - Check pipeline logs for artifact upload
   - Look for "db-schema-*" artifacts in Actions

---

## 🔴 Database Connection Issues

### Issue: "Can't connect to database"

**Error Message**:
```
❌ Connection failed: No connection could be made...
```

**Causes**:
- Database not running
- Wrong credentials
- Network issue
- Port not accessible

**Solutions**:
1. Check database status:
   ```bash
   docker ps | grep main_db
   ```

2. Verify credentials:
   ```bash
   docker exec main_db mysqladmin -u root -p$DB_PASS ping
   ```

3. Check network:
   ```bash
   docker network ls
   docker network inspect hosting_net
   ```

4. Wait longer for DB startup:
   ```bash
   sleep 30 && docker exec main_db mysqladmin ping
   ```

---

### Issue: "Access Denied for database user"

**Error Message**:
```
❌ Connection failed: Access denied for user 'app_user'@'localhost'
```

**Causes**:
- User not created yet (first run)
- Wrong password
- User doesn't exist

**Solutions**:
1. Create user manually:
   ```bash
   docker exec main_db mysql -u root -p$DB_PASS -e \
     "CREATE USER 'app_user'@'%' IDENTIFIED BY 'password'; \
      GRANT ALL ON app_db.* TO 'app_user'@'%';"
   ```

2. Verify user exists:
   ```bash
   docker exec main_db mysql -u root -p$DB_PASS -e \
     "SELECT User, Host FROM mysql.user;"
   ```

3. Check password:
   - Ensure `DB_APP_PASSWORD` secret is set in GitHub
   - Verify it doesn't contain special chars that need escaping

---

## 🔴 Schema Comparison Issues

### Issue: "Could not fetch structure for table"

**Error Message**:
```
⚠️ Could not fetch structure for users: ...
```

**Causes**:
- Table doesn't exist yet (normal on first run)
- User lacks permissions
- Database doesn't exist

**Solutions**:
1. Create database:
   ```bash
   docker exec main_db mysql -u root -p$DB_PASS -e \
     "CREATE DATABASE IF NOT EXISTS app_db;"
   ```

2. Grant permissions:
   ```bash
   docker exec main_db mysql -u root -p$DB_PASS -e \
     "GRANT ALL ON app_db.* TO 'app_user'@'%';"
   ```

3. Check database exists:
   ```bash
   docker exec main_db mysql -u root -p$DB_PASS -e \
     "SHOW DATABASES;"
   ```

---

## 🔴 Migration Execution Issues

### Issue: "Migration failed - syntax error"

**Error Message**:
```
❌ Migration failed: You have an error in your SQL syntax...
```

**Causes**:
- Unsupported column type
- Invalid constraint
- Conflicting migration

**Solutions**:
1. Check data type:
   ```json
   // ❌ Invalid
   {"name": "id", "type": "BIGINTEGER"}

   // ✅ Valid
   {"name": "id", "type": "BIGINT"}
   ```

2. Supported types:
   - INT, BIGINT, SMALLINT
   - DECIMAL(10,2), FLOAT, DOUBLE
   - VARCHAR(255), TEXT, LONGTEXT
   - DATETIME, DATE, BOOLEAN
   - JSON, ENUM

3. Check constraint syntax:
   ```json
   // ✅ Correct
   {"name": "email", "type": "VARCHAR(255)", "unique": true}

   // ✅ Also correct
   {"name": "status", "type": "ENUM('active','inactive')"}
   ```

---

### Issue: "Can't modify column - data incompatible"

**Error Message**:
```
❌ Migration failed: Incorrect DECIMAL value: '12345'
```

**Causes**:
- Type change incompatible with existing data
- DECIMAL size too small for current values
- String to number conversion

**Solutions**:
1. For numeric types - make field bigger:
   ```json
   // ❌ Not enough space
   {"name": "price", "type": "DECIMAL(8,2)"}

   // ✅ More space
   {"name": "price", "type": "DECIMAL(12,2)"}
   ```

2. For type conversions - use migration steps:
   ```json
   // Step 1: Make nullable
   {"name": "age", "type": "INT", "nullable": true}
   // Deploy, then in DB: UPDATE users SET age = CAST(age_string AS INT);
   // Step 2: Change type
   {"name": "age", "type": "INT"}
   ```

3. For string truncation:
   ```json
   // Check current data length first
   // Then expand:
   {"name": "code", "type": "VARCHAR(255)"}  // was VARCHAR(50)
   ```

---

## 🔴 Permission Issues

### Issue: "Permission denied - can't write schema files"

**Error Message**:
```
❌ Cannot write to /opt/ecapps-hosting/data/schemas/
```

**Causes**:
- Directory ownership issue
- Disk full
- User doesn't have permissions

**Solutions**:
1. Check directory:
   ```bash
   ls -la /opt/ecapps-hosting/data/
   ```

2. Fix permissions:
   ```bash
   sudo chown docker:docker /opt/ecapps-hosting/data
   sudo chmod 755 /opt/ecapps-hosting/data
   ```

3. Check disk space:
   ```bash
   df -h /opt/ecapps-hosting
   ```

---

## 🔴 Data Loss Warnings

### Issue: Dropping Columns

**Warning**:
```
⚠️ Removing column from schema will DROP the column!
```

**Be Careful**:
- Deleting a column from JSON = `ALTER TABLE DROP COLUMN`
- Data is deleted permanently
- No undo!

**Safe Approach**:
1. First, add soft-delete flag:
   ```json
   {"name": "is_deleted", "type": "BOOLEAN", "default": false}
   ```

2. Update queries to check flag:
   ```sql
   SELECT * FROM users WHERE is_deleted = false;
   ```

3. Safely delete old data:
   ```sql
   DELETE FROM users WHERE is_deleted = true AND updated_at < DATE_SUB(NOW(), INTERVAL 30 DAY);
   ```

4. Only then remove column from schema

---

## 🔴 Index Issues

### Issue: "Duplicate index error"

**Error Message**:
```
❌ Can't create index 'idx_email': Duplicate key name
```

**Causes**:
- Index already exists with different name
- Multiple identical indexes

**Solutions**:
1. Check existing indexes:
   ```bash
   docker exec main_db mysql -u root -p$DB_PASS app_db -e \
     "SHOW INDEXES FROM users;"
   ```

2. Use unique names:
   ```json
   "indexes": [
     {"name": "idx_username_unique", "columns": ["username"]},
     {"name": "idx_email_search", "columns": ["email"]}
   ]
   ```

3. Don't duplicate:
   ```json
   // ❌ Wrong
   "indexes": [
     {"columns": ["id"]},
     {"columns": ["id"]}
   ]

   // ✅ Right
   "indexes": [
     {"name": "idx_primary", "columns": ["id"]}
   ]
   ```

---

## 🟡 Performance Issues

### Issue: Migration takes too long

**Symptoms**:
```
⏳ Still waiting... (45 seconds left)
```

**Causes**:
- Large table with millions of rows
- Slow disk
- Limited memory

**Solutions**:
1. Check migration complexity:
   - Adding nullable column = fast ✅
   - Changing non-nullable column = slow ⚠️
   - Adding index on large table = very slow ⚠️

2. Run migrations at off-hours:
   - Don't deploy during peak traffic
   - Use `workflow_dispatch` for manual timing

3. Increase timeout (if needed):
   ```bash
   # In migration script or manually increase the timeout
   TIMEOUT=300  # 5 minutes instead of 60 seconds
   ```

---

## 🟡 Debugging Tips

### View Migration History

```bash
# On VPS:
cat /opt/ecapps-hosting/migration_history.json | jq .

# Shows:
# - Timestamp of migration
# - Total migrations applied
# - Details of each change
```

### Test Migration Locally

```bash
# Run dry-run to see what would happen
python3 schema_migrator.py \
  --host localhost \
  --user root \
  --password pass \
  --database app_db \
  --schema-dir ./schema \
  --dry-run
```

### Check Database State

```bash
# List all tables
docker exec main_db mysql -u root -p$DB_PASS app_db -e "SHOW TABLES;"

# Describe a table
docker exec main_db mysql -u root -p$DB_PASS app_db -e "DESCRIBE users;"

# Check indexes
docker exec main_db mysql -u root -p$DB_PASS app_db -e "SHOW INDEXES FROM users;"
```

### View Pipeline Logs

1. Go to GitHub Actions
2. Click on your workflow run
3. Expand "🔄 Apply Schema Migrations" step
4. Look for errors in output

### Enable Verbose Logging

Modify migration script to add more debug output:
```python
print(f"🔍 Comparing table: {table_name}")
print(f"   Current columns: {list(current_cols.keys())}")
print(f"   Schema columns: {list(schema_cols.keys())}")
```

---

## Quick Recovery Checklist

### If Deployment Failed:

1. ✅ Check pipeline logs for error message
2. ✅ Review migration_history.json on VPS
3. ✅ Identify problematic schema change
4. ✅ Fix the JSON schema file
5. ✅ Test locally with `--dry-run`
6. ✅ Commit and re-deploy
7. ✅ Monitor next deployment carefully

### If Database is Broken:

1. ✅ SSH to VPS
2. ✅ Backup database:
   ```bash
   docker exec main_db mysqldump -u root -p$DB_PASS --all-databases > backup.sql
   ```
3. ✅ Stop containers:
   ```bash
   cd /opt/ecapps-hosting
   docker compose down
   ```
4. ✅ Delete MySQL volume:
   ```bash
   docker volume rm ecapps-hosting_mysql-data  # Use actual volume name
   ```
5. ✅ Re-deploy with corrected schema

---

## Getting Help

1. **Check Documentation**:
   - `SCHEMA_MIGRATION_GUIDE.md`
   - `IMPLEMENTATION_SUMMARY.md`
   - `JSON_SCHEMA_REFERENCE.md`

2. **Review Examples**:
   - `example-schema-repo/`
   - Migration history in `migration_history.json`

3. **Test Locally**:
   - Run schema_migrator.py with `--dry-run`
   - Check output before deploying

4. **Manual Testing**:
   ```bash
   # SSH to VPS and test:
   docker exec main_db mysql -u root -p$DB_PASS
   mysql> DESCRIBE users;
   ```

---

Most issues are **JSON syntax** or **permission** related. Double-check both first! ✅
