# Este arquivo agora serve apenas para inicializar o banco de dados

import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Adiciona o diretório backend ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Importa o app do backend
from app import app, db

@app.cli.command("init-db")
def init_db_command_run():
    """Cria as tabelas do banco de dados."""
    with app.app_context():
        db.create_all()
    print("Banco de dados inicializado e tabelas criadas!")