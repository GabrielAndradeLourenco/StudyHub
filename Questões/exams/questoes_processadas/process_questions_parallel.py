#!/usr/bin/env python3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from bs4 import BeautifulSoup
import json
import time
import random
import re
import os
import glob
from multiprocessing import Pool, cpu_count
import concurrent.futures

# --- CONFIGURAÇÕES ---
SELENIUM_TIMEOUT = 10
DRIVER_PATH = None 
USE_HEADLESS_BROWSER = True
MAX_WORKERS = min(4, cpu_count())  # Máximo 4 processos paralelos
# --- FIM CONFIGURAÇÕES ---

def setup_driver():
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("start-maximized")
        options.add_argument("disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument('--log-level=3')
        if USE_HEADLESS_BROWSER:
            options.add_argument('--headless')
        
        if DRIVER_PATH:
            service = webdriver.ChromeService(executable_path=DRIVER_PATH)
            driver = webdriver.Chrome(service=service, options=options)
        else:
            driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        print(f"ERRO ao configurar o driver Selenium: {e}")
        return None

def extract_question_id(title):
    """Extrai o ID da questão do título"""
    match = re.search(r'question (\d+)', title)
    return match.group(1) if match else "1"

def extract_question_data_from_page(driver, url_info, question_index_overall):
    driver.get(url_info['url'])
    time.sleep(0.2) 
    page_html = driver.page_source
    soup = BeautifulSoup(page_html, 'html.parser')

    main_question_container = soup.find('div', class_='question-body')
    if not main_question_container:
        main_question_container = soup.find('div', class_='discussion-question-body')
    if not main_question_container:
        main_question_container = soup

    enunciado_html_str = ""
    question_text_p = main_question_container.find('p', class_='card-text')
    if question_text_p:
        temp_enunciado_soup = BeautifulSoup(str(question_text_p), 'html.parser')
        for tag in temp_enunciado_soup.find_all(True):
            if tag.name == 'img':
                tag.attrs = {k:v for k,v in tag.attrs.items() if k in ['src', 'alt', 'class']}
                style_attr = tag.attrs.get('style', '')
                if 'max-width:100%' not in style_attr: style_attr += ';max-width:100%;'
                if 'height:auto' not in style_attr: style_attr += ';height:auto;'
                tag.attrs['style'] = style_attr.strip(';')
                if 'src' in tag.attrs and tag['src'].startswith('/assets/'):
                    tag['src'] = 'https://www.examtopics.com' + tag['src']
            elif tag.name == 'pre':
                pass
            else: 
                tag.attrs = {}
        enunciado_html_str = str(temp_enunciado_soup.find('p'))
    else:
        enunciado_html_str = "<p><em>Enunciado não encontrado.</em></p>"

    opcoes_lista = []
    options_choices_container = main_question_container.find('div', class_='question-choices-container')
    if options_choices_container:
        options_ul_element = options_choices_container.find('ul')
        if options_ul_element:
            list_items = options_ul_element.find_all('li', class_='multi-choice-item')
            for item_li in list_items:
                temp_item_li = BeautifulSoup(str(item_li), 'html.parser').li
                letter_span = temp_item_li.find('span', class_='multi-choice-letter')
                option_letter_cleaned = ""
                option_letter_raw = ""

                if letter_span:
                    option_letter_raw = letter_span.get_text(strip=True)
                    option_letter_cleaned = option_letter_raw.replace('.', '').strip()
                    letter_span.decompose()
                
                for unwanted_class in ['most-voted-answer-badge', 'badge', 'discussion-link-title', 'vote-count']:
                    for unwanted_span in temp_item_li.find_all('span', class_=unwanted_class):
                        unwanted_span.decompose()
                for unwanted_div_class in ['voting-bar', 'progress']:
                     for unwanted_div in temp_item_li.find_all('div', class_=unwanted_div_class):
                        unwanted_div.decompose()
                for unwanted_a_class in ['btn', 'reveal-solution']:
                    for unwanted_a in temp_item_li.find_all('a', class_=unwanted_a_class):
                        unwanted_a.decompose()
                
                option_text_cleaned = temp_item_li.get_text(strip=True)
                if option_letter_cleaned and option_text_cleaned:
                    opcoes_lista.append({
                        "letra_raw": option_letter_raw,
                        "letra": option_letter_cleaned,
                        "texto": option_text_cleaned
                    })

    # Extração simplificada da resposta sugerida
    resposta_sugerida_letras_raw_list = []
    vote_distribution_bar = main_question_container.find('div', class_='vote-distribution-bar')
    if vote_distribution_bar:
        vote_bars = vote_distribution_bar.find_all('div', class_='vote-bar')
        multi_letter_pattern = re.compile(r"([A-Z]{2,})\s*\((\d+)%\)") 
        single_letter_pattern = re.compile(r"^([A-Z])\s*\((\d+)%\)")
        
        best_percentage = -1
        best_answer = ""
        
        for bar in vote_bars:
            bar_text = bar.get_text(strip=True)
            multi_match = multi_letter_pattern.search(bar_text)
            single_match = single_letter_pattern.search(bar_text)
            
            if multi_match:
                percentage = int(multi_match.group(2))
                if percentage > best_percentage:
                    best_percentage = percentage
                    best_answer = multi_match.group(1)
            elif single_match:
                percentage = int(single_match.group(2))
                if percentage > best_percentage:
                    best_percentage = percentage
                    best_answer = single_match.group(1)

    final_resposta_sugerida_str = best_answer
    
    # Determinar num_answers_to_select
    num_opcoes = len(opcoes_lista)
    num_answers_to_select = len(final_resposta_sugerida_str) if final_resposta_sugerida_str else 1
    if num_answers_to_select == 0:
        num_answers_to_select = 1

    return {
        "id_original_json": url_info.get('question_id', str(question_index_overall)),
        "url_original": url_info['url'],
        "titulo_original": url_info.get('title', "N/A"),
        "enunciado_html": enunciado_html_str,
        "opcoes": opcoes_lista,
        "resposta_sugerida_letra": final_resposta_sugerida_str,
        "num_answers_to_select": num_answers_to_select
    }

def process_single_exam_file(filename):
    """Processa um único arquivo de exame"""
    print(f"🚀 Iniciando processamento de: {os.path.basename(filename)}")
    
    # Setup do driver para este processo
    driver = setup_driver()
    if not driver:
        print(f"❌ Erro ao configurar driver para {filename}")
        return
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            exam_data = json.load(f)
    except Exception as e:
        print(f"❌ Erro ao ler '{filename}': {e}")
        return
    
    exam_name = exam_data.get('exam_name', '')
    questions = exam_data.get('questions', [])
    
    if not questions:
        print(f"⚠️ Nenhuma questão encontrada em '{filename}'")
        return
    
    # Ordenar questões
    questions_with_order = []
    for question in questions:
        question_id = extract_question_id(question.get('title', ''))
        questions_with_order.append((int(question_id), question))
    questions_with_order.sort(key=lambda x: x[0])
    
    # Arquivo de saída
    output_filename = os.path.basename(filename).replace('.json', '_questoes.json')
    
    # Verificar progresso existente
    processed_questions = []
    if os.path.exists(output_filename):
        try:
            with open(output_filename, 'r', encoding='utf-8') as f:
                processed_questions = json.load(f)
            print(f"📂 {len(processed_questions)} questões já processadas em {output_filename}")
        except:
            processed_questions = []
    
    processed_ids = {q.get('id_original_json') for q in processed_questions}
    
    try:
        for i, (order_num, question) in enumerate(questions_with_order):
            question_id = str(order_num)
            
            if question_id in processed_ids:
                continue
            
            print(f"📝 {os.path.basename(filename)} - Questão {question_id} ({len(processed_questions)+1}/{len(questions_with_order)})")
            
            url_info = {
                'url': question.get('url', ''),
                'title': question.get('title', ''),
                'question_id': question_id
            }
            
            try:
                question_data = extract_question_data_from_page(driver, url_info, i)
                processed_questions.append(question_data)
            except Exception as e:
                print(f"❌ Erro na questão {order_num}: {e}")
                processed_questions.append({
                    "id_original_json": question_id,
                    "url_original": question.get('url', ''),
                    "titulo_original": question.get('title', ''),
                    "enunciado_html": f"<p>Erro: {e}</p>",
                    "opcoes": [],
                    "resposta_sugerida_letra": "",
                    "num_answers_to_select": 1,
                    "error": str(e)
                })
            
            # Salvar progresso
            try:
                processed_questions_sorted = sorted(processed_questions, key=lambda x: int(x.get('id_original_json', '0')))
                with open(output_filename, 'w', encoding='utf-8') as f:
                    json.dump(processed_questions_sorted, f, indent=4, ensure_ascii=False)
            except Exception as e:
                print(f"⚠️ Erro ao salvar: {e}")
        
        print(f"✅ {os.path.basename(filename)} concluído: {len(processed_questions)} questões")
    
    finally:
        driver.quit()

def process_exam_questions_parallel():
    """Processa todos os arquivos em paralelo"""
    print("🚀 Iniciando processamento PARALELO de questões...")
    
    exams_dir = "../"
    json_files = glob.glob(os.path.join(exams_dir, '*.json'))
    
    if not json_files:
        print("❌ Nenhum arquivo encontrado")
        return
    
    print(f"🔍 Encontrados {len(json_files)} arquivos")
    print(f"⚡ Usando {MAX_WORKERS} processos paralelos")
    
    # Processar em paralelo
    with concurrent.futures.ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_single_exam_file, filename) for filename in json_files]
        
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"❌ Erro em processo: {e}")
    
    print("🎉 Processamento paralelo concluído!")

if __name__ == "__main__":
    process_exam_questions_parallel()