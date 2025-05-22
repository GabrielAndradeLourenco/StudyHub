from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import json
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy

# Configuração do diretório do projeto
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
QUESTIONS_JSON_PATH = os.path.join(PROJECT_ROOT, 'questoes_processadas.json')

# Inicialização do Flask
app = Flask(__name__)
CORS(app)  # Habilita CORS para todas as rotas

# Configuração do banco de dados
instance_path_abs = os.path.join(PROJECT_ROOT, 'instance')
if not os.path.exists(instance_path_abs):
    os.makedirs(instance_path_abs)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(instance_path_abs, 'studyhub.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'studyhub_secret_key'  # Chave fixa para sessões

# Inicializa o banco de dados
db = SQLAlchemy(app)

# Modelos
class TestSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    score_percentage = db.Column(db.Float, nullable=True) 
    total_questions_in_session = db.Column(db.Integer, nullable=True)
    correct_answers_in_session = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(50), nullable=False, default='in_progress') 
    last_question_idx_viewed = db.Column(db.Integer, nullable=True, default=0)
    responses = db.relationship('UserResponse', backref='test_session', lazy=True, cascade="all, delete-orphan")

class UserResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    test_session_id = db.Column(db.Integer, db.ForeignKey('test_session.id'), nullable=False)
    question_id_original = db.Column(db.String(80), nullable=False)
    user_answers_letters_json = db.Column(db.String(50), nullable=False) 
    is_correct = db.Column(db.Boolean, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Carregamento das questões
ALL_QUESTIONS_DATA = []
try:
    with open(QUESTIONS_JSON_PATH, 'r', encoding='utf-8') as f:
        ALL_QUESTIONS_DATA = json.load(f)
    print(f"SUCESSO: Carregadas {len(ALL_QUESTIONS_DATA)} questões de '{QUESTIONS_JSON_PATH}'.")
except FileNotFoundError:
    print(f"AVISO CRÍTICO: Arquivo '{QUESTIONS_JSON_PATH}' NÃO ENCONTRADO. Nenhuma questão carregada.")
except json.JSONDecodeError:
    print(f"AVISO CRÍTICO: Erro ao decodificar JSON de '{QUESTIONS_JSON_PATH}'. Nenhuma questão carregada.")

# Funções auxiliares
def get_or_create_current_test_session():
    # Busca a última sessão em progresso
    current_test_session = TestSession.query.filter_by(status='in_progress').order_by(db.desc(TestSession.timestamp)).first()
    
    if not current_test_session:
        current_test_session = TestSession(
            timestamp=datetime.utcnow(), 
            status='in_progress', 
            last_question_idx_viewed=0
        )
        db.session.add(current_test_session)
        db.session.commit()
    
    return current_test_session

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

# Rotas da API
@app.route('/api/questions/count', methods=['GET'])
def get_questions_count():
    return jsonify(len(ALL_QUESTIONS_DATA))

@app.route('/api/questions/<int:question_idx>', methods=['GET'])
def get_question(question_idx):
    if not (0 <= question_idx < len(ALL_QUESTIONS_DATA)):
        return jsonify({"error": "Índice de questão inválido"}), 404
    
    question = ALL_QUESTIONS_DATA[question_idx]
    
    # Atualiza o índice da última questão visualizada na sessão atual
    current_test_session = get_or_create_current_test_session()
    current_test_session.last_question_idx_viewed = question_idx
    db.session.commit()
    
    return jsonify(question)

@app.route('/api/submit_answer', methods=['POST'])
def submit_answer():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Dados não recebidos."}), 400

    question_id_original = data.get('question_id_original')
    user_choices_letters_list = data.get('chosen_letters')

    current_test_session = get_or_create_current_test_session()

    if not question_id_original or not user_choices_letters_list or not isinstance(user_choices_letters_list, list):
        return jsonify({"success": False, "message": "Dados incompletos ou formato inválido para respostas."}), 400

    # Encontrar a questão nos dados globais usando o ID original
    question_data = next((q for q in ALL_QUESTIONS_DATA if str(q.get('id_original_json')) == str(question_id_original)), None)

    if not question_data:
        return jsonify({"success": False, "message": f"Questão com ID original '{question_id_original}' não encontrada."}), 404

    # Obter o número esperado de respostas para esta questão
    num_answers_expected_by_question = question_data.get('num_answers_to_select', 1)

    if len(user_choices_letters_list) != num_answers_expected_by_question:
        return jsonify({"success": False, "message": f"Você deve selecionar {num_answers_expected_by_question} opção(ões)."}), 400
    
    question_id_original_to_save = str(question_data.get('id_original_json'))

    # Verificar se já existe uma resposta para esta questão nesta sessão
    existing_response = UserResponse.query.filter_by(
        test_session_id=current_test_session.id,
        question_id_original=question_id_original_to_save
    ).first()
    
    if existing_response:
        previous_answers_list_for_json = []
        if existing_response.user_answers_letters_json:
            try:
                previous_answers_list_for_json = json.loads(existing_response.user_answers_letters_json)
            except:
                previous_answers_list_for_json = [existing_response.user_answers_letters_json] if existing_response.user_answers_letters_json else []
        
        return jsonify({
            "success": False,
            "message": "Esta questão já foi respondida nesta sessão.",
            "is_correct": existing_response.is_correct,
            "correct_answer_was": question_data.get('resposta_sugerida_letra', ''),
            "previous_user_answers": previous_answers_list_for_json
        }), 409

    # Lógica de correção para múltiplas respostas
    correct_suggested_answer_str = question_data.get('resposta_sugerida_letra', "")
    is_correct_answer = False

    if correct_suggested_answer_str and isinstance(correct_suggested_answer_str, str) and correct_suggested_answer_str.strip():
        correct_letters_set = set(list(correct_suggested_answer_str.strip()))
        user_choices_set = set(user_choices_letters_list)
        
        if user_choices_set == correct_letters_set and \
           len(user_choices_letters_list) == num_answers_expected_by_question and \
           len(correct_letters_set) == num_answers_expected_by_question:
            is_correct_answer = True

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
        
        return jsonify({
            "success": True,
            "message": "Resposta registrada!",
            "is_correct": is_correct_answer,
            "correct_answer_was": correct_suggested_answer_str
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Erro ao salvar no banco de dados: {str(e)}"}), 500

@app.route('/api/current-session', methods=['GET'])
def get_current_session():
    current_session = get_or_create_current_test_session()
    
    # Verifica se a sessão tem respostas ou se o usuário navegou para alguma questão
    if UserResponse.query.filter_by(test_session_id=current_session.id).count() > 0 or \
       (current_session.last_question_idx_viewed is not None and current_session.last_question_idx_viewed > 0):
        return jsonify({
            'id': current_session.id,
            'timestamp': current_session.timestamp.isoformat(),
            'status': current_session.status,
            'last_question_idx_viewed': current_session.last_question_idx_viewed
        })
    
    return jsonify(None)

@app.route('/api/start-new-study', methods=['POST'])
def start_new_study():
    # Finaliza qualquer sessão em progresso
    existing_session = TestSession.query.filter_by(status='in_progress').first()
    if existing_session:
        if UserResponse.query.filter_by(test_session_id=existing_session.id).count() > 0:
            finalize_session(existing_session.id)
        else:
            existing_session.status = 'abandoned'
            db.session.commit()
    
    # Cria uma nova sessão
    new_session = TestSession(
        timestamp=datetime.utcnow(), 
        status='in_progress', 
        last_question_idx_viewed=0
    )
    db.session.add(new_session)
    db.session.commit()
    
    return jsonify({
        'id': new_session.id,
        'timestamp': new_session.timestamp.isoformat(),
        'status': new_session.status,
        'last_question_idx_viewed': new_session.last_question_idx_viewed
    })

@app.route('/api/resume-study', methods=['GET'])
def resume_study():
    current_session = get_or_create_current_test_session()
    
    return jsonify({
        'id': current_session.id,
        'timestamp': current_session.timestamp.isoformat(),
        'status': current_session.status,
        'last_question_idx_viewed': current_session.last_question_idx_viewed or 0
    })

@app.route('/api/finish-study', methods=['POST'])
def finish_study():
    current_session = get_or_create_current_test_session()
    
    if current_session.status == 'in_progress':
        finalized_session = finalize_session(current_session.id)
        
        if finalized_session:
            return jsonify({
                'id': finalized_session.id,
                'timestamp': finalized_session.timestamp.isoformat(),
                'status': finalized_session.status,
                'score_percentage': finalized_session.score_percentage,
                'total_questions_in_session': finalized_session.total_questions_in_session,
                'correct_answers_in_session': finalized_session.correct_answers_in_session
            })
    
    return jsonify({"error": "Nenhuma sessão em progresso para finalizar"}), 400

@app.route('/api/study-sessions', methods=['GET'])
def get_study_sessions():
    sessions = TestSession.query.order_by(db.desc(TestSession.timestamp)).all()
    
    return jsonify([{
        'id': session.id,
        'timestamp': session.timestamp.isoformat(),
        'status': session.status,
        'score_percentage': session.score_percentage,
        'total_questions_in_session': session.total_questions_in_session,
        'correct_answers_in_session': session.correct_answers_in_session
    } for session in sessions])

@app.route('/api/results/session/<int:session_id>', methods=['GET'])
def get_session_results(session_id):
    session_obj = TestSession.query.get_or_404(session_id)
    responses = UserResponse.query.filter_by(test_session_id=session_id).order_by(UserResponse.timestamp).all()
    
    results = []
    questions_dict_by_id = {
        str(q.get('id_original_json')): q for q in ALL_QUESTIONS_DATA if q.get('id_original_json') is not None
    }
    
    for resp in responses:
        question_details = questions_dict_by_id.get(str(resp.question_id_original))
        question_idx = None
        
        if question_details:
            try:
                question_idx = next(
                    idx for idx, q_data in enumerate(ALL_QUESTIONS_DATA) 
                    if str(q_data.get('id_original_json')) == str(resp.question_id_original)
                )
            except StopIteration:
                pass
        
        user_answers_display = "N/A"
        if resp.user_answers_letters_json:
            try:
                letters_list = json.loads(resp.user_answers_letters_json)
                user_answers_display = ", ".join(letters_list)
            except:
                user_answers_display = resp.user_answers_letters_json
        
        results.append({
            "response_id": resp.id,
            "question_id": resp.question_id_original,
            "question_title": question_details.get('titulo_original', 'Título não encontrado') if question_details else f"Detalhes não carregados",
            "question_idx": question_idx,
            "user_answers": user_answers_display,
            "is_correct": resp.is_correct,
            "timestamp": resp.timestamp.isoformat()
        })
    
    return jsonify({
        "session": {
            'id': session_obj.id,
            'timestamp': session_obj.timestamp.isoformat(),
            'status': session_obj.status,
            'score_percentage': session_obj.score_percentage,
            'total_questions_in_session': session_obj.total_questions_in_session,
            'correct_answers_in_session': session_obj.correct_answers_in_session
        },
        "results": results
    })

@app.route('/api/session/<int:session_id>', methods=['DELETE'])
def delete_session(session_id):
    session_to_delete = TestSession.query.get_or_404(session_id)
    
    db.session.delete(session_to_delete)
    db.session.commit()
    
    return jsonify({"success": True, "message": "Sessão excluída com sucesso"})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5002)