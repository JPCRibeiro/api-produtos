from flask import Flask # type: ignore
from flask_cors import CORS # type: ignore
from dotenv import load_dotenv # type: ignore
import mysql.connector
import json
import os

load_dotenv()

application = Flask(__name__)
CORS(application)

@application.route("/")
def index():
  return 'Hello!'

@application.route("/api/produtos")
def get_produtos():
  conexao = mysql.connector.connect(
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME')
  )

  cursor = conexao.cursor(dictionary=True)
  cursor.execute('SELECT * FROM produtos')
  produtos = cursor.fetchall()
  cursor.close()
  conexao.close()
  
  response = application.response_class(
    response=json.dumps(produtos, ensure_ascii=False).encode('utf8'),
    mimetype='application/json'
  )
  
  return response