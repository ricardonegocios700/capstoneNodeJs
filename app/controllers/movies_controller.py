from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import request, current_app, jsonify
from http import HTTPStatus

from app.utils import find_by_genre, analyze_keys, valid_profile_kid
from werkzeug.exceptions import NotFound, BadRequestKeyError
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from psycopg2.errors import UniqueViolation
from app.exc import EmptyListError, NotFoundError, InvalidProfileError

from app.utils import find_by_genre, analyze_keys, valid_profile_kid, serializer_movies, serializer_movie
from app.configs.var_age import AGE_KIDS
from app.models.gender_model import GendersModel
from app.models.movies_model import MoviesModel
from app.models.profile_model import ProfileModel
from app.models.user_model import UserModel


@jwt_required()
def create_movie():
    try:
        if not get_jwt_identity()["administer"]:
            raise PermissionError
        
        session = current_app.db.session
        data = request.get_json()
        keys = [
            "name",
            "image",
            "description",
            "duration",
            "trailers",
            "link",
            "subtitle",
            "dubbed",
            "classification",
            "released_date"]
        

        analyze_keys(keys, data)
        data["name"] = data["name"].title()

        movie = MoviesModel(**data)

        session.add(movie)
        session.commit()

        return jsonify(serializer_movie(movie)), HTTPStatus.CREATED

    except PermissionError:
        return {"error": "Admins only"}, HTTPStatus.BAD_REQUEST

    except KeyError as e:
        return {"error": e.args[0]}, HTTPStatus.BAD_REQUEST

    except IntegrityError as e:
        if isinstance(e.orig, UniqueViolation):
            return {"error": "This movie is already exists"}, HTTPStatus.CONFLICT

  
@jwt_required()
def get_movies():
    try:
        user = UserModel.query.filter_by(id=get_jwt_identity()["id"]).first_or_404("User not found")
        if not valid_profile_kid(user):
            movies = MoviesModel.query.all()
        else:
            movies = MoviesModel.query.filter(MoviesModel.classification <= AGE_KIDS).all()
            
        if not movies:
            return {"message": "Movie not found"}, HTTPStatus.NOT_FOUND
            
        return jsonify(serializer_movies(movies)), HTTPStatus.OK
    

    except NotFoundError:
        return {"error": "Profile not found"}, HTTPStatus.NOT_FOUND
    
    except InvalidProfileError:
        return {"error": "Invalid profile for user"}, HTTPStatus.CONFLICT
    
    except EmptyListError as e:
        return {"Message": e.description}, e.code

  
@jwt_required()
def get_movie_by_id(id):
    try:
        user = UserModel.query.filter_by(id=get_jwt_identity()["id"]).first_or_404("User not found")
        if not valid_profile_kid(user):
            movie = MoviesModel.query.filter_by(id=id).first()
        else:
            movie = MoviesModel.query.filter(and_(MoviesModel.classification <= AGE_KIDS, MoviesModel.id == id)).first()


        if not movie:
            return {"message": "Movie not found"}, HTTPStatus.NOT_FOUND

        movie.views += 1
        current_app.db.session.commit()

        return jsonify(serializer_movie(movie)), HTTPStatus.OK

    except NotFoundError:
        return {"error": "Profile not found"}, HTTPStatus.NOT_FOUND
    
    except InvalidProfileError:
        return {"error": "Invalid profile for user"}, HTTPStatus.UNAUTHORIZED

      
@jwt_required()
def get_movies_by_name():
    try:
        movies_name = request.args["name"]
        user = UserModel.query.filter_by(id=get_jwt_identity()["id"]).first_or_404("User not found")
        if not valid_profile_kid(user):
            movies = MoviesModel.query.filter(MoviesModel.name.ilike(f"%{movies_name}%")).all()
        else:
            movies = MoviesModel.query.filter(and_(MoviesModel.classification <= AGE_KIDS, MoviesModel.name.ilike(f"%{movies_name}%"))).all()

        
        return jsonify(serializer_movies(movies)),HTTPStatus.OK
    

    except NotFoundError:
        return {"error": "Profile not found"}, HTTPStatus.NOT_FOUND
    
    except InvalidProfileError:
        return {"error": "Invalid profile for user"}, HTTPStatus.UNAUTHORIZED
    
    except BadRequestKeyError:
        return {"error": "The query 'name' is necessary to search by name"}, HTTPStatus.BAD_REQUEST



