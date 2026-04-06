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

# Email settings
config_data['mail_server']   = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
config_data['mail_port']     = int(os.getenv('MAIL_PORT', '587'))
config_data['mail_username'] = os.getenv('MAIL_USERNAME', 'matchup.noreply@gmail.com')
config_data['mail_password'] = os.getenv('MAIL_PASSWORD')
config_data['mail_sender']   = os.getenv('MAIL_SENDER', 'matchup.noreply@gmail.com')

# Mocean SMS settings
config_data['mocean_api_token'] = os.getenv('MOCEAN_API_TOKEN', '')
config_data['mocean_api_key'] = os.getenv('MOCEAN_API_KEY', '')
config_data['mocean_api_secret'] = os.getenv('MOCEAN_API_SECRET', '')
config_data['mocean_sms_url'] = os.getenv('MOCEAN_SMS_URL', 'https://rest.moceanapi.com/rest/2/sms')
config_data['mocean_sender'] = os.getenv('MOCEAN_SENDER', 'MatchUp')

# Frontend URL (used in reset email link)
config_data['frontend_url'] = os.getenv('FRONTEND_URL', 'http://team5.ua-ppdb.com/')

# Build connection string
config_data['db_connstr'] = (
    f"postgresql+psycopg://{config_data['db_username']}:{config_data['db_password']}"
    f"@{config_data['db_host']}:{config_data['db_port']}/{config_data['db_name']}"
)