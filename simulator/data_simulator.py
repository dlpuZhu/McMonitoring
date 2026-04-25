import argparse
import random
import sqlite3
import sys
from datetime import datetime, timedelta
from urllib.parse import urlparse

try:
    import mysql.connector as mysql_connector
except ImportError:
    mysql_connector = None

try:
    import pymysql
except ImportError:
    pymysql = None

CONNECTOR_TYPES = ['SQLServer', 'PostgreSQL', 'CosmosDB', 'MongoDB', 'MySQL']
REGIONS = ['EastUS', 'WestEurope', 'SoutheastAsia', 'JapanEast']
STATUSES = ['Running', 'Failed', 'Creating', 'Paused', 'Completed']
ERROR_CODES = ['E001', 'E002', 'E003', 'E004']


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
        return sqlite3.connect(config['database'], detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    if config['driver'] == 'mysql':
        if mysql_connector is not None:
            return mysql_connector.connect(
                user=config['user'],
                password=config['password'],
                host=config['host'],
                port=config['port'],
                database=config['database'],
                autocommit=True,
            )
        if pymysql is not None:
            return pymysql.connect(
                user=config['user'],
                password=config['password'],
                host=config['host'],
                port=config['port'],
                database=config['database'],
                autocommit=True,
            )
        raise RuntimeError('MySQL support requires mysql-connector-python or PyMySQL')
    raise RuntimeError('Unsupported database driver')


def create_schema(conn):
    cursor = conn.cursor()
    if isinstance(conn, sqlite3.Connection):
        job_table = '''CREATE TABLE IF NOT EXISTS ConnectorJobs (
            JobId INTEGER PRIMARY KEY AUTOINCREMENT,
            ConnectorType VARCHAR(50),
            Region VARCHAR(50),
            Status VARCHAR(20),
            ErrorCode VARCHAR(20),
            CreatedTime DATETIME,
            LastUpdatedTime DATETIME,
            DurationSeconds INT
        );'''
        metrics_table = '''CREATE TABLE IF NOT EXISTS ConnectorJobMetrics (
            MetricsId INTEGER PRIMARY KEY AUTOINCREMENT,
            JobId INTEGER,
            ThroughputMbps REAL,
            ErrorCount INT,
            Retries INT,
            LastHeartbeat DATETIME,
            FOREIGN KEY(JobId) REFERENCES ConnectorJobs(JobId)
        );'''
    else:
        job_table = '''CREATE TABLE IF NOT EXISTS ConnectorJobs (
            JobId INT PRIMARY KEY AUTO_INCREMENT,
            ConnectorType VARCHAR(50),
            Region VARCHAR(50),
            Status VARCHAR(20),
            ErrorCode VARCHAR(20),
            CreatedTime DATETIME,
            LastUpdatedTime DATETIME,
            DurationSeconds INT
        );'''
        metrics_table = '''CREATE TABLE IF NOT EXISTS ConnectorJobMetrics (
            MetricsId INT PRIMARY KEY AUTO_INCREMENT,
            JobId INT,
            ThroughputMbps DOUBLE,
            ErrorCount INT,
            Retries INT,
            LastHeartbeat DATETIME,
            FOREIGN KEY(JobId) REFERENCES ConnectorJobs(JobId)
        );'''
    cursor.execute(job_table)
    cursor.execute(metrics_table)
    if hasattr(conn, 'commit'):
        conn.commit()


def random_job():
    status = random.choices(
        STATUSES,
        weights=[0.35, 0.15, 0.10, 0.10, 0.30],
        k=1,
    )[0]
    duration = {
        'Running': random.randint(30, 7200),
        'Failed': random.randint(5, 3600),
        'Creating': random.randint(3, 600),
        'Paused': random.randint(0, 1800),
        'Completed': random.randint(10, 10800),
    }[status]
    error_code = random.choice(ERROR_CODES) if status == 'Failed' else None
    created = datetime.utcnow() - timedelta(seconds=random.randint(3600, 86400))
    updated = created + timedelta(seconds=random.randint(0, max(1, duration)))
    throughput = {
        'Running': random.uniform(10.0, 120.0),
        'Completed': random.uniform(5.0, 80.0),
        'Failed': random.uniform(0.0, 40.0),
        'Creating': random.uniform(0.0, 10.0),
        'Paused': 0.0,
    }[status]
    return {
        'ConnectorType': random.choice(CONNECTOR_TYPES),
        'Region': random.choice(REGIONS),
        'Status': status,
        'ErrorCode': error_code,
        'CreatedTime': created.strftime('%Y-%m-%d %H:%M:%S'),
        'LastUpdatedTime': updated.strftime('%Y-%m-%d %H:%M:%S'),
        'DurationSeconds': duration,
        'ThroughputMbps': round(throughput, 2),
        'ErrorCount': random.randint(0, 6) if status == 'Failed' else random.randint(0, 2),
        'Retries': random.randint(0, 4) if status in ['Failed', 'Paused'] else random.randint(0, 2),
        'LastHeartbeat': (datetime.utcnow() - timedelta(seconds=random.randint(0, 300))).strftime('%Y-%m-%d %H:%M:%S'),
    }


def populate_data(conn, count):
    cursor = conn.cursor()
    job_sql = '''INSERT INTO ConnectorJobs (ConnectorType, Region, Status, ErrorCode, CreatedTime, LastUpdatedTime, DurationSeconds)
                 VALUES (%s, %s, %s, %s, %s, %s, %s)'''
    metrics_sql = '''INSERT INTO ConnectorJobMetrics (JobId, ThroughputMbps, ErrorCount, Retries, LastHeartbeat)
                     VALUES (%s, %s, %s, %s, %s)'''
    if isinstance(conn, sqlite3.Connection):
        job_sql = job_sql.replace('%s', '?')
        metrics_sql = metrics_sql.replace('%s', '?')
    rows = [random_job() for _ in range(count)]
    for row in rows:
        cursor.execute(
            job_sql,
            (
                row['ConnectorType'],
                row['Region'],
                row['Status'],
                row['ErrorCode'],
                row['CreatedTime'],
                row['LastUpdatedTime'],
                row['DurationSeconds'],
            ),
        )
        job_id = cursor.lastrowid
        cursor.execute(
            metrics_sql,
            (
                job_id,
                row['ThroughputMbps'],
                row['ErrorCount'],
                row['Retries'],
                row['LastHeartbeat'],
            ),
        )
    if hasattr(conn, 'commit'):
        conn.commit()
    print(f'Inserted {count} ConnectorJobs and {count} ConnectorJobMetrics records.')


def main():
    parser = argparse.ArgumentParser(description='Connector Service Data Simulator')
    parser.add_argument('--db-url', default='sqlite:///connector_monitor.db', help='Database URL, e.g. sqlite:///file.db or mysql://user:pass@host:port/db')
    parser.add_argument('--rows', type=int, default=300, help='Number of ConnectorJobs records to generate')
    args = parser.parse_args()
    conn = connect(args.db_url)
    create_schema(conn)
    populate_data(conn, args.rows)
    conn.close()


if __name__ == '__main__':
    main()
