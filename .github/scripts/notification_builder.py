#!/usr/bin/env python3
"""
Comprehensive Deployment Notification Builder
Generates rich notifications with deployment details
"""

import json
import os
import glob
import re
from datetime import datetime

def load_apps_json():
    """Load and parse apps.json"""
    try:
        with open('apps.json', 'r') as f:
            return json.load(f)
    except:
        return {'apps': []}

def parse_npm_log():
    """Extract NPM configuration results"""
    npm_data = {
        'created': [],
        'skipped': [],
        'failed': [],
        'status': '❌ No log found'
    }
    
    if not os.path.exists('logs/log-npm.txt'):
        return npm_data
    
    try:
        with open('logs/log-npm.txt', 'r') as f:
            content = f.read()
            
            # Parse created domains
            created = re.findall(r'✅ Created: (.+)', content)
            npm_data['created'] = created
            
            # Parse skipped domains
            skipped = re.findall(r'ℹ️.*Skipping (.+)', content)
            npm_data['skipped'] = skipped
            
            # Parse failed domains
            failed = re.findall(r'❌.*Failed (.+)', content)
            npm_data['failed'] = failed
            
            # Determine overall status
            if created or skipped:
                npm_data['status'] = '✅ Proxy Configuration Successful'
            elif failed:
                npm_data['status'] = '❌ Proxy Configuration Failed'
                
    except Exception as e:
        npm_data['status'] = f'⚠️ Could not parse NPM log: {e}'
    
    return npm_data

def parse_migration_log():
    """Extract database migration statistics"""
    migration_data = {
        'databases': {},
        'total_migrations': 0,
        'status': '⚠️ No migrations'
    }
    
    # Find migration logs
    migration_logs = glob.glob('logs/migration_*.log') + glob.glob('logs/*migration*.log')
    
    if not migration_logs:
        return migration_data
    
    try:
        for log_file in migration_logs:
            with open(log_file, 'r') as f:
                content = f.read()
                
                # Extract database name
                db_match = re.search(r'Migrating database: (\w+)', content)
                db_name = db_match.group(1) if db_match else 'unknown'
                
                # Count operations
                creates = len(re.findall(r'CREATE TABLE', content))
                adds = len(re.findall(r'ADD COLUMN', content))
                modifies = len(re.findall(r'MODIFY COLUMN', content))
                drops = len(re.findall(r'DROP COLUMN', content))
                fks = len(re.findall(r'FOREIGN KEY', content))
                indexes = len(re.findall(r'CREATE INDEX', content))
                
                migration_data['databases'][db_name] = {
                    'created_tables': creates,
                    'added_columns': adds,
                    'modified_columns': modifies,
                    'dropped_columns': drops,
                    'foreign_keys': fks,
                    'indexes': indexes
                }
                
                migration_data['total_migrations'] += (creates + adds + modifies + drops + fks + indexes)
        
        if migration_data['databases']:
            migration_data['status'] = '✅ Migrations Applied'
            
    except Exception as e:
        migration_data['status'] = f'⚠️ Could not parse migrations: {e}'
    
    return migration_data

def get_deployed_apps(config):
    """Extract deployed applications with their domains"""
    apps_info = {
        'static': [],
        'containers': [],
        'databases': []
    }
    
    for app in config.get('apps', []):
        app_type = app.get('type', '').lower()
        name = app.get('name', 'unknown')
        domain = app.get('domain')
        
        if 'static' in app_type or 'node' in app_type:
            apps_info['static'].append({
                'name': name,
                'domain': domain,
                'url': f"https://{domain}" if domain else None,
                'www_url': f"https://www.{domain}" if domain else None
            })
        elif 'container' in app_type or 'backend' in app_type:
            apps_info['containers'].append({
                'name': name,
                'domain': domain,
                'url': f"https://{domain}" if domain else None
            })
        elif 'database' in app_type:
            apps_info['databases'].append({
                'name': name
            })
    
    return apps_info

