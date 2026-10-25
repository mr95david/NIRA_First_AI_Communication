"""CRUD de usuários. Cada usuário tem sua pasta em user_path/ para áudios, transcrições e respostas."""
from flask import Blueprint
from flask import request
from flask import jsonify
from api.models import users
from api import db
import os

user_bp = Blueprint('user_bp', __name__)

@user_bp.route('/users', methods = ['GET'])
@user_bp.route('/get_users', methods = ['GET'])
def getUsers():
    """Lista todos os usuários."""
    try:
        users_ = users.query.all()

        resultado = [
            {
                "id": user.id_value,
                "name": user.name,
                "lastname": user.lastname,
                "age": user.age,
                "profession": user.profession,
                "sexo": user.sexo,
                "user_path": user.user_path,
                "transcription_path": user.transcription_path,
                "ia_path": user.ia_path
            } for user in users_
        ]

        return jsonify(resultado), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@user_bp.route('/set_user', methods=['POST'])
def set_user():
    """Cria um usuário (name, lastname, age, profession, sexo) e sua pasta de dados. 409 se já existir."""
    data = request.get_json()

    if not all([data.get('name'), data.get('lastname'), data.get('age'), data.get('profession'), data.get('sexo')]):
        return jsonify({"error": "Faltan datos obligatorios"}), 400
    
    try:
        age = int(data['age'])
        if age <= 0:
            raise ValueError
    except ValueError:
        return jsonify({"error": "La edad debe ser un número entero positivo"}), 400
    
    existing_user = users.query.filter_by(name=data['name'], lastname=data['lastname']).first()
    if existing_user:
        return jsonify({"error": "El usuario con ese nombre y apellido ya existe"}), 409  # 409 Conflict


    user_path_value = f'./user_path/{data["name"]}_{data["lastname"]}_{data["age"]}'
    # Os caminhos de transcrições e IA ficam dentro de user_path_value
    transcription_path_value = f'./transcription_{data["name"]}'
    ia_path_value = f'./ia_{data["name"]}'
    new_user = users(
        name=data['name'],
        lastname=data['lastname'],
        age=age,
        profession=data['profession'],
        sexo=data['sexo'],
        user_path=user_path_value,
        transcription_path=transcription_path_value,
        ia_path=ia_path_value
    )

    try:
        db.session.add(new_user)
        db.session.commit()

        os.makedirs(user_path_value, exist_ok = True)
        os.makedirs(os.path.join(user_path_value, transcription_path_value), exist_ok = True)
        os.makedirs(os.path.join(user_path_value, ia_path_value), exist_ok = True)
        
        return jsonify({
            "message": "Nuevo usuario creado correctamente.",
            "id": new_user.id_value,
            "name": f"{new_user.name} {new_user.lastname}"
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
@user_bp.route('/delete_user', methods = ["DELETE"])
def deleteUser():
    """Remove um usuário por `id_value` ou por `name` + `lastname` (query params). Não apaga sua pasta."""
    user_id = request.args.get('id_value')
    nombre = request.args.get('name')
    apellido = request.args.get('lastname')

    if not user_id and not (nombre and apellido):
        return jsonify({"error": "Debe proporcionar un id o el nombre y apellido para eliminar al usuario"}), 400

    if user_id:
        usuario = users.query.filter_by(id_value=user_id).first()
    else:
        usuario = users.query.filter_by(name=nombre, lastname=apellido).first()

    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404

    try:
        db.session.delete(usuario)
        db.session.commit()
        return '', 204  # 204 No Content para indicar exclusão bem-sucedida
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500  # Devolve o erro se houver algum problema

@user_bp.route('/validate_user', methods=['GET'])
def validate_user():
    """Indica se o usuário `name` + `lastname` existe (query params); devolve seu id ou 0 com 404."""
    name = request.args.get('name')
    lastname = request.args.get('lastname')

    if not name or not lastname:
        return jsonify({"error": "Se requiere tanto el nombre como el apellido para la validación."}), 400

    try:
        user = users.query.filter_by(name=name, lastname=lastname).first()

        if user:
            return jsonify({"message": "Usuario encontrado", "id": user.id_value}), 200
        else:
            return jsonify({"message": "Usuario no encontrado", "id": 0}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500