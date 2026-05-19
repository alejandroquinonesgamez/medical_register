from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return {
        "status": "success",
        "message": "Servidor Flask corriendo en Debian con Gunicorn y Nginx",
        "version": "1.0"
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0')
