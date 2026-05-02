#!/usr/bin/env python3
"""
Script para processar as questões do Generative AI Developer Professional
a partir do arquivo data/questoes_base_generative_ai.json
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import json
import time
import re
import os

# --- CONFIGURAÇÕES ---
USE_HEADLESS_BROWSER = True
INPUT_FILE = "../data/questoes_base_generative_ai.json"
OUTPUT_FILE = "../data/questoes_genai_processadas.json"
PROGRESS_FILE = "../data/questoes_base_generative_ai_progress.txt"
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
        
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        print(f"❌ ERRO ao configurar o driver Selenium: {e}")
        return None

def extract_question_data_from_page(driver, url_info, question_index_overall):
    print(f"  Processando URL: {url_info['url']}")
    driver.get(url_info['url'])
    
    time.sleep(0.3) 
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

    # Extração da resposta sugerida
    resposta_sugerida_letras_raw_list = []
    max_percentage_overall = -1

    vote_distribution_bar = main_question_container.find('div', class_='vote-distribution-bar')
    if not vote_distribution_bar and question_text_p:
         vote_distribution_bar = question_text_p.find_next_sibling('div', class_='vote-distribution-bar')
    if not vote_distribution_bar:
        choices_container_temp = main_question_container.find('div', class_='question-choices-container')
        if choices_container_temp:
            vote_distribution_bar = choices_container_temp.find_next_sibling('div', class_='vote-distribution-bar')
            if not vote_distribution_bar:
                 vote_distribution_bar = choices_container_temp.find('div', class_='vote-distribution-bar')

    if vote_distribution_bar:
        vote_bars = vote_distribution_bar.find_all('div', class_='vote-bar')
        
        multi_letter_pattern = re.compile(r"([A-Z]{2,})\s*\((\d+)%\)") 
        single_letter_pattern = re.compile(r"^([A-Z])\s*\((\d+)%\)")
        visible_letter_only_pattern = re.compile(r"^\s*([A-Z])\s*$")

        best_multi_choice_letters_str = ""
        best_multi_choice_percentage = -1
        
        for bar in vote_bars:
            bar_text = bar.get_text(strip=True)
            multi_match = multi_letter_pattern.search(bar_text)
            if multi_match:
                letters_group_str = multi_match.group(1)
                percentage_group = int(multi_match.group(2))
                if percentage_group > best_multi_choice_percentage:
                    best_multi_choice_letters_str = letters_group_str
                    best_multi_choice_percentage = percentage_group
        
        if best_multi_choice_letters_str:
            resposta_sugerida_letras_raw_list = list(best_multi_choice_letters_str)
        else:
            single_best_letter = None
            visible_bar_letter_candidate = None
            
            for bar in vote_bars:
                bar_text = bar.get_text(strip=True)
                single_match = single_letter_pattern.search(bar_text)
                if single_match:
                    letter = single_match.group(1)
                    percentage = int(single_match.group(2))
                    if percentage > max_percentage_overall:
                        max_percentage_overall = percentage
                        single_best_letter = letter
                elif 'style' in bar.attrs and \
                     ('display:flex' in bar.attrs['style'].replace(' ', '') or \
                      'display: flex' in bar.attrs['style'].replace(' ', '')):
                    letter_only_match = visible_letter_only_pattern.match(bar_text)
                    if letter_only_match and not visible_bar_letter_candidate:
                        visible_bar_letter_candidate = letter_only_match.group(1)
            
            if single_best_letter:
                resposta_sugerida_letras_raw_list = [single_best_letter]
            elif visible_bar_letter_candidate:
                resposta_sugerida_letras_raw_list = [visible_bar_letter_candidate]

    final_resposta_sugerida_str = "".join(sorted(list(set(resposta_sugerida_letras_raw_list))))
    
    if final_resposta_sugerida_str:
        print(f"    Resposta sugerida: '{final_resposta_sugerida_str}'")
    else:
        print(f"    Resposta sugerida não encontrada")

    num_opcoes = len(opcoes_lista)
    num_answers_to_select = 1

    if final_resposta_sugerida_str:
        num_answers_to_select = len(final_resposta_sugerida_str)
        if num_answers_to_select == 0:
            num_answers_to_select = 1 
    else: 
        if num_opcoes == 5:
            num_answers_to_select = 2
        elif num_opcoes == 6:
            num_answers_to_select = 3
    
    print(f"    Opções: {num_opcoes}, Respostas a selecionar: {num_answers_to_select}")

    return {
        "id_original_json": url_info.get('question_id', str(question_index_overall)),
        "url_original": url_info['url'],
        "titulo_original": url_info.get('title', "N/A"),
        "enunciado_html": enunciado_html_str,
        "opcoes": opcoes_lista,
        "resposta_sugerida_letra": final_resposta_sugerida_str,
        "num_answers_to_select": num_answers_to_select
    }

def main():
    print("="*70)
    print("🎯 PROCESSAMENTO - AWS Generative AI Developer Professional")
    print("="*70)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(script_dir, INPUT_FILE)
    output_path = os.path.join(script_dir, OUTPUT_FILE)
    progress_path = os.path.join(script_dir, PROGRESS_FILE)
    
    # Carregar questões base
    if not os.path.exists(input_path):
        print(f"❌ Arquivo não encontrado: {input_path}")
        return
    
    with open(input_path, 'r', encoding='utf-8') as f:
        questions_base = json.load(f)
    
    print(f"📝 Total de questões no arquivo base: {len(questions_base)}")
    
    # Carregar progresso anterior
    processed_questions = []
    if os.path.exists(output_path):
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                processed_questions = json.load(f)
            print(f"📂 Encontrado progresso anterior: {len(processed_questions)} questões processadas")
        except:
            processed_questions = []
    
    processed_ids = {q.get('id_original_json') for q in processed_questions}
    
    # Ordenar questões por ID
    questions_sorted = sorted(questions_base, key=lambda x: int(x.get('question_id', 0)))
    
    # Contar quantas faltam
    remaining = [q for q in questions_sorted if q.get('question_id') not in processed_ids]
    print(f"📊 Questões restantes para processar: {len(remaining)}")
    
    if len(remaining) == 0:
        print("✅ Todas as questões já foram processadas!")
        return
    
    # Setup do driver
    driver = setup_driver()
    if not driver:
        return
    
    try:
        for i, question in enumerate(questions_sorted):
            question_id = question.get('question_id', str(i))
            
            if question_id in processed_ids:
                continue
            
            print(f"\n   Questão {question_id} ({len(processed_questions)+1}/{len(questions_sorted)})...")
            
            url_info = {
                'url': question.get('url', ''),
                'title': question.get('title', ''),
                'question_id': question_id
            }
            
            try:
                question_data = extract_question_data_from_page(driver, url_info, i)
                processed_questions.append(question_data)
            except Exception as e:
                print(f"   ❌ Erro: {e}")
                processed_questions.append({
                    "id_original_json": question_id,
                    "url_original": question.get('url', ''),
                    "titulo_original": question.get('title', ''),
                    "enunciado_html": f"<p>Erro ao extrair: {e}</p>",
                    "opcoes": [],
                    "resposta_sugerida_letra": "",
                    "num_answers_to_select": 1,
                    "error": str(e)
                })
            
            # Salvar progresso
            try:
                processed_sorted = sorted(processed_questions, key=lambda x: int(x.get('id_original_json', '0')))
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(processed_sorted, f, indent=4, ensure_ascii=False)
                
                # Salvar índice de progresso
                with open(progress_path, 'w') as f:
                    f.write(str(len(processed_questions)))
                    
                print(f"   💾 Progresso salvo: {len(processed_questions)} questões")
            except Exception as e:
                print(f"   ⚠️  Erro ao salvar: {e}")
        
        print(f"\n✅ Processamento completo: {len(processed_questions)} questões")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrompido pelo usuário")
        print("💾 Progresso foi salvo automaticamente")
    
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
    
    finally:
        if driver:
            driver.quit()
            print("🔒 Driver fechado")

if __name__ == "__main__":
    main()
