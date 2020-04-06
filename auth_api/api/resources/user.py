from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource, abort
from marshmallow import validate
from webargs.flaskparser import use_kwargs

from auth_api.commons.decorators import user_or_admin, admin_role
from auth_api.commons.pagination import paginate
from auth_api.extensions import ma, db
from auth_api.models import User
from auth_api.models.roles_enum import roles, Roles


class UserSchema(ma.SQLAlchemyAutoSchema):
    password = ma.String(load_only=True, required=True)
    external_uuid = ma.UUID(dupm_only=True, data_key="uuid")
    role = ma.String(validate=validate.OneOf(roles), default=Roles.User)
    resources = ma.List(ma.String(), default=[])

    class Meta:
        model = User
        sqla_session = db.session
        load_instance = True
        include_relationships = True
        exclude = ('id',)


class UserPublicSchema(ma.Schema):
    external_uuid = ma.UUID(data_key='uuid')
    username = ma.String()


class PasswordChangeSchema(ma.Schema):
    new_password = ma.String(load_only=True, required=True)


class UserResource(Resource):
    """Single object resource

    ---
    get:
      tags:
        - api
      parameters:
        - in: path
          name: user_uuid
          schema:
            type: string
            format: uuid
      responses:
        200:
          content:
            application/json:
              schema:
                type: object
                properties:
                  user: UserSchema
        404:
          description: user does not exists
    put:
      tags:
        - api
      description: create or update user
      parameters:
        - in: path
          name: user_uuid
          schema:
            type: string
            format: uuid
      requestBody:
        content:
          application/json:
            schema:
              UserSchema
      responses:
        200:
          content:
            application/json:
              schema:
                type: object
                properties:
                  msg:
                    type: string
                    example: user updated
                  user: UserSchema
        201:
          content:
            application/json:
              schema:
                type: object
                properties:
                  msg:
                    type: string
                    example: user created
                  user: UserSchema
        404:
          description: user does not exists
    delete:
      tags:
        - api
      parameters:
        - in: path
          name: user_uuid
          schema:
            type: string
            format: uuid
      responses:
        200:
          content:
            application/json:
              schema:
                type: object
                properties:
                  msg:
                    type: string
                    example: user deleted
        404:
          description: user does not exists
    """

    method_decorators = {'get': [user_or_admin, jwt_required],
                         'put': [admin_role, jwt_required],
                         'delete': [admin_role, jwt_required]}

    def get(self, user_uuid):
        schema = UserSchema()
        user = User.query.filter(User.external_uuid == user_uuid).first_or_404()
        return {"user": schema.dump(user)}

    def put(self, user_uuid):
        schema = UserSchema(partial=True)
        user = User.query.filter(User.external_uuid == user_uuid).first()
        if not user:
            create_schema = UserSchema()
            user = create_schema.load(request.json)
            if User.query.filter(User.username == user.username).first() is not None:
                return "Username already exists", 409
            if User.query.filter(User.email == user.email).first() is not None:
                return "Email already exists", 409

            user.external_uuid = user_uuid
            db.session.add(user)
            result_text = "user created"
            status = 201
        else:
            user = schema.load(request.json, instance=user)
            result_text = "user updated"
            status = 200

        db.session.commit()

        return {"msg": result_text, "user": schema.dump(user)}, status

    def delete(self, user_uuid):
        user = User.query.filter(User.external_uuid == user_uuid).first_or_404()
        db.session.delete(user)
        db.session.commit()

        return {"msg": "user deleted"}


class UserPassword(Resource):
    """Change user password

    ---
    put:
      tags:
        - api
      parameters:
        - in: path
          name: user_uuid
          schema:
            type: string
            format: uuid
      requestBody:
        content:
          application/json:
            schema:
              PasswordChangeSchema
      responses:
        204:
          description: password changed
        403:
          description: access denied
        404:
          description: user does not exists
    """

    method_decorators = [user_or_admin, jwt_required]

    def put(self, user_uuid):
        schema = PasswordChangeSchema()
        request_data = schema.load(request.json)
        user = User.query.filter(User.external_uuid == user_uuid).first_or_404()
        user.update_password(request_data['new_password'])

        db.session.commit()

        return "", 204


class UserPublicInfo(Resource):
    """Get public info for users

    ---
    get:
      tags:
        - api
      parameters:
        - in: query
          name: uuids
          schema:
            type: array
            items:
              type: string
              format: uuid
      responses:
        200:
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/UserPublicSchema'
        404:
          description: user does not exists
    """

    method_decorators = {'get': [use_kwargs({'uuids': ma.List(ma.UUID(), required=True)}, location='query'),
                                 jwt_required]}

    def get(self, uuids):
        schema = UserPublicSchema(many=True)
        users = User.query.filter(User.external_uuid.in_(uuids)).all()
        if not len(users) == len(set(uuids)):
            abort(404)
        return schema.dump(users)


class UserList(Resource):
    """Creation and get_all

    ---
    get:
      tags:
        - api
      responses:
        200:
          content:
            application/json:
              schema:
                allOf:
                  - $ref: '#/components/schemas/PaginatedResult'
                  - type: object
                    properties:
                      results:
                        type: array
                        items:
                          $ref: '#/components/schemas/UserSchema'
    """

    method_decorators = [admin_role, jwt_required]

    def get(self):
        schema = UserSchema(many=True)
        query = User.query
        return paginate(query, schema)
