#!/usr/bin/env python3
"""
Script para filtrar questões específicas do questoes_base.json
e organizar por exame em pastas separadas
"""

import os
import json
import re
from collections import defaultdict

# --- CONFIGURAÇÕES ---
INPUT_FILE = "../questoes_base.json"  # Arquivo na raiz do projeto
OUTPUT_BASE_DIR = "../Questões/exams"  # Diretório base de saída

# Exames que você quer filtrar (palavras-chave no título)
EXAMES_FILTRAR = [
    "Generative AI Developer - Professional AIP-C01",
    "AI Practitioner AIF-C01", 
    "Data Engineer - Associate DEA-C01"
]
# --- FIM CONFIGURAÇÕES ---

def extract_exam_name(title):
    """Extrai o nome do exame do título"""
    # Padrão: "Exam [NOME DO EXAME] topic X question Y discussion"
    match = re.search(r'Exam (.*?) topic', title, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None

def sanitize_filename(name):
    """Remove caracteres inválidos do nome do arquivo"""
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

def should_include_exam(exam_name):
    """Verifica se o exame deve ser incluído baseado nos filtros"""
    if not EXAMES_FILTRAR:
        return True  # Se não há filtros, inclui todos
    
    for filtro in EXAMES_FILTRAR:
        if filtro.lower() in exam_name.lower():
            return True
    return False

def organize_questions():
    print("="*70)
    print("🎯 FILTRO E ORGANIZAÇÃO DE QUESTÕES POR EXAME")
    print("="*70)
    
    # Verificar se arquivo de entrada existe
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(script_dir, INPUT_FILE)
    
    if not os.path.exists(input_path):
        print(f"❌ Arquivo '{INPUT_FILE}' não encontrado em: {input_path}")
        return
    
    print(f"📂 Lendo arquivo: {input_path}")
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            all_questions = json.load(f)
    except Exception as e:
        print(f"❌ Erro ao ler arquivo: {e}")
        return
    
    print(f"📊 Total de questões no arquivo: {len(all_questions)}")
    
    if EXAMES_FILTRAR:
        print(f"\n🔍 Filtrando apenas os exames:")
        for filtro in EXAMES_FILTRAR:
            print(f"   • {filtro}")
    else:
        print("\n📋 Organizando TODOS os exames encontrados")
    
    # Agrupar questões por exame
    exams = defaultdict(list)
    
    for question in all_questions:
        title = question.get('title', '')
        exam_name = extract_exam_name(title)
        
        if exam_name and should_include_exam(exam_name):
            exams[exam_name].append(question)
    
    if not exams:
        print("\n❌ Nenhuma questão encontrada para os exames filtrados.")
        return
    
    print(f"\n✅ Encontrados {len(exams)} exames:")
    for exam_name, questions in sorted(exams.items()):
        print(f"   • {exam_name}: {len(questions)} questões")
    
    # Criar estrutura de diretórios
    output_base = os.path.join(script_dir, OUTPUT_BASE_DIR)
    os.makedirs(output_base, exist_ok=True)
    
    print(f"\n📁 Salvando arquivos em: {output_base}")
    
    # Salvar cada exame em arquivo separado
    for exam_name, questions in exams.items():
        # Ordenar questões por question_id
        questions_sorted = sorted(questions, key=lambda x: int(x.get('question_id', 0)))
        
        filename = sanitize_filename(exam_name) + ".json"
        filepath = os.path.join(output_base, filename)
        
        exam_data = {
            "exam_name": exam_name,
            "total_questions": len(questions_sorted),
            "questions": questions_sorted
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(exam_data, f, indent=2, ensure_ascii=False)
            print(f"   ✅ {filename} - {len(questions_sorted)} questões")
        except Exception as e:
            print(f"   ❌ Erro ao salvar '{filename}': {e}")
    
    print("\n" + "="*70)
    print("🎉 ORGANIZAÇÃO CONCLUÍDA!")
    print("="*70)
    print(f"📂 Arquivos salvos em: {output_base}")
    print("="*70)

if __name__ == "__main__":
    organize_questions()
