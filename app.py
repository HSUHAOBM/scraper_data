import os
from dotenv import load_dotenv
from flask import Flask
from routes import main
import secrets

load_dotenv()

app = Flask(__name__)

app.secret_key = secrets.token_hex(32)
SCRAPER_PASSWORD = os.getenv('SCRAPER_PASSWORD')

app.register_blueprint(main)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
