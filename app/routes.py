from flask import (
    current_app, render_template, url_for, abort, jsonify, request,
    redirect, flash, session as flask_session
)
from sqlalchemy import desc
from . import db, ALL_QUESTIONS_DATA as GLOBAL_APP_QUESTIONS_DATA
from .models import UserResponse, TestSession
import os
from datetime import datetime
import json

def get_or_create_current_test_session():
    test_session_id = flask_session.get('current_test_session_id')
    current_test_session = None

    if test_session_id:
        current_test_session = TestSession.query.get(test_session_id)
        if not current_test_session or current_test_session.status != 'in_progress':
            flask_session.pop('current_test_session_id', None)
            flask_session.pop('questions_in_current_session', None)
            test_session_id = None
            current_test_session = None

    if not test_session_id:
        last_in_progress_db_session = TestSession.query.filter_by(status='in_progress').order_by(desc(TestSession.timestamp)).first()
        
        if last_in_progress_db_session:
            current_test_session = last_in_progress_db_session
            flask_session['current_test_session_id'] = current_test_session.id
            responses_for_session = UserResponse.query.filter_by(test_session_id=current_test_session.id).all()
            flask_session['questions_in_current_session'] = [
                {'id': r.question_id_original, 'correct': r.is_correct} for r in responses_for_session
            ]
            # flash("Sessão em progresso anterior restaurada.", "info") # Removido para evitar spam de flash
        else:
            current_test_session = TestSession(
                timestamp=datetime.utcnow(), 
                status='in_progress', 
                last_question_idx_viewed=0
            )
            db.session.add(current_test_session)
            db.session.commit()
            flask_session['current_test_session_id'] = current_test_session.id
            flask_session['questions_in_current_session'] = []
    
    return current_test_session


@current_app.route('/')
def index():
    num_total_questions = len(GLOBAL_APP_QUESTIONS_DATA)
    in_progress_session = None
    current_session = get_or_create_current_test_session() # Garante que a sessão está ativa ou criada
    if current_session and current_session.status == 'in_progress':
        # Verifica se a sessão tem respostas ou se o usuário navegou para alguma questão
        if UserResponse.query.filter_by(test_session_id=current_session.id).count() > 0 or \
           (current_session.last_question_idx_viewed is not None and current_session.last_question_idx_viewed > 0):
            in_progress_session = current_session
            
    return render_template('index.html', 
                           num_total_questions=num_total_questions,
                           in_progress_session=in_progress_session)


@current_app.route('/start_new_study')
def start_new_study():
    existing_session_id = flask_session.get('current_test_session_id')
    if existing_session_id:
        session_to_close = TestSession.query.get(existing_session_id)
        if session_to_close and session_to_close.status == 'in_progress':
            # Finaliza apenas se houver respostas, senão marca como abandonada
            if UserResponse.query.filter_by(test_session_id=existing_session_id).count() > 0:
                finalize_session(existing_session_id) 
                flash("Sessão de estudo anterior finalizada para iniciar uma nova.", "info")
            else:
                session_to_close.status = 'abandoned'
                session_to_close.score_percentage = 0.0
                session_to_close.total_questions_in_session = 0
                session_to_close.correct_answers_in_session = 0
                db.session.commit()
                flash("Sessão de estudo anterior (sem respostas) marcada como abandonada. Iniciando uma nova.", "info")

    # Limpa a sessão Flask e cria uma nova sessão no DB
    flask_session.pop('current_test_session_id', None)
    flask_session.pop('questions_in_current_session', None)

    if not GLOBAL_APP_QUESTIONS_DATA:
        flash("Nenhuma questão carregada para iniciar o estudo.", "warning")
        return redirect(url_for('index'))
    
    new_session = TestSession(
        timestamp=datetime.utcnow(), 
        status='in_progress', 
        last_question_idx_viewed=0
    )
    db.session.add(new_session)
    db.session.commit()
    flask_session['current_test_session_id'] = new_session.id
    flask_session['questions_in_current_session'] = [] # Inicia o rastreador para a nova sessão

    flash("Novo estudo iniciado!", "success")
    return redirect(url_for('show_question', question_idx=0))

