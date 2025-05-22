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

# --- CONFIGURAÇÕES ---
INPUT_JSON_URLS_FILE = 'questoes_base.json'
OUTPUT_PROCESSED_QUESTIONS_FILE = 'questoes_processadas.json'
MIN_DELAY_SECONDS = 2
MAX_DELAY_SECONDS = 5
SELENIUM_TIMEOUT = 10
DRIVER_PATH = None 
USE_HEADLESS_BROWSER = True
MAX_QUESTIONS_TO_SCRAPE_FOR_TESTING = None 
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

def extract_question_data_from_page(driver, url_info, question_index_overall):
    print(f"  Processando URL: {url_info['url']}")
    driver.get(url_info['url'])
    
    time.sleep(1) 
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
    if not vote_distribution_bar: # Tenta mais uma vez dentro do choices_container
        choices_container_temp = main_question_container.find('div', class_='question-choices-container')
        if choices_container_temp:
            vote_distribution_bar = choices_container_temp.find_next_sibling('div', class_='vote-distribution-bar')
            if not vote_distribution_bar: # Última tentativa dentro do choices_container se não for sibling
                 vote_distribution_bar = choices_container_temp.find('div', class_='vote-distribution-bar')


    if vote_distribution_bar:
        vote_bars = vote_distribution_bar.find_all('div', class_='vote-bar')
        
        # Padrão para múltiplas letras (ex: "AD (75%)", "BCE (60%)")
        multi_letter_pattern = re.compile(r"([A-Z]{2,})\s*\((\d+)%\)") 
        # Padrão para letra única (ex: "A (75%)")
        single_letter_pattern = re.compile(r"^([A-Z])\s*\((\d+)%\)")
        # Padrão para letra única visível sem porcentagem (ex: "A")
        visible_letter_only_pattern = re.compile(r"^\s*([A-Z])\s*$")

        # Prioridade 1: Barra com múltiplas letras e porcentagem
        best_multi_choice_letters_str = ""
        best_multi_choice_percentage = -1
        
        for bar in vote_bars:
            bar_text = bar.get_text(strip=True)
            multi_match = multi_letter_pattern.search(bar_text)
            if multi_match:
                letters_group_str = multi_match.group(1) # Ex: "AD"
                percentage_group = int(multi_match.group(2))
                if percentage_group > best_multi_choice_percentage:
                    best_multi_choice_letters_str = letters_group_str
                    best_multi_choice_percentage = percentage_group
        
        if best_multi_choice_letters_str:
            resposta_sugerida_letras_raw_list = list(best_multi_choice_letters_str)
        else:
            # Prioridade 2: Barra com letra única e maior porcentagem
            single_best_letter = None
            visible_bar_letter_candidate = None # Para barras visíveis sem %
            
            for bar in vote_bars:
                bar_text = bar.get_text(strip=True)
                single_match = single_letter_pattern.search(bar_text)
                if single_match:
                    letter = single_match.group(1)
                    percentage = int(single_match.group(2))
                    if percentage > max_percentage_overall:
                        max_percentage_overall = percentage
                        single_best_letter = letter
                # Fallback para barras visíveis sem %
                elif 'style' in bar.attrs and \
                     ('display:flex' in bar.attrs['style'].replace(' ', '') or \
                      'display: flex' in bar.attrs['style'].replace(' ', '')):
                    letter_only_match = visible_letter_only_pattern.match(bar_text)
                    if letter_only_match and not visible_bar_letter_candidate: # Pega a primeira visível
                        visible_bar_letter_candidate = letter_only_match.group(1)
            
            if single_best_letter: # Se encontrou alguma com porcentagem
                resposta_sugerida_letras_raw_list = [single_best_letter]
            elif visible_bar_letter_candidate: # Senão, usa a visível sem porcentagem
                resposta_sugerida_letras_raw_list = [visible_bar_letter_candidate]

    final_resposta_sugerida_str = "".join(sorted(list(set(resposta_sugerida_letras_raw_list))))
    
    if final_resposta_sugerida_str:
        print(f"    Resposta sugerida (scraper): '{final_resposta_sugerida_str}'")
    else:
        print(f"    Resposta sugerida não encontrada/parseada.")

    # Determinar num_answers_to_select
    num_opcoes = len(opcoes_lista)
    num_answers_to_select = 1 # Default

    # Se o scraper encontrou explicitamente uma resposta (única ou múltipla), usa o tamanho dela
    if final_resposta_sugerida_str:
        num_answers_to_select = len(final_resposta_sugerida_str)
        if num_answers_to_select == 0: # Caso de string vazia (improvável, mas seguro)
            num_answers_to_select = 1 
    else: 
        # Se o scraper NÃO encontrou resposta, aplica sua regra baseada no número de opções
        if num_opcoes == 5:
            num_answers_to_select = 2
        elif num_opcoes == 6:
            num_answers_to_select = 3
    
    print(f"    Num de opções na página: {num_opcoes}, Num de respostas a selecionar: {num_answers_to_select}")

    return {
        "id_original_json": url_info.get('question_id', str(question_index_overall)),
        "url_original": url_info['url'],
        "titulo_original": url_info.get('title', "N/A"),
        "enunciado_html": enunciado_html_str,
        "opcoes": opcoes_lista,
        "resposta_sugerida_letra": final_resposta_sugerida_str, # Pode ser "AD", "A", ou ""
        "num_answers_to_select": num_answers_to_select # NOVO CAMPO
    }

