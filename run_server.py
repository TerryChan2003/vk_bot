import os
os.system("gunicorn --certfile cert.pem --keyfile key.pem -b 0.0.0.0:8000 flask_app:app")
