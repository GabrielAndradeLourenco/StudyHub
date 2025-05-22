from flask import Flask, session as flask_app_session # ADICIONE session aqui
from flask_sqlalchemy import SQLAlchemy
import os
import json
from datetime import datetime, timedelta

db = SQLAlchemy()
ALL_QUESTIONS_DATA = []

CURRENT_DIR_OF_INIT_PY = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR_OF_INIT_PY)
QUESTIONS_JSON_PATH = os.path.join(PROJECT_ROOT, 'questoes_processadas.json')


def load_questions_on_startup():
    global ALL_QUESTIONS_DATA
    try:
        with open(QUESTIONS_JSON_PATH, 'r', encoding='utf-8') as f:
            ALL_QUESTIONS_DATA = json.load(f)
        print(f"SUCESSO: Carregadas {len(ALL_QUESTIONS_DATA)} questões de '{QUESTIONS_JSON_PATH}'.")
    except FileNotFoundError:
        print(f"AVISO CRÍTICO: Arquivo '{QUESTIONS_JSON_PATH}' NÃO ENCONTRADO. Nenhuma questão carregada.")
        ALL_QUESTIONS_DATA = []
    except json.JSONDecodeError:
        print(f"AVISO CRÍTICO: Erro ao decodificar JSON de '{QUESTIONS_JSON_PATH}'. Nenhuma questão carregada.")
        ALL_QUESTIONS_DATA = []

def create_app():
    app = Flask(__name__, instance_relative_config=False)
    app.secret_key = os.urandom(24)

    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
    # app.config['SESSION_COOKIE_SECURE'] = True # Descomente se estiver usando HTTPS
    # app.config['SESSION_COOKIE_HTTPONLY'] = True
    # app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

    instance_path_abs = os.path.join(PROJECT_ROOT, 'instance')
    if not os.path.exists(instance_path_abs):
        os.makedirs(instance_path_abs)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(instance_path_abs, 'studyhub.sqlite')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    load_questions_on_startup()

    with app.app_context():
        from . import routes
        from . import models

        @app.before_request
        def make_session_permanent():
            flask_app_session.permanent = True # Use o 'session' importado do flask

        @app.context_processor
        def inject_global_vars():
            return {
                'now': datetime.utcnow(),
                'ALL_QUESTIONS_DATA': ALL_QUESTIONS_DATA
            }
        
    return app