@current_app.route('/resume_study')
def resume_study():
    current_session = get_or_create_current_test_session()

    if not current_session or current_session.status != 'in_progress':
        flash("Nenhuma sessão de estudo em progresso encontrada. Iniciando uma nova.", "info")
        return redirect(url_for('start_new_study'))
    
    last_idx = current_session.last_question_idx_viewed if current_session.last_question_idx_viewed is not None else 0
    flash(f"Continuando estudo da sessão de {current_session.timestamp.strftime('%d/%m/%Y %H:%M')}.", "info")
    return redirect(url_for('show_question', question_idx=last_idx))


@current_app.route('/question/<int:question_idx>')
def show_question(question_idx):
    if not GLOBAL_APP_QUESTIONS_DATA:
        flash("Nenhuma questão carregada.", "error")
        return redirect(url_for('index'))

    current_test_session = get_or_create_current_test_session() # Garante que a sessão está ativa
    
    if not (0 <= question_idx < len(GLOBAL_APP_QUESTIONS_DATA)):
        flash("Índice de questão inválido. Finalizando sessão...", "warning")
        return redirect(url_for('finish_study')) # Ou redirecionar para os resultados da sessão atual

    # Atualiza o índice da última questão visualizada nesta sessão
    current_test_session.last_question_idx_viewed = question_idx
    db.session.commit()

    question = GLOBAL_APP_QUESTIONS_DATA[question_idx]
    previous_response_obj = None
    previous_response_letters_list = None # Para armazenar a lista de letras se já respondida
    
    if 'id_original_json' in question:
        q_id_original = str(question['id_original_json'])
        # Busca a resposta para ESTA questão NESTA sessão
        previous_response_obj = UserResponse.query.filter_by(
            test_session_id=current_test_session.id,
            question_id_original=q_id_original
        ).first()
        if previous_response_obj and previous_response_obj.user_answers_letters_json:
            try:
                previous_response_letters_list = json.loads(previous_response_obj.user_answers_letters_json)
            except json.JSONDecodeError:
                 # Fallback para dados antigos ou malformados
                previous_response_letters_list = [previous_response_obj.user_answers_letters_json] 
        
    return render_template('questao.html',
                           question=question,
                           question_index=question_idx,
                           total_questions=len(GLOBAL_APP_QUESTIONS_DATA),
                           previous_response=previous_response_obj, # Passa o objeto UserResponse inteiro
                           previous_response_letters=previous_response_letters_list, # Lista de letras da resposta anterior
                           current_test_session_id=current_test_session.id)