@jwt_required()
def get_most_seen_movies():
    try:
        user = UserModel.query.filter_by(id=get_jwt_identity()["id"]).first_or_404("User not found")
        if not valid_profile_kid(user):
            movies = MoviesModel.query.order_by(MoviesModel.views.desc()).limit(5).all()
        else:
            movies = MoviesModel.query.filter(MoviesModel.classification <= AGE_KIDS).order_by(MoviesModel.views.desc()).limit(5).all()
        
        
        return jsonify(serializer_movies(movies)), HTTPStatus.OK
    
    except NotFoundError:
        return {"error": "Profile not found"}, HTTPStatus.NOT_FOUND
    
    except InvalidProfileError:
        return {"error": "Invalid profile for user"}, HTTPStatus.UNAUTHORIZED


@jwt_required()
def get_most_recent_movies():
    try:
        user = UserModel.query.filter_by(id=get_jwt_identity()["id"]).first_or_404("User not found")
        if not valid_profile_kid(user):
            movies = MoviesModel.query.order_by(MoviesModel.created_at.desc()).all()
        else:
            movies = MoviesModel.query.filter(MoviesModel.classification <= AGE_KIDS).order_by(MoviesModel.created_at.desc()).all()
        
        
        return jsonify(serializer_movies(movies)), HTTPStatus.OK
    
    except NotFoundError:
        return {"error": "Profile not found"}, HTTPStatus.NOT_FOUND
    
    except InvalidProfileError:
        return {"error": "Invalid profile for user"}, HTTPStatus.UNAUTHORIZED


    
@jwt_required()
def delete_movie(id: int):
    try:
        administer = get_jwt_identity()
        if not administer["administer"]:
            raise PermissionError

        movie = MoviesModel.query.filter_by(id=id).first()

        if not movie:
            return {"message": "Movie not found"}, HTTPStatus.NOT_FOUND

        current_app.db.session.delete(movie)
        current_app.db.session.commit()

        return {}, HTTPStatus.NO_CONTENT

    except PermissionError:
        return {"error": "Admins only"}, HTTPStatus.BAD_REQUEST


@jwt_required()
def post_favorite():
    try:
        data = request.get_json()
        user = UserModel.query.filter_by(id=get_jwt_identity()["id"]).first_or_404("User not found")

        profile = ProfileModel.query.filter_by(id=data["profile_id"]).first_or_404("Profile not found")
        
        if not profile in user.profiles:
            raise InvalidProfileError

        user = UserModel.query.filter_by(id=get_jwt_identity()["id"]).first_or_404("User not found")
        if not valid_profile_kid(user):
            movie = MoviesModel.query.filter_by(id=data["movie_id"]).first_or_404("Movie not found")
        else:
            movie = MoviesModel.query.filter(and_(MoviesModel.id == data["movie_id"], MoviesModel.classification <= AGE_KIDS)).first_or_404("Movie not found")
        
        if movie in profile.movies:
            return jsonify({"error": "Is already favorite"}), HTTPStatus.CONFLICT
        
        profile.movies.append(movie)
        current_app.db.session.add(profile)
        current_app.db.session.commit()

        return jsonify({}), HTTPStatus.NO_CONTENT

    except NotFoundError:
        return {"error": "Profile not found"}, HTTPStatus.NOT_FOUND
    
    except InvalidProfileError:
        return {"error": "Invalid profile for user"}, HTTPStatus.UNAUTHORIZED
    
    except NotFound as e:
        return {"error": e.description}, HTTPStatus.NOT_FOUND
    


