from uuid import uuid4

from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from marshmallow import validate

from auth_api.commons.decorators import user_or_admin, admin_role
from auth_api.commons.pagination import paginate
from auth_api.extensions import ma, db
from auth_api.models import User
from auth_api.models.roles_enum import roles, Roles


class UserSchema(ma.ModelSchema):
    id = ma.Int(dump_only=True)
    password = ma.String(load_only=True, required=True)
    external_uuid = ma.UUID(dupm_only=True)
    role = ma.String(validate=validate.OneOf(roles), default=Roles.User)

    class Meta:
        model = User
        sqla_session = db.session


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
          name: user_id
          schema:
            type: integer
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
      parameters:
        - in: path
          name: user_id
          schema:
            type: integer
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
        404:
          description: user does not exists
    delete:
      tags:
        - api
      parameters:
        - in: path
          name: user_id
          schema:
            type: integer
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

    def get(self, user_id):
        schema = UserSchema()
        user = User.query.get_or_404(user_id)
        return {"user": schema.dump(user)}

    def put(self, user_id):
        schema = UserSchema(partial=True)
        user = User.query.get_or_404(user_id)
        user = schema.load(request.json, instance=user)

        db.session.commit()

        return {"msg": "user updated", "user": schema.dump(user)}

    def delete(self, user_id):
        user = User.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()

        return {"msg": "user deleted"}


class UserPassword(Resource):
    """Change user password

    ---
    put:
      tags:
        - api
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

    def put(self, user_id):
        schema = PasswordChangeSchema()
        request_data = schema.load(request.json)
        user = User.query.get_or_404(user_id)
        user.update_password(request_data['new_password'])

        db.session.commit()

        return "", 204


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
    post:
      tags:
        - api
      requestBody:
        content:
          application/json:
            schema:
              UserSchema
      responses:
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
    """

    method_decorators = [admin_role, jwt_required]

    def get(self):
        schema = UserSchema(many=True)
        query = User.query
        return paginate(query, schema)

    def post(self):
        schema = UserSchema()
        user = schema.load(request.json)
        user.external_uuid = uuid4()

        db.session.add(user)
        db.session.commit()

        return {"msg": "user created", "user": schema.dump(user)}, 201