def build_telegram_message(deploy_result, proxy_result, apps_info, npm_data, migration_data):
    """Build rich Telegram message"""
    
    # Status emoji and title
    if deploy_result == 'success' and (proxy_result == 'success' or proxy_result == 'skipped'):
        emoji = '✅'
        title = 'Deployment Successful'
        status = 'success'
    else:
        emoji = '❌'
        title = 'Deployment Failed'
        status = 'failure'
    
    msg = f"{emoji} <b>{title}</b>\n"
    msg += f"<i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</i>\n\n"
    
    # Deployed Applications
    msg += "<b>📱 Applications Deployed:</b>\n"
    if apps_info['static']:
        for app in apps_info['static']:
            msg += f"⚡ {app['name']}\n"
            if app['url']:
                msg += f"   🔗 {app['url']}\n"
                msg += f"   🔗 {app['www_url']}\n"
    
    if apps_info['containers']:
        for app in apps_info['containers']:
            msg += f"🐳 {app['name']}\n"
            if app['url']:
                msg += f"   🔗 {app['url']}\n"
    
    if not apps_info['static'] and not apps_info['containers']:
        msg += "ℹ️ No applications deployed\n"
    
    # Nginx Proxy Manager
    msg += f"\n<b>🌐 Nginx Proxy Manager:</b>\n"
    msg += f"{npm_data['status']}\n"
    if npm_data['created']:
        msg += f"✅ Configured: {', '.join(npm_data['created'][:3])}"
        if len(npm_data['created']) > 3:
            msg += f" +{len(npm_data['created'])-3} more"
        msg += "\n"
    if npm_data['skipped']:
        msg += f"ℹ️ Already Configured: {len(npm_data['skipped'])}\n"
    if npm_data['failed']:
        msg += f"❌ Failed: {', '.join(npm_data['failed'])}\n"
    
    # Database Migrations
    msg += f"\n<b>🗄️ Database Migrations:</b>\n"
    msg += f"{migration_data['status']}\n"
    
    if migration_data['databases']:
        for db_name, stats in migration_data['databases'].items():
            msg += f"\n📊 <b>{db_name}:</b>\n"
            if stats['created_tables']:
                msg += f"  📦 Tables Created: {stats['created_tables']}\n"
            if stats['added_columns']:
                msg += f"  ➕ Columns Added: {stats['added_columns']}\n"
            if stats['modified_columns']:
                msg += f"  🔄 Columns Modified: {stats['modified_columns']}\n"
            if stats['dropped_columns']:
                msg += f"  ➖ Columns Dropped: {stats['dropped_columns']}\n"
            if stats['foreign_keys']:
                msg += f"  🔗 Foreign Keys: {stats['foreign_keys']}\n"
            if stats['indexes']:
                msg += f"  📇 Indexes: {stats['indexes']}\n"
    else:
        msg += "ℹ️ No migrations applied\n"
    
    # Summary
    msg += f"\n<b>📊 Summary:</b>\n"
    msg += f"Status: {status.upper()}\n"
    msg += f"Timestamp: {datetime.now().isoformat()}\n"
    
    return emoji, title, msg

