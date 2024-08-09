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
      return jsonify({'message': 'Token is missing!'}), 401

    try:
      if not isinstance(token, str):
        raise ValueError('Expected a string value')
      data = jwt.decode(token, os.getenv('JWT_KEY'), algorithms=["HS256"])
      current_user = {
        "username": data['username'],
        "email": data['email']
      }
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError) as e:
      return jsonify({'message': 'Token is invalid!'}), 401
    except ValueError as ve:
      return jsonify({'message': str(ve)}), 400
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
    
@application.route("/api/registro", methods=['POST'])
@conexao_db
def register(cursor):
    username = request.json['username']
    email = request.json['email']

    cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
    existing_user = cursor.fetchone()
    
    if existing_user:
      return jsonify({"error": "Email já registrado"}), 400
    
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
    token = jwt.encode({"username": username, "email": email}, os.getenv('JWT_KEY'), algorithm="HS256")

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
@token_required
def get_user(current_user, cursor):
  cursor.execute('SELECT * FROM users WHERE username = %s', (current_user['username'],))
  user = cursor.fetchone()

  if user:
    user_info = {
      "username": user['username'],
      "email": user['email'],
    }
    return jsonify(user_info), 200
  else:
    return jsonify({"error": "Usuário não encontrado"}), 404
  
if __name__ == "__main__":
  application.debug = True
  application.run()