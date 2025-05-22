from flask import current_app, render_template, url_for, abort, jsonify, request
from sqlalchemy import desc
from . import db, ALL_QUESTIONS_DATA # Importa db e ALL_QUESTIONS_DATA de app/__init__.py
from .models import UserResponse
import os # Para a rota do scraper

# Se você tiver o scraper_selenium.py na raiz do projeto (StudyHub_Project)
# e run.py também, o import pode ser relativo ao diretório de execução.
# Ou defina o caminho absoluto.
# Para simplicidade, vamos assumir que o scraper pode ser importado se estiver no sys.path
# ou ajustamos o import depois.

@current_app.route('/')
def index():
    total_answered = 0
    correct_answered = 0
    accuracy = 0.0
    
    total_answered = UserResponse.query.count() # Já está dentro do app_context implicitamente
    correct_answered = UserResponse.query.filter_by(is_correct=True).count()
    
    if total_answered > 0:
        accuracy = (correct_answered / total_answered) * 100
    
    return render_template('index.html', 
                           num_questions=len(ALL_QUESTIONS_DATA),
                           total_answered=total_answered,
                           accuracy=accuracy)

@current_app.route('/question/<int:question_idx>')
def show_question(question_idx):
    if not ALL_QUESTIONS_DATA:
        return "Nenhuma questão carregada. Por favor, execute o scraper ou verifique 'questoes_processadas.json'.", 404
    
    if 0 <= question_idx < len(ALL_QUESTIONS_DATA):
        question = ALL_QUESTIONS_DATA[question_idx]
        previous_response = None
        if 'id_original_json' in question:
            previous_response = UserResponse.query.filter_by(
                question_id_original=str(question['id_original_json'])
            ).order_by(desc(UserResponse.timestamp)).first()
        
        return render_template('questao.html', 
                               question=question,
                               question_index=question_idx,
                               total_questions=len(ALL_QUESTIONS_DATA),
                               previous_response=previous_response)
    else:
        abort(404)

@current_app.route('/submit_answer', methods=['POST'])
def submit_answer():
    data = request.get_json()
    # Adicione seus logs de DEBUG aqui se precisar
    if not data:
        return jsonify({"success": False, "message": "Dados não recebidos."}), 400

    question_idx_from_js = data.get('question_index')
    user_choice_letter = data.get('chosen_letter')
    
    if question_idx_from_js is None or user_choice_letter is None:
        return jsonify({"success": False, "message": "Dados incompletos."}), 400

    try:
        question_idx = int(question_idx_from_js)
    except ValueError:
        return jsonify({"success": False, "message": "Índice da questão inválido."}), 400

    if not (0 <= question_idx < len(ALL_QUESTIONS_DATA)):
        return jsonify({"success": False, "message": f"Índice da questão ({question_idx}) fora do range."}), 400

    question_data = ALL_QUESTIONS_DATA[question_idx]
    
    question_id_original_to_save = str(question_data.get('id_original_json', f"idx_{question_idx}"))

    correct_letter = question_data.get('resposta_sugerida_letra')
    is_correct_answer = False
    if correct_letter and isinstance(correct_letter, str) and correct_letter.strip():
        is_correct_answer = (user_choice_letter == correct_letter)
    
    try:
        new_response = UserResponse(
            question_id_original=question_id_original_to_save,
            user_answer_letter=user_choice_letter,
            is_correct=is_correct_answer
        )
        db.session.add(new_response)
        db.session.commit()
        return jsonify({
            "success": True, 
            "message": "Resposta registrada!",
            "is_correct": is_correct_answer,
            "correct_answer_was": correct_letter if (correct_letter and isinstance(correct_letter, str) and correct_letter.strip()) else ""
        })
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao salvar resposta: {e}")
        return jsonify({"success": False, "message": f"Erro ao salvar no banco de dados: {e}"}), 500

@current_app.route('/my_results')
def my_results():
    results_with_question_info = []
    responses = UserResponse.query.order_by(desc(UserResponse.timestamp)).all()

    if ALL_QUESTIONS_DATA:
        questions_dict_by_id = {
            str(q.get('id_original_json')): q for q in ALL_QUESTIONS_DATA if q.get('id_original_json') is not None
        }
        
        for resp in responses:
            question_details = questions_dict_by_id.get(str(resp.question_id_original))
            question_idx_for_url = None
            if question_details:
                try:
                    question_idx_for_url = next(
                        idx for idx, q_data in enumerate(ALL_QUESTIONS_DATA) 
                        if str(q_data.get('id_original_json')) == str(resp.question_id_original)
                    )
                except StopIteration:
                    question_idx_for_url = None

            results_with_question_info.append({
                "response": resp,
                "question_title": question_details.get('titulo_original', 'Título não encontrado') if question_details else f"Detalhes (ID: {resp.question_id_original}) não carregados.",
                "question_url_internal": url_for('show_question', question_idx=question_idx_for_url) if question_idx_for_url is not None else '#',
                "question_url_external": question_details.get('url_original', '#') if question_details else '#'
            })
    return render_template('results.html', results=results_with_question_info)

@current_app.route('/run_scraper')
def run_scraper_route():
    try:
        # Tentativa de importar o scraper_selenium
        # Isso assume que StudyHub_Project está no PYTHONPATH ou o run.py está lá.
        from scraper_selenium import main_scraper # Se scraper_selenium.py está na raiz StudyHub_Project
        
        print("Iniciando o scraping via rota da web...")
        main_scraper() 
        
        # Recarregar questões após o scraping
        # Precisamos de uma função para recarregar, que pode estar em __init__.py ou services.py
        # Por agora, vamos chamar a função load_questions_on_startup do __init__
        # Isso é um pouco hacky, o ideal seria ter uma função em services.py
        from . import load_questions_on_startup
        load_questions_on_startup()

        return f"Scraping concluído! {len(ALL_QUESTIONS_DATA)} questões agora."
    except ImportError:
        return "Erro: Não foi possível importar 'scraper_selenium'. Verifique o caminho.", 500
    except Exception as e:
        return f"Erro ao executar o scraper: {str(e)}", 500