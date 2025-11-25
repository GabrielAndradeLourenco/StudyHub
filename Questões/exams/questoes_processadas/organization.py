#!/usr/bin/env python3
import os
import json
import glob
import re
from collections import defaultdict

def extract_exam_name(title):
    # Extrai apenas o nome do exame, ignorando topic e questão
    # Padrão: "Exam [NOME DO EXAME] topic" ou "Exam [NOME DO EXAME] question"
    match = re.search(r'Exam (.*?) (?:topic|question)', title)
    if match:
        return match.group(1).strip()
    return None

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

def organize_questions_by_exam():
    print("🚀 Iniciando organização de questões por exame...")
    
    exams = defaultdict(dict)
    questions_dir = "questions"
    
    if not os.path.exists(questions_dir):
        print(f"❌ Pasta '{questions_dir}' não encontrada.")
        return
    
    json_files = glob.glob(os.path.join(questions_dir, '*.json'))
    if not json_files:
        print(f"❌ Nenhum arquivo JSON encontrado na pasta '{questions_dir}'.")
        return
        
    print(f"🔍 Encontrados {len(json_files)} arquivos JSON para processar.")
    
    processed_count = 0
    
    for filename in json_files:
        print(f"   ... Processando arquivo: {os.path.basename(filename)}")
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except:
            continue

        links_list = []
        if isinstance(data, dict) and 'links' in data:
            links_list = data['links']
        elif isinstance(data, list):
            links_list = data
        else:
            continue
        
        for item in links_list:
            if not isinstance(item, dict):
                continue
                
            title = item.get('title', '')
            url = item.get('url', '')
            if not title or not url:
                continue
            
            exam_name = extract_exam_name(title)
            if exam_name and url not in exams[exam_name]:
                exams[exam_name][url] = item
                processed_count += 1

    if not exams:
        print("❌ Nenhuma questão foi extraída dos arquivos.")
        return

    print(f"\n✅ Extração concluída! Processadas {processed_count} questões de {len(exams)} exames diferentes.")
    
    output_dir = "exams"
    os.makedirs(output_dir, exist_ok=True)
    print(f"📂 Criando/Verificando a pasta de saída: '{output_dir}'")

    for exam_name, questions_dict in exams.items():
        file_name = sanitize_filename(exam_name) + ".json"
        file_path = os.path.join(output_dir, file_name)
        
        questions_list = list(questions_dict.values())
        print(f"   💾 Salvando {len(questions_list)} questões em '{file_path}'")
        
        exam_data = {
            "exam_name": exam_name,
            "total_questions": len(questions_list),
            "questions": questions_list
        }
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(exam_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"   ❌ Erro ao salvar '{file_path}': {e}")
            
    print("\n🎉 Processo concluído com sucesso!")
    print(f"Todas as questões foram organizadas por exame na pasta '{output_dir}'.")
    
    print("\n📊 Resumo dos exames encontrados:")
    for exam_name, questions_dict in sorted(exams.items()):
        print(f"   • {exam_name}: {len(questions_dict)} questões")

if __name__ == "__main__":
    organize_questions_by_exam()