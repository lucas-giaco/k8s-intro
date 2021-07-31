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
      host='db.mysql'
    ) as connection:
      #TODO: return something
      pass
  except Error as e:
    print(e)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
