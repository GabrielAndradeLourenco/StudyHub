#!/usr/bin/env python3
"""
Script para coletar todas as URLs de questões do ExamTopics
Navega pelas páginas de discussões e extrai os links das questões
Gera o arquivo questoes_base.json
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json
import time
import random
import re
import os

# --- CONFIGURAÇÕES ---
BASE_URL = "https://www.examtopics.com/discussions/amazon/"
OUTPUT_FILE = "questoes_base.json"
USE_HEADLESS = True
MIN_DELAY = 1
MAX_DELAY = 3
START_PAGE = 1  # Página inicial
MAX_PAGES = None  # None para todas as páginas, ou número específico para limitar
# --- FIM CONFIGURAÇÕES ---

def setup_driver():
    """Configura o driver do Selenium"""
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("start-maximized")
        options.add_argument("disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument('--log-level=3')
        
        if USE_HEADLESS:
            options.add_argument('--headless')
        
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        print(f"❌ ERRO ao configurar o driver Selenium: {e}")
        print("💡 Certifique-se de ter o Chrome e ChromeDriver instalados")
        return None

def extract_question_id_from_title(title):
    """Extrai o ID da questão do título"""
    # Padrão: "... question 123 discussion"
    match = re.search(r'question\s+(\d+)\s+discussion', title, re.IGNORECASE)
    return match.group(1) if match else None

def extract_exam_id_from_url(url):
    """Extrai o exam_id da URL"""
    # Padrão: /view/12345-exam-...
    match = re.search(r'/view/(\d+)-', url)
    return int(match.group(1)) if match else None

def scrape_page(driver, page_num):
    """Faz scraping de uma página de discussões"""
    if page_num == 1:
        url = BASE_URL
    else:
        url = f"{BASE_URL}{page_num}/"
    
    print(f"\n📄 Acessando página {page_num}: {url}")
    
    try:
        driver.get(url)
        time.sleep(2)  # Aguarda carregamento
        
        # Encontrar todas as discussões
        discussions = driver.find_elements(By.CSS_SELECTOR, "div.discussion-row")
        
        if not discussions:
            print(f"⚠️  Nenhuma discussão encontrada na página {page_num}")
            return [], False
        
        questions = []
        print(f"🔍 Encontradas {len(discussions)} discussões")
        
        for discussion in discussions:
            try:
                # Encontrar o link da questão
                link_element = discussion.find_element(By.CSS_SELECTOR, "a.discussion-link")
                title = link_element.text.strip()
                url = link_element.get_attribute("href")
                
                # Extrair IDs
                question_id = extract_question_id_from_title(title)
                exam_id = extract_exam_id_from_url(url)
                
                if question_id and exam_id and url:
                    questions.append({
                        "exam_id": exam_id,
                        "url": url,
                        "title": title,
                        "question_id": question_id
                    })
                    print(f"   ✅ Questão {question_id}: {title[:80]}...")
                else:
                    print(f"   ⚠️  Dados incompletos: {title[:50]}")
                    
            except Exception as e:
                print(f"   ❌ Erro ao processar discussão: {e}")
                continue
        
        # Verificar se existe próxima página
        has_next = False
        try:
            next_button = driver.find_element(By.LINK_TEXT, "Next")
            has_next = True
        except NoSuchElementException:
            print("🏁 Última página alcançada")
        
        return questions, has_next
        
    except Exception as e:
        print(f"❌ Erro ao acessar página {page_num}: {e}")
        return [], False

def save_progress(questions, filename):
    """Salva o progresso em arquivo JSON"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(questions, f, indent=4, ensure_ascii=False)
        print(f"💾 Progresso salvo: {len(questions)} questões em '{filename}'")
    except Exception as e:
        print(f"⚠️  Erro ao salvar progresso: {e}")

def main():
    print("="*70)
    print("🚀 COLETOR DE URLs DO EXAMTOPICS")
    print("="*70)
    print(f"📍 URL base: {BASE_URL}")
    print(f"💾 Arquivo de saída: {OUTPUT_FILE}")
    print("="*70)
    
    driver = setup_driver()
    if not driver:
        return
    
    all_questions = []
    
    # Carregar progresso anterior se existir
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                all_questions = json.load(f)
            print(f"📂 Carregado arquivo existente com {len(all_questions)} questões")
            
            # Perguntar se quer continuar ou recomeçar
            response = input("Deseja continuar de onde parou? (s/n): ").lower()
            if response != 's':
                all_questions = []
                print("🔄 Recomeçando do zero...")
        except:
            print("⚠️  Erro ao carregar arquivo existente, começando do zero")
            all_questions = []
    
    try:
        page = START_PAGE
        has_next = True
        
        while has_next:
            if MAX_PAGES and page > MAX_PAGES:
                print(f"\n🛑 Limite de {MAX_PAGES} páginas atingido")
                break
            
            questions, has_next = scrape_page(driver, page)
            
            if questions:
                all_questions.extend(questions)
                print(f"📊 Total acumulado: {len(all_questions)} questões")
                
                # Salvar progresso a cada página
                save_progress(all_questions, OUTPUT_FILE)
            
            if has_next:
                page += 1
                delay = random.uniform(MIN_DELAY, MAX_DELAY)
                print(f"⏳ Aguardando {delay:.1f}s antes da próxima página...")
                time.sleep(delay)
        
        print("\n" + "="*70)
        print("🎉 COLETA CONCLUÍDA!")
        print("="*70)
        print(f"📊 Total de questões coletadas: {len(all_questions)}")
        print(f"💾 Arquivo salvo: {OUTPUT_FILE}")
        print("="*70)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrompido pelo usuário")
        print(f"💾 Salvando progresso... {len(all_questions)} questões coletadas")
        save_progress(all_questions, OUTPUT_FILE)
    
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        print(f"💾 Salvando progresso... {len(all_questions)} questões coletadas")
        save_progress(all_questions, OUTPUT_FILE)
    
    finally:
        if driver:
            driver.quit()
            print("🔒 Driver fechado")

if __name__ == "__main__":
    main()
