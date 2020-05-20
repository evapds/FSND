import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    formatted_questions = [question.format() for question in selection]
    current_questions = formatted_questions[start:end]

    return current_questions

# create and configure the app


def create_app(test_config=None):
    app = Flask(__name__)
    setup_db(app)
    CORS(app, resources={r"*": {"origins": "*"}})

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET, POST, PATCH, DELETE, OPTIONS')
        return response

    # endpoint to handle GET requests for all available categories
    @app.route('/categories', methods=['GET'])
    def get_categories():
        categories = {}
        for category in Category.query.order_by(Category.id).all():
            categories[category.id] = category.type

            if (len(categories) == 0):
                abort(404)

        return jsonify({
            'success': True,
            'categories': categories,
            'total_categories': len(categories),
        })

    # endpoint to handle GET requests for questions, including pagination (every 10 questions).
    @app.route('/questions', methods=['GET'])
    def get_questions():
        selection = Question.query.order_by(Question.id).all()
        categories = Category.query.all()
        current_questions = paginate_questions(request, selection)
        formatted_categories = {category.id: category.type
                                for category in categories}
        total_questions = len(selection)

        if len(selection) == 0:
            abort(404)

        result = {
            'success': True,
            'questions': current_questions,
            'total_questions': total_questions,
            'categories': formatted_categories,
            'current_category': None,
        }

        return jsonify(result)

    # Delete a question
    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.filter(
                Question.id == question_id).one_or_none()

            if question is None:
                abort(404)

            question.delete()
            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)

            result = {
                'success': True,
                'delete': question_id,
                'questions': current_questions,
                'total_questions': len(Question.query.all())
            }

            return jsonify(result)

        except:
            abort(422)

    # add new questions
    @app.route('/questions', methods=['POST'])
    def create_question():
        body = request.get_json()

        new_question = body.get('question', None)
        new_category = body.get('category', None)
        new_difficulty = body.get('difficulty', None)
        new_answer = body.get('answer', None)

        try:
            question = Question(question=new_question, category=new_category,
                                difficulty=new_difficulty, answer=new_answer)
            question.insert()

            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)

            result = {
                'success': True,
                'created': question.id,
                'questions': current_questions,
                'total_questions': len(Question.query.all())
            }

            return jsonify(result)

        except:
            abort(422)

    # search for questions
    @app.route('/questionssearch', methods=['POST'])
    def search_question():
        try:
            body = request.get_json()
            search_term = body.get('searchTerm', '')

            selection = Question.query.filter(
                Question.question.ilike('%{}%'.format(search_term))).all()
            current_questions = paginate_questions(request, selection)
            formatted_questions = [question.format()
                                   for question in selection]

            if (len(formatted_questions) == 0):
                abort(400)

            result = {
                'success': True,
                'questions': formatted_questions,
                'total_questions': len(formatted_questions),
                'current_category': None
            }

            return jsonify(result)

        except:
            abort(404)

    # get questions based on category
    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def get_questions_per_category(category_id):
        try:
            category_id = str(category_id)
            selection = Question.query.filter(
                Question.category == category_id).all()
            current_questions = paginate_questions(request, selection)

            result = {
                'success': True,
                'questions': current_questions,
                'total_questions': len(selection),
                'current_category': category_id
            }

            return jsonify(result)

        except:
            abort(422)

    # play the quiz
    @app.route('/quizzes', methods=['POST'])
    def play_quiz():
        try:
            body = request.get_json()
            quiz_category = body.get('quiz_category', None).get('id')
            previous_questions = body.get('previous_questions', None)

            questions = Question.query.filter(Question.category == quiz_category).filter(
                Question.id.notin_(previous_questions)).all()

            if (len(questions) > 0):
                question = random.choice(questions).format()

                result = {
                    'success': True,
                    'question': question
                }

            else:
                result = {
                    'succes': True,
                    'question': None
                }

            return jsonify(result)

        except:
            abort(422)

    # error handlers
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'success': False,
            'error': 400,
            'message': 'Bad request'
        }), 400

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

    return app
