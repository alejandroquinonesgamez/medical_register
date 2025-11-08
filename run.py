from app import create_app
from app.config import SERVER_CONFIG

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host=SERVER_CONFIG["host"], port=SERVER_CONFIG["port"])


