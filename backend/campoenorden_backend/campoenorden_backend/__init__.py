import os

_db_engine = os.environ.get('DATABASE_ENGINE', 'postgresql')
if 'mysql' in _db_engine or 'mysql' in os.environ.get('DJANGO_SETTINGS_MODULE', ''):
    import pymysql
    pymysql.install_as_MySQLdb()
