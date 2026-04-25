import argparse
import json
import sqlite3
from urllib.parse import urlparse

try:
    import mysql.connector as mysql_connector
except ImportError:
    mysql_connector = None

try:
    import pymysql
except ImportError:
    pymysql = None

EXPECTED_PANELS = {
    'Connector Jobs by Status',
    'Failed Jobs by Connector Type',
    'Regional Failure Rate',
    'Active Jobs and Error Count',
    'Job Duration Distribution',
}

EXPECTED_ALERT_KEYS = {
    'HighFailureRate',
    'SlowCompletion',
    'NoActiveJobs',
    'RegionalFailureSpike',
}


def parse_db_url(db_url):
    parsed = urlparse(db_url)
    if parsed.scheme == 'sqlite':
        if parsed.path == ':memory:':
            return {'driver': 'sqlite', 'database': ':memory:'}
        if parsed.path.startswith('/') and not parsed.netloc:
            return {'driver': 'sqlite', 'database': parsed.path[1:]}
        return {'driver': 'sqlite', 'database': parsed.path}
    if parsed.scheme == 'mysql':
        return {
            'driver': 'mysql',
            'user': parsed.username,
            'password': parsed.password,
            'host': parsed.hostname or '127.0.0.1',
            'port': parsed.port or 3306,
            'database': parsed.path.lstrip('/'),
        }
    raise ValueError('Unsupported DB URL scheme: %s' % parsed.scheme)


def connect(db_url):
    config = parse_db_url(db_url)
    if config['driver'] == 'sqlite':
        return sqlite3.connect(config['database'])
    if config['driver'] == 'mysql':
        if mysql_connector is not None:
            return mysql_connector.connect(
                user=config['user'],
                password=config['password'],
                host=config['host'],
                port=config['port'],
                database=config['database'],
            )
        if pymysql is not None:
            return pymysql.connect(
                user=config['user'],
                password=config['password'],
                host=config['host'],
                port=config['port'],
                database=config['database'],
            )
        raise RuntimeError('MySQL support requires mysql-connector-python or PyMySQL')
    raise RuntimeError('Unsupported database driver')


def query_one(cursor, sql):
    cursor.execute(sql)
    return cursor.fetchone()[0]


def validate_database(cursor):
    results = []
    total = query_one(cursor, 'SELECT COUNT(1) FROM ConnectorJobs')
    results.append(('Total rows', total >= 50, f'{total} rows present'))
    failed = query_one(cursor, "SELECT COUNT(1) FROM ConnectorJobs WHERE Status='Failed'")
    results.append(('Failed row existence', failed >= 1, f'{failed} failed rows'))
    running = query_one(cursor, "SELECT COUNT(1) FROM ConnectorJobs WHERE Status='Running'")
    results.append(('Running row existence', running >= 1, f'{running} running rows'))
    ext = query_one(cursor, 'SELECT COUNT(1) FROM ConnectorJobMetrics')
    results.append(('Metrics table rows', ext >= total, f'{ext} metrics rows for {total} jobs'))
    failed_ratio = failed / max(total, 1)
    results.append(('Failure ratio within range', 0.02 <= failed_ratio <= 0.25, f'{failed_ratio:.2%} failure ratio'))
    return results


def validate_dashboard_file(path):
    results = []
    with open(path, 'r', encoding='utf-8') as fh:
        dashboard = json.load(fh)

    panels = {panel.get('title') for panel in dashboard.get('panels', []) if panel.get('title')}
    missing = EXPECTED_PANELS - panels
    results.append(('Expected panels exist', not missing, f'missing panels: {sorted(missing)}' if missing else 'all panels found'))

    definitions = dashboard.get('templating', {}).get('list', [])
    results.append(('Dashboard variables defined', len(definitions) >= 1, f'{len(definitions)} variables configured'))

    alert_names = set()
    for panel in dashboard.get('panels', []):
        alert = panel.get('alert')
        if alert and alert.get('name'):
            alert_names.add(alert['name'])
    missing_alerts = EXPECTED_ALERT_KEYS - alert_names
    results.append(('Expected alerts present', not missing_alerts, f'missing alerts: {sorted(missing_alerts)}' if missing_alerts else 'all alerts found'))
    return results


def main():
    parser = argparse.ArgumentParser(description='Self validation for Connector Service monitoring skill')
    parser.add_argument('--db-url', default='sqlite:///connector_monitor.db')
    parser.add_argument('--dashboard', default='grafana/dashboards/connector_service_dashboard.json')
    args = parser.parse_args()

    conn = connect(args.db_url)
    cursor = conn.cursor()
    db_results = validate_database(cursor)
    dash_results = validate_dashboard_file(args.dashboard)

    print('\nSelf-validation summary:\n')
    all_ok = True
    for name, passed, message in db_results + dash_results:
        status = 'PASS' if passed else 'FAIL'
        print(f'[{status}] {name}: {message}')
        if not passed:
            all_ok = False

    print('\nOverall result:', 'PASSED' if all_ok else 'FAILED')
    conn.close()
    if not all_ok:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