def main_scraper():
    driver = setup_driver()
    if not driver:
        return

    try:
        with open(INPUT_JSON_URLS_FILE, 'r', encoding='utf-8') as f:
            lista_urls_info = json.load(f)
    except FileNotFoundError:
        print(f"ERRO: Arquivo de entrada '{INPUT_JSON_URLS_FILE}' não encontrado.")
        if driver: driver.quit()
        return
    except json.JSONDecodeError:
        print(f"ERRO: Arquivo '{INPUT_JSON_URLS_FILE}' não é um JSON válido.")
        if driver: driver.quit()
        return

    if not isinstance(lista_urls_info, list) or not lista_urls_info:
        print("Arquivo JSON de entrada está vazio ou não é uma lista.")
        if driver: driver.quit()
        return
    
    questoes_processadas_lista = []
    
    urls_to_process = lista_urls_info
    if MAX_QUESTIONS_TO_SCRAPE_FOR_TESTING is not None:
        urls_to_process = lista_urls_info[:MAX_QUESTIONS_TO_SCRAPE_FOR_TESTING]
        print(f"--- ATENÇÃO: Processando apenas as primeiras {MAX_QUESTIONS_TO_SCRAPE_FOR_TESTING} questões para teste! ---")

    total_a_processar = len(urls_to_process)

    for i, url_info_item in enumerate(urls_to_process):
        print(f"Processando questão {i+1}/{total_a_processar}...")
        try:
            dados_questao = extract_question_data_from_page(driver, url_info_item, i)
            questoes_processadas_lista.append(dados_questao)
        except Exception as e_page:
            print(f"  !!!! ERRO CRÍTICO ao processar a página {url_info_item['url']}: {e_page} !!!!")
            questoes_processadas_lista.append({
                "id_original_json": url_info_item.get('question_id', str(i)),
                "url_original": url_info_item['url'],
                "titulo_original": url_info_item.get('title', "ERRO NA EXTRAÇÃO"),
                "enunciado_html": f"<p>Erro ao extrair dados desta questão: {e_page}</p>",
                "opcoes": [],
                "resposta_sugerida_letra": "", # Default para erro
                "num_answers_to_select": 1,    # Default para erro
                "error": str(e_page)
            })

        if i < total_a_processar - 1:
            delay = random.uniform(MIN_DELAY_SECONDS, MAX_DELAY_SECONDS)
            print(f"  Esperando por {delay:.2f} segundos...")
            time.sleep(delay)
    
    try:
        with open(OUTPUT_PROCESSED_QUESTIONS_FILE, 'w', encoding='utf-8') as f_out:
            json.dump(questoes_processadas_lista, f_out, indent=4, ensure_ascii=False)
        print(f"\nConcluído! {len(questoes_processadas_lista)} questões processadas e salvas em '{OUTPUT_PROCESSED_QUESTIONS_FILE}'")
    except IOError:
        print(f"ERRO: Não foi possível escrever o arquivo de saída '{OUTPUT_PROCESSED_QUESTIONS_FILE}'.")
    
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    if not os.path.exists(INPUT_JSON_URLS_FILE):
        print(f"ERRO: Arquivo de entrada '{INPUT_JSON_URLS_FILE}' não encontrado.")
        print("Por favor, crie este arquivo com a lista de URLs das questões no formato JSON.")
    else:
        main_scraper()