@jwt_required()
def remove_from_genre():
    administer = get_jwt_identity()
    
    try:
        if not administer["administer"]:
            raise PermissionError
        data = request.get_json()
        analyze_keys(["genre_id", "movie_id"], data)
        
        movie = MoviesModel.query.filter_by(id=data["movie_id"]).first_or_404("Movie not found")
        gender = GendersModel.query.filter_by(id=data["genre_id"]).first_or_404("Genre not found")
        remove = movie.genders.index(gender)
        movie.genders.pop(remove)
        current_app.db.session.add(movie)
        current_app.db.session.commit()
    
    except ValueError:
        return {"error": "This movie does not belong to the genre"}, HTTPStatus.NOT_FOUND

    except NotFound as e:
        return {"error": e.description}, HTTPStatus.NOT_FOUND

    except KeyError as e:
        return {"error": e.args[0]}, HTTPStatus.BAD_REQUEST
    
    except PermissionError:
        return {"error": "Admins only"}, HTTPStatus.UNAUTHORIZED
        
    
    return {}, HTTPStatus.OK

 
@jwt_required()
def add_to_genre():
    administer = get_jwt_identity()

    try:
        if not administer["administer"]:
            raise PermissionError

        data = request.get_json()
        analyze_keys(["genre_id", "movie_id"], data)

        movie = MoviesModel.query.filter_by(id=data["movie_id"]).first_or_404("Movie not found")
        gender = GendersModel.query.filter_by(id=data["genre_id"]).first_or_404("Genre not found")
        movie.genders.append(gender)
        current_app.db.session.add(gender)
        current_app.db.session.commit()

        return {}, HTTPStatus.NO_CONTENT

    except NotFound as e:
        return {"error": e.description}, HTTPStatus.NOT_FOUND

    except KeyError as e:
        return {"error": e.args[0]}, 400
    
    except PermissionError:
        return {"error": "Admins only"}, HTTPStatus.UNAUTHORIZED
    


@jwt_required()
def get_movies_by_genre():
    try:
        genre_name: str = request.args['genre']

        movies = find_by_genre(genre_name, video_type="movies")

        return jsonify(movies)

    except BadRequestKeyError:
        return {"error": "The query 'genre' is necessary to search by genre"}, HTTPStatus.BAD_REQUEST


@jwt_required()
def update_movie(id: int):
    try:
        administer = get_jwt_identity()
        if not administer["administer"]:
            raise PermissionError
        
        movie: MoviesModel = MoviesModel.query.filter_by(id=id).first_or_404("Serie not found")
        body = request.get_json()
        
        keys = [
        "name",
        "image",
        "description",
        "duration",
        "trailers",
        "link",
        "subtitle",
        "dubbed",
        "classification"]

        analyze_keys(keys, body, 'update')

        if not movie:
            return {"error": "Movie not found."}, HTTPStatus.NOT_FOUND
        
        for key, value in body.items():
            setattr(movie, key, value)
            
        current_app.db.session.add(movie)
        current_app.db.session.commit()

    except PermissionError:
        return {"error": "Admins only"}, HTTPStatus.UNAUTHORIZED

    except KeyError as e:
        return {"error": e.args[0]}, HTTPStatus.BAD_REQUEST
    
    return {}, HTTPStatus.NO_CONTENT


@jwt_required()
def remove_favorite():
    try:
        data = request.get_json()
        user = UserModel.query.filter_by(id=get_jwt_identity()["id"]).first_or_404("User not found")
        profile = ProfileModel.query.filter_by(id=data["profile_id"]).first_or_404("Profile not found")
        
        if not profile in user.profiles:
            return jsonify({"error": "Invalid profile for user"}), HTTPStatus.UNAUTHORIZED
        
        movie = MoviesModel.query.filter_by(id=data["movie_id"]).first_or_404("Movie not found")
        
        if not movie in profile.movies:
            return jsonify({"error": "Movie not found in favorite's profile"}), HTTPStatus.NOT_FOUND
        
        remove = profile.movies.index(movie)
        profile.movies.pop(remove)
        current_app.db.session.add(profile)
        current_app.db.session.commit()

        return jsonify({}), HTTPStatus.NO_CONTENT

    
    except InvalidProfileError:
        return {"error": "Invalid profile for user"}, HTTPStatus.UNAUTHORIZED
    
    except NotFound as e:
        return {"error": e.description}, HTTPStatus.NOT_FOUND
    
    

    