def build_email_message(deploy_result, proxy_result, apps_info, npm_data, migration_data):
    """Build rich email message"""
    
    # Status
    if deploy_result == 'success' and (proxy_result == 'success' or proxy_result == 'skipped'):
        status = 'SUCCESS ✅'
        status_color = '#2ecc71'
    else:
        status = 'FAILED ❌'
        status_color = '#e74c3c'
    
    html = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; background-color: #f5f5f5; margin: 0; padding: 20px; }}
        .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .header {{ background: {status_color}; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 24px; }}
        .section {{ margin-bottom: 20px; border-left: 4px solid #3498db; padding-left: 15px; }}
        .section h2 {{ color: #2c3e50; margin: 10px 0; font-size: 18px; }}
        .section p {{ margin: 5px 0; color: #555; }}
        .app-item {{ background: #ecf0f1; padding: 10px; margin: 5px 0; border-radius: 4px; }}
        .link {{ color: #3498db; text-decoration: none; }}
        .stats {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 10px 0; }}
        .stat-box {{ background: #f8f9fa; padding: 10px; border-radius: 4px; text-align: center; }}
        .stat-number {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
        .stat-label {{ font-size: 12px; color: #7f8c8d; }}
        .footer {{ text-align: center; margin-top: 20px; padding-top: 20px; border-top: 1px solid #ecf0f1; color: #7f8c8d; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Deployment {status}</h1>
            <p>{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        </div>

        <div class="section">
            <h2>📱 Applications Deployed</h2>
    """
    
    if apps_info['static']:
        html += "<h3>⚡ Static Sites</h3>"
        for app in apps_info['static']:
            html += f'<div class="app-item">'
            html += f'<strong>{app["name"]}</strong><br>'
            if app['url']:
                html += f'<a href="{app["url"]}" class="link">🔗 {app["url"]}</a><br>'
                html += f'<a href="{app["www_url"]}" class="link">🔗 {app["www_url"]}</a>'
            html += '</div>'
    
    if apps_info['containers']:
        html += "<h3>🐳 Containers</h3>"
        for app in apps_info['containers']:
            html += f'<div class="app-item">'
            html += f'<strong>{app["name"]}</strong><br>'
            if app['url']:
                html += f'<a href="{app["url"]}" class="link">🔗 {app["url"]}</a>'
            html += '</div>'
    
    if not apps_info['static'] and not apps_info['containers']:
        html += '<p>ℹ️ No applications deployed</p>'
    
    html += """
        </div>

        <div class="section">
            <h2>🌐 Nginx Proxy Manager</h2>
    """
    
    html += f"<p>{npm_data['status']}</p>"
    
    if npm_data['created'] or npm_data['skipped'] or npm_data['failed']:
        html += '<div class="stats">'
        if npm_data['created']:
            html += f'<div class="stat-box"><div class="stat-number">{len(npm_data["created"])}</div><div class="stat-label">Created</div></div>'
        if npm_data['skipped']:
            html += f'<div class="stat-box"><div class="stat-number">{len(npm_data["skipped"])}</div><div class="stat-label">Already Configured</div></div>'
        if npm_data['failed']:
            html += f'<div class="stat-box"><div class="stat-number">{len(npm_data["failed"])}</div><div class="stat-label">Failed</div></div>'
        html += '</div>'
    
    html += """
        </div>

        <div class="section">
            <h2>🗄️ Database Migrations</h2>
    """
    
    html += f"<p>{migration_data['status']}</p>"
    
    if migration_data['databases']:
        for db_name, stats in migration_data['databases'].items():
            html += f"<h3>{db_name}</h3>"
            html += '<div class="stats">'
            if stats['created_tables']:
                html += f'<div class="stat-box"><div class="stat-number">{stats["created_tables"]}</div><div class="stat-label">Tables Created</div></div>'
            if stats['added_columns']:
                html += f'<div class="stat-box"><div class="stat-number">{stats["added_columns"]}</div><div class="stat-label">Columns Added</div></div>'
            if stats['modified_columns']:
                html += f'<div class="stat-box"><div class="stat-number">{stats["modified_columns"]}</div><div class="stat-label">Columns Modified</div></div>'
            if stats['dropped_columns']:
                html += f'<div class="stat-box"><div class="stat-number">{stats["dropped_columns"]}</div><div class="stat-label">Columns Dropped</div></div>'
            if stats['foreign_keys']:
                html += f'<div class="stat-box"><div class="stat-number">{stats["foreign_keys"]}</div><div class="stat-label">Foreign Keys</div></div>'
            if stats['indexes']:
                html += f'<div class="stat-box"><div class="stat-number">{stats["indexes"]}</div><div class="stat-label">Indexes</div></div>'
            html += '</div>'
    else:
        html += '<p>ℹ️ No migrations applied</p>'
    
    html += """
        </div>

        <div class="footer">
            <p>This is an automated deployment notification. Do not reply to this email.</p>
        </div>
    </div>
</body>
</html>
    """
    
    return html

def main():
    """Generate notification content"""
    
    deploy_result = os.environ.get('DEPLOY_RESULT', 'unknown')
    proxy_result = os.environ.get('PROXY_RESULT', 'unknown')
    
    # Parse data
    config = load_apps_json()
    apps_info = get_deployed_apps(config)
    npm_data = parse_npm_log()
    migration_data = parse_migration_log()
    
    # Build messages
    emoji, title, telegram_msg = build_telegram_message(deploy_result, proxy_result, apps_info, npm_data, migration_data)
    email_html = build_email_message(deploy_result, proxy_result, apps_info, npm_data, migration_data)
    
    # Output for GitHub Actions
    print(emoji)
    print(title)
    print(telegram_msg)
    
    # Write to files for use in workflow
    with open('telegram_message.txt', 'w') as f:
        f.write(telegram_msg)
    
    with open('email_message.html', 'w') as f:
        f.write(email_html)
    
    # Export for GitHub Actions
    with open(os.environ.get('GITHUB_OUTPUT', '/dev/null'), 'a') as f:
        f.write(f"EMOJI={emoji}\n")
        f.write(f"TITLE={title}\n")
        f.write(f"TELEGRAM_MSG={telegram_msg.replace(chr(10), '%0A')}\n")

if __name__ == '__main__':
    main()
