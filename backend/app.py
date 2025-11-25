from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import json
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy

# Configuração do diretório do projeto
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

# Configuração dos simulados disponíveis
AVAILABLE_EXAMS = {
    'machine-learning-specialty': {
        'name': 'AWS Certified Machine Learning - Specialty',
        'file': 'Questões/exams/questoes_processadas/AWS Certified Machine Learning - Specialty_questoes.json'
    },
    'machine-learning-engineer': {
        'name': 'AWS Certified Machine Learning Engineer - Associate MLA-C01',
        'file': 'Questões/exams/questoes_processadas/AWS Certified Machine Learning Engineer - Associate MLA-C01_questoes.json'
    },
    'ai-practitioner': {
        'name': 'AWS Certified AI Practitioner AIF-C01',
        'file': 'Questões/exams/questoes_processadas/AWS Certified AI Practitioner AIF-C01_questoes.json'
    },
    'solutions-architect-associate': {
        'name': 'AWS Certified Solutions Architect - Associate SAA-C03',
        'file': 'Questões/exams/questoes_processadas/AWS Certified Solutions Architect - Associate SAA-C03_questoes.json'
    },
    'solutions-architect-professional': {
        'name': 'AWS Certified Solutions Architect - Professional SAP-C02',
        'file': 'Questões/exams/questoes_processadas/AWS Certified Solutions Architect - Professional SAP-C02_questoes.json'
    },
    'developer-associate': {
        'name': 'AWS Certified Developer - Associate DVA-C02',
        'file': 'Questões/exams/questoes_processadas/AWS Certified Developer - Associate DVA-C02_questoes.json'
    },
    'sysops-administrator': {
        'name': 'AWS Certified SysOps Administrator - Associate',
        'file': 'Questões/exams/questoes_processadas/AWS Certified SysOps Administrator - Associate_questoes.json'
    },
    'cloud-practitioner': {
        'name': 'AWS Certified Cloud Practitioner CLF-C02',
        'file': 'Questões/exams/questoes_processadas/AWS Certified Cloud Practitioner CLF-C02_questoes.json'
    },
    'data-analytics-specialty': {
        'name': 'AWS Certified Data Analytics - Specialty',
        'file': 'Questões/exams/questoes_processadas/AWS Certified Data Analytics - Specialty_questoes.json'
    },
    'data-engineer-associate': {
        'name': 'AWS Certified Data Engineer - Associate DEA-C01',
        'file': 'Questões/exams/questoes_processadas/AWS Certified Data Engineer - Associate DEA-C01_questoes.json'
    },
    'devops-engineer-professional': {
        'name': 'AWS Certified DevOps Engineer - Professional DOP-C02',
        'file': 'Questões/exams/questoes_processadas/AWS Certified DevOps Engineer - Professional DOP-C02_questoes.json'
    },
    'security-specialty': {
        'name': 'AWS Certified Security - Specialty SCS-C02',
        'file': 'Questões/exams/questoes_processadas/AWS Certified Security - Specialty SCS-C02_questoes.json'
    }
}

# Cache para questões carregadas
QUESTIONS_CACHE = {}
# Cache para contagem de questões
QUESTION_COUNT_CACHE = {}

# Inicialização do Flask
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})  # Habilita CORS para todas as rotas da API

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
    exam_type = db.Column(db.String(100), nullable=True)
    responses = db.relationship('UserResponse', backref='test_session', lazy=True, cascade="all, delete-orphan")

class UserResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    test_session_id = db.Column(db.Integer, db.ForeignKey('test_session.id'), nullable=False)
    question_id_original = db.Column(db.String(80), nullable=False)
    user_answers_letters_json = db.Column(db.String(50), nullable=False) 
    is_correct = db.Column(db.Boolean, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

def load_questions_for_exam(exam_type):
    """Carrega questões para um tipo específico de exame"""
    if exam_type in QUESTIONS_CACHE:
        return QUESTIONS_CACHE[exam_type]
    
    if exam_type not in AVAILABLE_EXAMS:
        return []
    
    file_path = os.path.join(PROJECT_ROOT, AVAILABLE_EXAMS[exam_type]['file'])
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            all_questions = json.load(f)
        
        # Filtrar questões com erro
        questions = [q for q in all_questions if 'error' not in q and len(q.get('opcoes', [])) > 0]
        
        QUESTIONS_CACHE[exam_type] = questions
        print(f"SUCESSO: Carregadas {len(questions)} questões válidas para {exam_type} (de {len(all_questions)} totais)")
        return questions
    except FileNotFoundError:
        print(f"AVISO: Arquivo não encontrado para {exam_type}: {file_path}")
        return []
    except json.JSONDecodeError:
        print(f"AVISO: Erro ao decodificar JSON para {exam_type}")
        return []

# Funções auxiliares
def get_or_create_current_test_session(exam_type):
    current_test_session = TestSession.query.filter_by(
        status='in_progress', 
        exam_type=exam_type
    ).order_by(db.desc(TestSession.timestamp)).first()
    
    if not current_test_session:
        current_test_session = TestSession(
            timestamp=datetime.utcnow(), 
            status='in_progress', 
            last_question_idx_viewed=0,
            exam_type=exam_type
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
@app.route('/api/exams', methods=['GET'])
def get_available_exams():
    """Retorna lista de simulados disponíveis"""
    exams = []
    for exam_id, exam_info in AVAILABLE_EXAMS.items():
        # Usar cache para contagem
        if exam_id in QUESTION_COUNT_CACHE:
            count = QUESTION_COUNT_CACHE[exam_id]
        else:
            questions = load_questions_for_exam(exam_id)
            count = len(questions)
            QUESTION_COUNT_CACHE[exam_id] = count
            
        exams.append({
            'id': exam_id,
            'name': exam_info['name'],
            'question_count': count
        })
    
    response = jsonify(exams)
    response.headers['Cache-Control'] = 'public, max-age=3600'  # Cache por 1 hora
    return response

@app.route('/api/questions/count', methods=['GET'])
def get_questions_count():
    exam_type = request.args.get('exam_type')
    if not exam_type:
        return jsonify({"error": "exam_type é obrigatório"}), 400
    
    # Usar cache para contagem
    if exam_type in QUESTION_COUNT_CACHE:
        return jsonify(QUESTION_COUNT_CACHE[exam_type])
    
    questions = load_questions_for_exam(exam_type)
    count = len(questions)
    QUESTION_COUNT_CACHE[exam_type] = count
    return jsonify(count)

@app.route('/api/questions/<int:question_idx>', methods=['GET'])
def get_question(question_idx):
    exam_type = request.args.get('exam_type')
    if not exam_type:
        return jsonify({"error": "exam_type é obrigatório"}), 400
    questions = load_questions_for_exam(exam_type)
    
    if not (0 <= question_idx < len(questions)):
        return jsonify({"error": "Índice de questão inválido"}), 404
    
    question = questions[question_idx]
    
    current_test_session = get_or_create_current_test_session(exam_type)
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
    exam_type = data.get('exam_type')
    if not exam_type:
        return jsonify({"success": False, "message": "exam_type é obrigatório"}), 400

    current_test_session = get_or_create_current_test_session(exam_type)
    questions = load_questions_for_exam(exam_type)

    if not question_id_original or not user_choices_letters_list or not isinstance(user_choices_letters_list, list):
        return jsonify({"success": False, "message": "Dados incompletos ou formato inválido para respostas."}), 400

    question_data = next((q for q in questions if str(q.get('id_original_json')) == str(question_id_original)), None)

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
    exam_type = request.args.get('exam_type')
    if not exam_type:
        return jsonify({"error": "exam_type é obrigatório"}), 400
    current_session = get_or_create_current_test_session(exam_type)
    
    if UserResponse.query.filter_by(test_session_id=current_session.id).count() > 0 or \
       (current_session.last_question_idx_viewed is not None and current_session.last_question_idx_viewed > 0):
        return jsonify({
            'id': current_session.id,
            'timestamp': current_session.timestamp.isoformat(),
            'status': current_session.status,
            'last_question_idx_viewed': current_session.last_question_idx_viewed,
            'exam_type': current_session.exam_type
        })
    
    return jsonify(None)

@app.route('/api/start-new-study', methods=['POST'])
def start_new_study():
    data = request.get_json()
    start_question_idx = data.get('start_question_idx', 0) if data else 0
    exam_type = data.get('exam_type') if data else None
    if not exam_type:
        return jsonify({"error": "exam_type é obrigatório"}), 400
    
    questions = load_questions_for_exam(exam_type)
    if not (0 <= start_question_idx < len(questions)):
        return jsonify({"error": "Índice de questão inválido"}), 400
    
    existing_session = TestSession.query.filter_by(status='in_progress', exam_type=exam_type).first()
    if existing_session:
        if UserResponse.query.filter_by(test_session_id=existing_session.id).count() > 0:
            finalize_session(existing_session.id)
        else:
            existing_session.status = 'abandoned'
            db.session.commit()
    
    new_session = TestSession(
        timestamp=datetime.utcnow(), 
        status='in_progress', 
        last_question_idx_viewed=start_question_idx,
        exam_type=exam_type
    )
    db.session.add(new_session)
    db.session.commit()
    
    return jsonify({
        'id': new_session.id,
        'timestamp': new_session.timestamp.isoformat(),
        'status': new_session.status,
        'last_question_idx_viewed': new_session.last_question_idx_viewed,
        'exam_type': new_session.exam_type
    })

@app.route('/api/resume-study', methods=['GET'])
def resume_study():
    exam_type = request.args.get('exam_type')
    if not exam_type:
        return jsonify({"error": "exam_type é obrigatório"}), 400
    current_session = get_or_create_current_test_session(exam_type)
    
    return jsonify({
        'id': current_session.id,
        'timestamp': current_session.timestamp.isoformat(),
        'status': current_session.status,
        'last_question_idx_viewed': current_session.last_question_idx_viewed or 0,
        'exam_type': current_session.exam_type
    })

@app.route('/api/finish-study', methods=['POST'])
def finish_study():
    data = request.get_json()
    exam_type = data.get('exam_type') if data else None
    if not exam_type:
        return jsonify({"error": "exam_type é obrigatório"}), 400
    current_session = get_or_create_current_test_session(exam_type)
    
    if current_session.status == 'in_progress':
        finalized_session = finalize_session(current_session.id)
        
        if finalized_session:
            return jsonify({
                'id': finalized_session.id,
                'timestamp': finalized_session.timestamp.isoformat(),
                'status': finalized_session.status,
                'score_percentage': finalized_session.score_percentage,
                'total_questions_in_session': finalized_session.total_questions_in_session,
                'correct_answers_in_session': finalized_session.correct_answers_in_session,
                'exam_type': finalized_session.exam_type
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
        'correct_answers_in_session': session.correct_answers_in_session,
        'exam_type': session.exam_type
    } for session in sessions])

@app.route('/api/results/session/<int:session_id>', methods=['GET'])
def get_session_results(session_id):
    session_obj = TestSession.query.get_or_404(session_id)
    responses = UserResponse.query.filter_by(test_session_id=session_id).order_by(UserResponse.timestamp).all()
    
    exam_type = session_obj.exam_type
    questions = load_questions_for_exam(exam_type)
    
    results = []
    questions_dict_by_id = {
        str(q.get('id_original_json')): q for q in questions if q.get('id_original_json') is not None
    }
    
    for resp in responses:
        question_details = questions_dict_by_id.get(str(resp.question_id_original))
        question_idx = None
        
        if question_details:
            try:
                question_idx = next(
                    idx for idx, q_data in enumerate(questions) 
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
            'correct_answers_in_session': session_obj.correct_answers_in_session,
            'exam_type': session_obj.exam_type
        },
        "results": results
    })

@app.route('/api/session/<int:session_id>', methods=['DELETE'])
def delete_session(session_id):
    session_to_delete = TestSession.query.get_or_404(session_id)
    
    db.session.delete(session_to_delete)
    db.session.commit()
    
    return jsonify({"success": True, "message": "Sessão excluída com sucesso"})

@app.route('/')
def index():
    return jsonify({
        "message": "StudyHub API está funcionando!",
        "endpoints": [
            "/api/exams",
            "/api/questions/count",
            "/api/questions/<question_idx>",
            "/api/current-session",
            "/api/start-new-study",
            "/api/resume-study",
            "/api/finish-study",
            "/api/study-sessions",
            "/api/results/session/<session_id>",
            "/api/session/<session_id>"
        ]
    })


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5002))
    with app.app_context():
        db.create_all()
    app.run(debug=False, host='0.0.0.0', port=port)