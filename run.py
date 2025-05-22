from app import create_app

app = create_app()

@app.cli.command("init-db")
def init_db_command_run():
    """Cria as tabelas do banco de dados."""
    from app import db # Importa db aqui, dentro do contexto do comando
    with app.app_context():
         db.create_all()
    print("Banco de dados inicializado e tabelas criadas!")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)