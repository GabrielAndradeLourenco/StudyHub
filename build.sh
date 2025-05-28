#!/bin/bash
# Instalar dependências do backend
pip install -r backend/requirements.txt

# Garantir que o diretório instance existe
mkdir -p instance

# Inicializar o banco de dados
python -m flask --app run.py init-db