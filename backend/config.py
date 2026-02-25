import os
from dotenv import load_dotenv

load_dotenv()

config_data = dict()

# Database settings
config_data['db_username'] = os.getenv('DB_USER', 'app')
config_data['db_password'] = os.getenv('DB_PASSWORD', '')
config_data['db_host']     = os.getenv('DB_HOST', 'localhost')
config_data['db_port']     = os.getenv('DB_PORT', '5432')
config_data['db_name']     = os.getenv('DB_NAME', 'matchup')

# JWT settings
config_data['jwt_secret']       = os.getenv('JWT_SECRET', 'changeme')
config_data['jwt_algorithm']    = 'HS256'
config_data['jwt_expiry_hours'] = int(os.getenv('JWT_EXPIRY_HOURS', '24'))

# App settings
config_data['app_name'] = 'MatchUp'
config_data['debug']    = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'

# Build connection string
config_data['db_connstr'] = (
    f"postgresql://{config_data['db_username']}:{config_data['db_password']}"
    f"@{config_data['db_host']}:{config_data['db_port']}/{config_data['db_name']}"
)