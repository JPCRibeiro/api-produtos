from flask import Flask, jsonify, request # type: ignore
from flask_cors import CORS # type: ignore
from dotenv import load_dotenv # type: ignore
import mysql.connector
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash # type: ignore
import jwt # type: ignore
from functools import wraps

load_dotenv()

application = Flask(__name__)
CORS(application)

def conexao_db(f):
  @wraps(f)
  def decorated(*args, **kwargs):
    conexao = mysql.connector.connect(
      host = os.getenv('DB_HOST'),
      user = os.getenv('DB_USER'),
      password = os.getenv('DB_PASSWORD'),
      database = os.getenv('DB_NAME')
    )

    cursor = conexao.cursor(dictionary=True)

    try:
      resultado = f(cursor, *args, **kwargs)
      conexao.commit()
    except mysql.connector.Error as err:
      conexao.rollback()
      return jsonify({"error": str(err)}), 500
    except Exception as e:
      return jsonify({"error": str(e)}), 500
    finally:
      cursor.close()
      conexao.close()
    return resultado
  return decorated
  
def token_required(f):
  @wraps(f)
  def decorated(*args, **kwargs):
    token = None

    if 'Authorization' in request.headers:
      token = request.headers['Authorization']
      if token.startswith('Bearer '):
        token = token.split(" ")[1]

    if not token:
      return jsonify({'message' : 'Token is missing!'}), 401
    
    try:
      data = jwt.decode(token, os.getenv('JWT_KEY'), algorithms=["HS256"])
      current_user = {
        "username": data['username'],
        "email": data['email']
      }
    except:
      return jsonify({'message' : 'Token is invalid!'}), 401
    return f(current_user, *args, **kwargs)
  return decorated

@application.route("/")
def index():
  return 'Hello!'

@application.route("/api/produtos")
@conexao_db
def get_produtos(cursor):
  cursor.execute('SELECT * FROM produtos')
  produtos = cursor.fetchall()

  response = application.response_class(
    response = json.dumps(produtos, ensure_ascii=False).encode('utf8'),
    mimetype = 'application/json'
  )

  return response

@application.route("/api/produtos/<slug>")
@conexao_db
def get_produto(cursor, slug):
  cursor.execute('SELECT * FROM produtos WHERE slug = %s', (slug,))
  produto = cursor.fetchone()

  response = application.response_class(
    response = json.dumps(produto, ensure_ascii=False).encode('utf8'),
    mimetype = 'application/json'
  )

  return response

@application.route("/api/fichas/<produto_id>")
@conexao_db
def get_fichas(cursor, produto_id):
  cursor.execute('SELECT * FROM fichas WHERE produto_id = %s', (produto_id,))
  fichas = cursor.fetchall()

  for ficha in fichas:
    ficha['dados'] = json.loads(ficha['dados'])

  response = application.response_class(
    response = json.dumps(fichas, ensure_ascii=False).encode('utf8'),
    mimetype = 'application/json'
  )

  return response
  
if __name__ == "__main__":
  application.debug = True
  application.run()