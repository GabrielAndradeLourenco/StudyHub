#!/usr/bin/env python3
import time
import json
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    return webdriver.Chrome(options=options)

def scrape_genai_exam():
    driver = setup_driver()
    all_questions = []
    base_url = "https://www.examtopics.com"
    # MUDE AQUI: URL do exame que você quer
    exam_url = "https://www.examtopics.com/exams/amazon/aws-certified-generative-ai-developer-professional-aip-c01/"
    page = 1
    
    print(f"🚀 Iniciando scraping do exame Generative AI Developer")
    
    try:
        while True:
            current_url = f"{exam_url}view/{page}/" if page > 1 else f"{exam_url}view/"
            print(f"\n📄 Página {page}")
            print(f"🌐 URL: {current_url}")
            
            driver.get(current_url)
            time.sleep(2)
            
            # Encontrar todas as questões na página
            try:
                questions = driver.find_elements(By.CSS_SELECTOR, "div.discussion-row")
                print(f"🔍 Encontradas {len(questions)} questões")
                
                if len(questions) == 0:
                    print("🏁 Nenhuma questão encontrada. Fim do scraping.")
                    break
                
                for i, question in enumerate(questions, 1):
                    try:
                        link = question.find_element(By.CSS_SELECTOR, "a.discussion-link")
                        title = link.text.strip()
                        url = link.get_attribute("href")
                        
                        if url.startswith('/'):
                            url = base_url + url
                        
                        all_questions.append({
                            'title': title,
                            'url': url
                        })
                        
                        print(f"   ✅ {i}. {title}")
                    except Exception as e:
                        print(f"   ❌ Erro na questão {i}: {e}")
                
                # Tentar ir para próxima página
                try:
                    next_button = driver.find_element(By.XPATH, "//a[contains(text(), 'Next')]")
                    page += 1
                    time.sleep(random.uniform(1, 3))
                except NoSuchElementException:
                    print("🏁 Última página alcançada")
                    break
                    
            except Exception as e:
                print(f"❌ Erro ao processar página {page}: {e}")
                break
    
    finally:
        driver.quit()
    
    return all_questions

def save_results(questions):
    # Salvar no formato esperado
    output_file = "../AWS Certified Generative AI Developer Professional AIP-C01.json"
    
    exam_data = {
        "exam_name": "AWS Certified Generative AI Developer Professional AIP-C01",
        "total_questions": len(questions),
        "questions": questions
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(exam_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ {len(questions)} questões salvas em '{output_file}'")

if __name__ == "__main__":
    print("="*60)
    print("🎯 SCRAPER - AWS Generative AI Developer Professional")
    print("="*60)
    
    questions = scrape_genai_exam()
    
    if questions:
        save_results(questions)
        print(f"\n🎉 Scraping concluído! Total: {len(questions)} questões")
    else:
        print("\n❌ Nenhuma questão foi coletada")
