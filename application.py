from flask import Flask, jsonify, request 
from flask_cors import CORS 
from dotenv import load_dotenv 
import mysql.connector
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash 
import jwt 
import datetime
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
    
@application.route("/api/registro", methods=['POST'])
@conexao_db
def register(cursor):
  username = request.json['username']
  email = request.json['email']

  errors = []

  cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
  if cursor.fetchone():
    errors.append('Email já cadastrado')

  cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
  if cursor.fetchone():
    errors.append('Nome de usuário já cadastrado')

  if errors:
    return jsonify({"error": errors}), 401
    
  password = request.json['password']
  hashed_password = generate_password_hash(password)
  cursor.execute('INSERT INTO users (username, email, password) VALUES (%s, %s, %s)', (username, email, hashed_password))

  response = {
    "message": "Conta criada com sucesso",
    "user": {
      "username": username,
      "email": email
    }
  }

  return jsonify(response), 201

@application.route("/api/login", methods=['POST'])
@conexao_db
def login(cursor):
  email = request.json['email']
  password = request.json['password']

  if not email or not password:
    return jsonify({"error": "Email e senha são necessários"}), 400

  cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
  user = cursor.fetchone()

  if user and check_password_hash(user['password'], password):
    username = user['username']
    token = jwt.encode({
      "username": username, 
      "email": email,
      "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
    }, os.getenv('JWT_KEY'), algorithm="HS256")

    print(token)

    response = {
      "message": "Usuário autenticado",
      "token": token,
      "user": {
        "username": username,
        "email": email
      }
    }
  
    return jsonify(response), 200
  else:
    return jsonify({"error": "Credenciais inválidas"}), 401
  
@application.route("/api/user", methods=['GET'])
@conexao_db
def get_user(cursor):
  token = None

  if 'Authorization' in request.headers:
    token = request.headers['Authorization']
    if token.startswith('Bearer '):
      token = token.split(" ")[1]

  try:
    data = jwt.decode(token, os.getenv('JWT_KEY'), algorithms=["HS256"])
    current_user = {
      "username": data['username'],
      "email": data['email']
    }

    cursor.execute('SELECT * FROM users WHERE email = %s', (current_user['email'],))
    user = cursor.fetchone()

    print(user)

    if user:
      user_info = {
        "username": user['username'],
        "email": user['email'],
      }
      return jsonify(user_info), 200
    else:
      return jsonify({"error": "Usuário não encontrado"}), 404
    
  except jwt.ExpiredSignatureError:
    return jsonify({"error": "Token expirado"}), 401
  except jwt.InvalidTokenError:
    return jsonify({"error": "Token inválido"}), 401
  
if __name__ == "__main__":
  application.debug = True
  application.run()