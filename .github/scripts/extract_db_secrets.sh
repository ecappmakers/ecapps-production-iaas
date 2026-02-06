#!/bin/bash
# Extract database secret names from db-config.json files
# Outputs environment variable names that need to be passed

SCHEMAS_DIR="${1:-.}"

if [ ! -d "$SCHEMAS_DIR" ]; then
    echo "❌ Schemas directory not found: $SCHEMAS_DIR"
    exit 1
fi

echo "🔍 Extracting database secret names..."

SECRETS=()

# Iterate through each database directory
for db_dir in "$SCHEMAS_DIR"/*/; do
    [ -d "$db_dir" ] || continue
    
    config_file="$db_dir/db-config.json"
    
    if [ -f "$config_file" ]; then
        # Extract secret_name from db-config.json
        secret_name=$(jq -r '.secret_name // empty' "$config_file" 2>/dev/null)
        
        if [ -n "$secret_name" ]; then
            echo "   Found: $secret_name"
            SECRETS+=("$secret_name")
        fi
    fi
done

# Output comma-separated list
if [ ${#SECRETS[@]} -gt 0 ]; then
    printf '%s\n' "${SECRETS[@]}" | tr '\n' ',' | sed 's/,$//'
    echo ""
else
    echo "⚠️ No database secrets found"
    exit 1
fi
