from flask import Flask, jsonify
from flask_cors import CORS 
from dotenv import load_dotenv 
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
  try:
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
  except mysql.connector.Error as err:
    return jsonify({"error": str(err)}), 500
  except Exception as e:
    return jsonify({"error": str(e)}), 500

@application.route("/api/produtos/<slug>")
def get_produto(slug):
  try:
    conexao = mysql.connector.connect(
      host=os.getenv('DB_HOST'),
      user=os.getenv('DB_USER'),
      password=os.getenv('DB_PASSWORD'),
      database=os.getenv('DB_NAME')
    )

    cursor = conexao.cursor(dictionary=True)
    cursor.execute('SELECT * FROM produtos WHERE slug = %s', (slug,))
    produto = cursor.fetchone()
    cursor.close()
    conexao.close()

    response = application.response_class(
      response=json.dumps(produto, ensure_ascii=False).encode('utf8'),
      mimetype='application/json'
    )

    return response
  except mysql.connector.Error as err:
    return jsonify({"error": str(err)}), 500
  except Exception as e:
    return jsonify({"error": str(e)}), 500
  
@application.route("/api/fichas/<produto_id>")
def get_fichas(produto_id):
  try:
    conexao = mysql.connector.connect(
      host=os.getenv('DB_HOST'),
      user=os.getenv('DB_USER'),
      password=os.getenv('DB_PASSWORD'),
      database=os.getenv('DB_NAME')
    )

    cursor = conexao.cursor(dictionary=True)
    cursor.execute('SELECT * FROM fichas WHERE produto_id = %s', (produto_id,))
    fichas = cursor.fetchall()
    cursor.close()
    conexao.close()

    for ficha in fichas:
      ficha['dados'] = json.loads(ficha['dados'])

    response = application.response_class(
      response=json.dumps(fichas, ensure_ascii=False).encode('utf8'),
      mimetype='application/json'
    )

    return response
  except mysql.connector.Error as err:
    return jsonify({"error": str(err)}), 500
  except Exception as e:
    return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
  application.run()