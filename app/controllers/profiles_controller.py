from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.profile_model import ProfileModel
from flask import request, current_app, jsonify
from app import utils


@jwt_required()
def create_profile():
    body = request.get_json()
    identity = get_jwt_identity()

    try: 
        utils.analyze_keys(['name', "kids"], body)
        
        profile = ProfileModel(**body, user_id=identity['id'])
        profile.name = body['name'].title()

        current_app.db.session.add(profile)
        current_app.db.session.commit()

        return jsonify(profile), 201
        
    except KeyError as e:
        return {"error": str(e)}, 400
    except Exception:
        return {"error": "An unexpected error occurred"}, 400


@jwt_required()
def get_profiles():
    identity = get_jwt_identity()
    profiles = ProfileModel.query.filter_by(user_id=identity["id"]).all()

    serializer = [
        {
            "id": profile.id,
            "name": profile.name,
            "kids": profile.kids
        } for profile in profiles
    ]

    if serializer == []:
        return {"error": "Nada foi encontrado"}, 404

    return jsonify(serializer), 200
