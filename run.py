import os
from app import create_app

# Get config name from environment, default to development
config_name = os.environ.get('FLASK_ENV', 'development')
if config_name == 'production':
    config_name = 'production'
else:
    config_name = 'development'

app = create_app(config_name)

if __name__ == '__main__':
    app.run(debug=(config_name != 'production'), port=5000, host='0.0.0.0')