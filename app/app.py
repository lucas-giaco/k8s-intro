import os
import socket
from mysql.connector import connect, Error
from flask import Flask

app = Flask(__name__)

@app.route("/exit")
def exit():
  return os._exit(0)

@app.route("/whoami")
def whoami():
  return socket.gethostname()

@app.route("/db")
def db():
  try:
    with connect(
      host=os.getenv('DB_HOST', default='localhost'),
      port=os.getenv('DB_PORT', default=3306),
      user=os.getenv('DB_USER'),
      password=os.getenv('DB_PASSWORD')
    ) as connection:
      if connection.is_connected():
        db_Info = connection.get_server_info()
        return f"Connected to MySQL Server version {db_Info}"
  except Error as e:
    print(e)
    return 'Unable to connect to DB'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
