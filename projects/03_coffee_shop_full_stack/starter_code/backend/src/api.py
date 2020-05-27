import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
# db_drop_and_create_all()


# ROUTES

# see drinks
@app.route('/drinks', methods=['GET'])
def get_drinks():
    all_drinks = Drink.query.all()
    drinks = [drink.short() for drink in all_drinks]
    if len(drinks) == 0:
        abort(404)
    else:
        return jsonify({
            'success': True,
            'drinks': drinks
        })

# see drinks details
@app.route('/drinks-detail', methods=['GET'])
@requires_auth(permission='get:drinks-detail')
def get_drinks_detail(payload):
    all_drinks = Drink.query.all()
    drinks = [drink.long() for drink in all_drinks]
    if len(drinks) == 0:
        abort(404)
    else:
        return jsonify({
            'success': True,
            'drinks': drinks
        })

# add new drinks
@app.route('/drinks', methods=['POST'])
@requires_auth(permission='post:drinks')
def add_drinks(payload):
    body = request.get_json()
    new_title = body.get('title', None)
    new_recipe = body.get('recipe', None)

    try:
        drink = Drink(title=new_title, recipe=json.dumps([new_recipe]))
        drink.insert()

        # all_drinks = Drink.query.order_by(Drink.id).all()
        # drink = [drink.long() for drink in all_drinks]

        result = {
            'success': True,
            'drinks': [drink.long()]
        }

        return jsonify(result)

    except:
        abort(422)


# update existing drink
@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth(permission='patch:drinks')
def update_drink(payload, id):
    body = request.get_json()
    title = body.get("title")

    try:
        drink = Drink.query.filter(Drink.id == id).one_or_none()
        if drink is None:
            abort(404)

        drink.title = title
        drink.update()

        result = {
            'success': True,
            'drinks': [drink.long()]
        }

        return jsonify(result)

    except:
        abort(422)


# delete existing drink
@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth(permission='delete:drinks')
def delete_drink(payload, id):
    try:
        drink = Drink.query.filter(Drink.id == id).one_or_none()

        if drink is None:
            abort(404)

        drink.delete()
        #remaining_drinks = Drink.query.order_by(Drink.id).all()

        result = {
            'success': True,
            'delete': id,
            # 'drinks': remaining_drinks
        }

        return jsonify(result)

    except:
        abort(422)

# Error Handling
@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': 400,
        'message': 'Bad request'
    }), 400


@app.errorhandler(401)
def unauthorized(error):
    return jsonify({
        'success': False,
        'error': 401,
        'message': 'Unauthorized'
    }), 401


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 404,
        'message': 'Not found'
    }), 404


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        'success': False,
        'error': 422,
        'message': 'Unprocessable'
    }), 422


@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({
        'success': False,
        'error': 500,
        'message': 'Internal Server Error'
    }), 500


@app.errorhandler(AuthError)
def handle_auth_error(ex):
    return jsonify({
        'success': False,
        'error': ex.status_code,
        'message': ex.error['code']
    }), 401