@current_app.route('/submit_answer', methods=['POST'])
def submit_answer():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Dados não recebidos."}), 400

    question_id_original_from_js = data.get('question_id_original')
    user_choices_letters_list = data.get('chosen_letters') # Espera uma lista de letras

    current_test_session = get_or_create_current_test_session()
    if not current_test_session:
        return jsonify({"success": False, "message": "Sessão de estudo não encontrada."}), 400

    if not question_id_original_from_js or not user_choices_letters_list or not isinstance(user_choices_letters_list, list):
        return jsonify({"success": False, "message": "Dados incompletos ou formato inválido para respostas."}), 400

    # Encontrar a questão nos dados globais usando o ID original
    question_data = next((q for q in GLOBAL_APP_QUESTIONS_DATA if str(q.get('id_original_json')) == str(question_id_original_from_js)), None)

    if not question_data:
        return jsonify({"success": False, "message": f"Questão com ID original '{question_id_original_from_js}' não encontrada."}), 404

    # Obter o número esperado de respostas para esta questão (do JSON processado)
    num_answers_expected_by_question = question_data.get('num_answers_to_select', 1)

    if len(user_choices_letters_list) != num_answers_expected_by_question:
        return jsonify({"success": False, "message": f"Você deve selecionar {num_answers_expected_by_question} opção(ões)."}), 400
    
    question_id_original_to_save = str(question_data.get('id_original_json'))

    # Verificar se já existe uma resposta para esta questão NESTA SESSÃO
    existing_response = UserResponse.query.filter_by(
        test_session_id=current_test_session.id,
        question_id_original=question_id_original_to_save
    ).first()
    if existing_response:
        previous_answers_list_for_json = []
        if existing_response.user_answers_letters_json:
            try:
                previous_answers_list_for_json = json.loads(existing_response.user_answers_letters_json)
            except: # Em caso de erro de parsing, envia string vazia ou o conteúdo bruto
                previous_answers_list_for_json = [existing_response.user_answers_letters_json] if existing_response.user_answers_letters_json else []
        
        return jsonify({
            "success": False,
            "message": "Esta questão já foi respondida nesta sessão.",
            "is_correct": existing_response.is_correct, # A correção da resposta já salva
            "correct_answer_was": question_data.get('resposta_sugerida_letra', ''), # O gabarito da questão
            "previous_user_answers": previous_answers_list_for_json # As letras que o usuário tinha marcado
        }), 409 # Código de conflito

    # Lógica de correção para múltiplas respostas
    correct_suggested_answer_str = question_data.get('resposta_sugerida_letra', "") # Ex: "AD", "A", ou ""
    is_correct_answer = False

    # A resposta só é correta se a string do gabarito não estiver vazia
    if correct_suggested_answer_str and isinstance(correct_suggested_answer_str, str) and correct_suggested_answer_str.strip():
        correct_letters_set = set(list(correct_suggested_answer_str.strip())) # Converte "AD" para {'A', 'D'}
        user_choices_set = set(user_choices_letters_list) # Converte ["A", "D"] para {'A', 'D'}
        
        # Para ser correta, o conjunto de respostas do usuário deve ser IGUAL ao conjunto de respostas corretas
        # E o número de respostas dadas deve ser o esperado pela questão.
        # E o número de letras no gabarito também deve ser o esperado.
        if user_choices_set == correct_letters_set and \
           len(user_choices_letters_list) == num_answers_expected_by_question and \
           len(correct_letters_set) == num_answers_expected_by_question:
            is_correct_answer = True
        elif len(correct_letters_set) != num_answers_expected_by_question and num_answers_expected_by_question > 0 :
            # Loga um aviso se o gabarito tem um número diferente de respostas do que o `num_answers_to_select`
            current_app.logger.warning(f"Discrepância de contagem de respostas para q_id {question_id_original_to_save}: "
                                     f"num_answers_to_select JSON={num_answers_expected_by_question}, "
                                     f"mas gabarito '{correct_suggested_answer_str}' tem {len(correct_letters_set)} letras.")
            # Neste caso, a resposta do usuário é considerada incorreta porque o gabarito é inconsistente.
            is_correct_answer = False
    else: # Se não há resposta sugerida no JSON, não podemos marcar como correta.
        is_correct_answer = False

    try:
        # Salva as respostas do usuário como uma string JSON de uma lista ordenada
        user_answers_json_str = json.dumps(sorted(user_choices_letters_list))
        new_response = UserResponse(
            test_session_id=current_test_session.id,
            question_id_original=question_id_original_to_save,
            user_answers_letters_json=user_answers_json_str,
            is_correct=is_correct_answer
        )
        db.session.add(new_response)
        db.session.commit()

        # Atualiza o rastreador de sessão Flask
        questions_in_session_tracker = flask_session.get('questions_in_current_session', [])
        questions_in_session_tracker.append({'id': question_id_original_to_save, 'correct': is_correct_answer})
        flask_session['questions_in_current_session'] = questions_in_session_tracker
        
        return jsonify({
            "success": True,
            "message": "Resposta registrada!",
            "is_correct": is_correct_answer,
            "correct_answer_was": correct_suggested_answer_str # Envia a string original do gabarito "AD" ou "A"
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao salvar resposta: {e}")
        return jsonify({"success": False, "message": f"Erro ao salvar no banco de dados: {e}"}), 500

def finalize_session(session_id_to_finalize):
    test_session_obj = TestSession.query.get(session_id_to_finalize)
    if test_session_obj:
        # Recalcula baseado apenas nas respostas do DB para esta sessão
        responses_for_session = UserResponse.query.filter_by(test_session_id=session_id_to_finalize).all()
        
        total_answered_in_session = len(responses_for_session)
        correct_in_session = sum(1 for r in responses_for_session if r.is_correct)

        if total_answered_in_session > 0:
            score = (correct_in_session / total_answered_in_session) * 100
            test_session_obj.score_percentage = round(score, 2)
        else:
            test_session_obj.score_percentage = 0.0 
        
        test_session_obj.total_questions_in_session = total_answered_in_session
        test_session_obj.correct_answers_in_session = correct_in_session
        test_session_obj.status = 'completed' # Marca como completada
        db.session.commit()
        return test_session_obj
    return None


@current_app.route('/finish_study')
def finish_study():
    session_id = flask_session.get('current_test_session_id')
    
    if not session_id:
        flash("Nenhuma sessão de estudo ativa para finalizar.", "info")
        return redirect(url_for('my_study_sessions')) # Ou index, se preferir

    finalized_session = finalize_session(session_id)

    # Limpa as variáveis da sessão Flask
    flask_session.pop('current_test_session_id', None)
    flask_session.pop('questions_in_current_session', None)

    if finalized_session:
        if finalized_session.total_questions_in_session > 0:
            flash(f"Estudo finalizado! Seu score: {finalized_session.score_percentage:.2f}% ({finalized_session.correct_answers_in_session}/{finalized_session.total_questions_in_session})", "success")
        else:
            flash("Estudo finalizado, mas nenhuma questão foi respondida nesta sessão.", "info")
        return redirect(url_for('show_session_results', session_id=finalized_session.id))
    else:
        flash("Não foi possível encontrar a sessão de estudo para finalizar.", "error")
        return redirect(url_for('my_study_sessions'))


@current_app.route('/my_study_sessions')
def my_study_sessions():
    sessions = TestSession.query.order_by(desc(TestSession.timestamp)).all()
    current_in_progress_session_id = None
    # Verifica se há uma sessão em progresso no cookie Flask
    flask_session_id = flask_session.get('current_test_session_id')
    if flask_session_id:
        s = TestSession.query.get(flask_session_id)
        if s and s.status == 'in_progress':
            current_in_progress_session_id = s.id

    return render_template('study_sessions_list.html', 
                           sessions=sessions,
                           current_in_progress_session_id=current_in_progress_session_id)


@current_app.route('/results/session/<int:session_id>')
def show_session_results(session_id):
    session_obj = TestSession.query.get_or_404(session_id)
    responses = UserResponse.query.filter_by(test_session_id=session_id).order_by(UserResponse.timestamp).all()
    
    results_with_question_info = []
    if GLOBAL_APP_QUESTIONS_DATA:
        # Criar um dicionário para busca rápida de detalhes da questão pelo ID original
        questions_dict_by_id = {
            str(q.get('id_original_json')): q for q in GLOBAL_APP_QUESTIONS_DATA if q.get('id_original_json') is not None
        }
        
        for resp in responses:
            question_details = questions_dict_by_id.get(str(resp.question_id_original))
            question_idx_for_url = None
            if question_details:
                try:
                    # Encontrar o índice da questão na lista GLOBAL_APP_QUESTIONS_DATA para criar o link de revisão
                    question_idx_for_url = next(
                        idx for idx, q_data in enumerate(GLOBAL_APP_QUESTIONS_DATA) 
                        if str(q_data.get('id_original_json')) == str(resp.question_id_original)
                    )
                except StopIteration:
                    pass # question_idx_for_url permanecerá None

            user_answers_display_str = "N/A"
            if resp.user_answers_letters_json:
                try:
                    letters_list = json.loads(resp.user_answers_letters_json)
                    user_answers_display_str = ", ".join(letters_list)
                except: # Fallback se não for JSON (dados antigos ou erro)
                    user_answers_display_str = resp.user_answers_letters_json


            results_with_question_info.append({
                "response": resp,
                "question_title": question_details.get('titulo_original', 'Título não encontrado') if question_details else f"Detalhes (ID: {resp.question_id_original}) não carregados.",
                "question_url_internal": url_for('show_question_review', question_idx=question_idx_for_url, session_id_context=session_id) if question_idx_for_url is not None else '#',
                "question_url_external": question_details.get('url_original', '#') if question_details else '#',
                "user_answers_display": user_answers_display_str
            })
            
    return render_template('session_results_detail.html', session=session_obj, results=results_with_question_info)

@current_app.route('/review_question/<int:question_idx>/session/<int:session_id_context>')
def show_question_review(question_idx, session_id_context):
    if not GLOBAL_APP_QUESTIONS_DATA or not (0 <= question_idx < len(GLOBAL_APP_QUESTIONS_DATA)):
        abort(404)

    question = GLOBAL_APP_QUESTIONS_DATA[question_idx]
    session_context_obj = TestSession.query.get_or_404(session_id_context)

    # Busca a resposta do usuário para ESTA questão DENTRO DESTA SESSÃO específica
    user_response_in_session_obj = UserResponse.query.filter_by(
        test_session_id=session_id_context,
        question_id_original=str(question.get('id_original_json'))
    ).first()
    
    user_response_letters_list_review = None
    if user_response_in_session_obj and user_response_in_session_obj.user_answers_letters_json:
        try:
            user_response_letters_list_review = json.loads(user_response_in_session_obj.user_answers_letters_json)
        except json.JSONDecodeError:
            user_response_letters_list_review = [user_response_in_session_obj.user_answers_letters_json] # Fallback
            
    return render_template('questao_review.html',
                           question=question,
                           question_index=question_idx,
                           total_questions=len(GLOBAL_APP_QUESTIONS_DATA),
                           user_response_in_session=user_response_in_session_obj, # Objeto UserResponse
                           user_response_letters_review=user_response_letters_list_review, # Lista de letras da resposta
                           session_context=session_context_obj)


@current_app.route('/delete_session/<int:session_id>', methods=['POST'])
def delete_session(session_id):
    session_to_delete = TestSession.query.get(session_id)
    if session_to_delete:
        # Se a sessão a ser excluída é a atual na flask_session, limpa da flask_session
        if flask_session.get('current_test_session_id') == session_id:
            flask_session.pop('current_test_session_id', None)
            flask_session.pop('questions_in_current_session', None)
            
        db.session.delete(session_to_delete) # Isso deve deletar UserResponses em cascata
        db.session.commit()
        flash(f"Sessão de estudo de {session_to_delete.timestamp.strftime('%d/%m/%Y %H:%M')} foi excluída.", "success")
    else:
        flash("Sessão não encontrada para exclusão.", "error")
    return redirect(url_for('my_study_sessions'))


@current_app.route('/run_scraper')
def run_scraper_route():
    try:
        # Tenta importar o scraper_selenium
        # Isso assume que StudyHub_Project está no PYTHONPATH ou o run.py está lá.
        import sys
        # Adiciona o diretório pai (StudyHub_Project) ao sys.path para encontrar scraper_selenium.py
        project_root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
        if project_root_path not in sys.path:
            sys.path.append(project_root_path)
        
        from scraper_selenium import main_scraper # Agora deve encontrar
        
        current_app.logger.info("Iniciando o scraping via rota da web...")
        main_scraper() 
        
        # Recarregar questões após o scraping
        from . import load_questions_on_startup # Importa a função de __init__.py
        load_questions_on_startup() # Chama a função para recarregar ALL_QUESTIONS_DATA

        flash(f"Scraping concluído! {len(GLOBAL_APP_QUESTIONS_DATA)} questões agora estão disponíveis.", "info")
        return redirect(url_for('index'))

    except ImportError as e:
        current_app.logger.error(f"Erro de importação no scraper: {e}")
        flash("Erro: Não foi possível importar 'scraper_selenium'. Verifique o caminho e o PYTHONPATH.", "error")
        return redirect(url_for('index'))
    except Exception as e:
        current_app.logger.error(f"Erro ao executar o scraper: {str(e)}")
        flash(f"Erro ao executar o scraper: {str(e)}", "error")
        return redirect(url_for('index'))