import traceback
from flask import request, make_response, render_template
from flask_restful import Resource
from werkzeug.security import safe_str_cmp
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_refresh_token_required,
    get_jwt_identity,
    jwt_required,
    get_raw_jwt,
)
from models.user import UserModel
from schemas.user import UserSchema
from libs.mailgun import MailGunException
from blacklist import BLACKLIST

BLANK_ERROR = "'{}' cannot be blank."
USER_ALREADY_EXISTS = "A user with that username already exists."
EMAIL_ALREADY_EXISTS = "A user with that email already exists."
CREATED_SUCCESSFULLY = "User created successfully, please check your email for activation link."
USER_ACTIVATED = "User activated."
USER_NOT_FOUND = "User not found."
USER_DELETED = "User deleted."
INVALID_CREDENTIALS = "Invalid credentials!"
USER_LOGGED_OUT = "User <id={user_id}> successfully logged out."
NOT_CONFIRMED_ERROR = "You have not confirmed registration, please check your email <{}>."
FAILED_TO_CREATE = "Internal server error. Failed to created user."

user_schema = UserSchema()


class UserRegister(Resource):
    @classmethod
    def post(cls):
        user = user_schema.load(request.get_json())

        if UserModel.find_by_username(user.username):
            return {"message": USER_ALREADY_EXISTS}, 400

        if UserModel.find_by_email(user.email):
            return {"message": EMAIL_ALREADY_EXISTS}, 400

        try:
            user.save_to_db()
            user.send_confirmation_email()
            return {"message": CREATED_SUCCESSFULLY}, 201
        except MailGunException as e:
            user.delete_from_db()
            return {'message': str(e)}, 500
        except:
            traceback.print_exc()
            return {'message': FAILED_TO_CREATE}, 500


class User(Resource):
    """
    This resource can be useful when testing our Flask app. We may not want to expose it to public users, but for the
    sake of demonstration in this course, it can be useful when we are manipulating data regarding the users.
    """

    @classmethod
    def get(cls, user_id: int):
        user = UserModel.find_by_id(user_id)
        if not user:
            return {"message": USER_NOT_FOUND}, 404
        return user_schema.dump(user), 200

    @classmethod
    def delete(cls, user_id: int):
        user = UserModel.find_by_id(user_id)
        if not user:
            return {"message": USER_NOT_FOUND}, 404
        user.delete_from_db()
        return {"message": USER_DELETED}, 200


class UserLogin(Resource):
    @classmethod
    def post(cls):
        user_data = user_schema.load(request.get_json(), partial=('email',))

        user = UserModel.find_by_username(user_data.username)

        # this is what the `authenticate()` function did in security.py
        if user and safe_str_cmp(user.password, user_data.password):
            if user.activated:
                # identity= is what the identity() function did in security.py—now stored in the JWT
                access_token = create_access_token(identity=user.id, fresh=True)
                refresh_token = create_refresh_token(user.id)
                return {"access_token": access_token, "refresh_token": refresh_token}, 200
            else:
                return {"message": NOT_CONFIRMED_ERROR.format(user.username)}, 400

        return {"message": INVALID_CREDENTIALS}, 401


class UserLogout(Resource):
    @classmethod
    @jwt_required
    def post(cls):
        jti = get_raw_jwt()["jti"]  # jti is "JWT ID", a unique identifier for a JWT.
        user_id = get_jwt_identity()
        BLACKLIST.add(jti)
        return {"message": USER_LOGGED_OUT.format(user_id)}, 200


class TokenRefresh(Resource):
    @classmethod
    @jwt_refresh_token_required
    def post(cls):
        current_user = get_jwt_identity()
        new_token = create_access_token(identity=current_user, fresh=False)
        return {"access_token": new_token}, 200


class UserConfirm(Resource):
    @classmethod
    def get(cls, user_id: int):
        user = UserModel.find_by_id(user_id)
        if user:
            user.activated = True
            user.save_to_db()
            headers = {'Content-Type': 'text/html'}
            return make_response(render_template('confirmation_page.html', email=user.username), 200, headers)

        return {'message': USER_NOT_FOUND}, 400
