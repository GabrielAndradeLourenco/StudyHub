#!/usr/bin/env python3
import time
import json
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

def retry_on_failure(max_retries=3, delay=5):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(f"Tentativa {attempt + 1} falhou: {e}")
                    if attempt < max_retries - 1:
                        print(f"Aguardando {delay} segundos antes de tentar novamente...")
                        time.sleep(delay)
                    else:
                        raise e
            return None
        return wrapper
    return decorator

@retry_on_failure(max_retries=3)
def setup_driver():
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    return webdriver.Chrome(service=service, options=options)

@retry_on_failure(max_retries=3)
def extract_page_links(driver, base_url):
    print(f"   ⏳ Aguardando elementos carregarem...")
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.discussion-list"))
    )
    print(f"   ✅ Container principal encontrado!")
    
    page_links = []
    discussion_rows = driver.find_elements(By.CSS_SELECTOR, "div.discussion-list div.discussion-row")
    print(f"   🔍 Encontradas {len(discussion_rows)} rows de discussão")
    
    for i, row in enumerate(discussion_rows, 1):
        try:
            title_div = row.find_element(By.CSS_SELECTOR, "div.col-7.col-md-6.discussion-column.discussion-title")
            link_element = title_div.find_element(By.CSS_SELECTOR, "div.dicussion-title-container h2 a.discussion-link")
            href = link_element.get_attribute("href")
            title = link_element.text.strip()
            
            creation_info = title_div.find_element(By.CSS_SELECTOR, "p.creation-info")
            author_element = creation_info.find_element(By.CSS_SELECTOR, "a.title-username")
            author = author_element.text.strip()
            
            stats_div = row.find_element(By.CSS_SELECTOR, "div.discussion-stats")
            replies_element = stats_div.find_element(By.CSS_SELECTOR, "div.discussion-stats-replies")
            replies = replies_element.text.split('\n')[0].strip()
            
            try:
                views_element = stats_div.find_element(By.CSS_SELECTOR, "div.discussion-stats-views")
                views = views_element.text.split('\n')[0].strip()
            except:
                views = "N/A"
            
            full_url = base_url + href if href.startswith('/') else href
            
            page_links.append({
                'url': full_url,
                'title': title,
                'author': author,
                'replies': replies,
                'views': views,
                'creation_info': creation_info.text.strip()
            })
            
            print(f"   ✅ Link {i}/20: {title[:50]}... (Autor: {author}, Replies: {replies})")
            
        except Exception as e:
            print(f"   ❌ Erro ao extrair link {i}: {e}")
            continue
    
    print(f"   📊 Extração concluída: {len(page_links)} links válidos")
    return page_links

def scrape_examtopics_links():
    driver = setup_driver()
    all_links = []
    base_url = "https://www.examtopics.com"
    current_url = "https://www.examtopics.com/discussions/amazon/"
    page_count = 0
    total_pages = 567
    expected_links_per_page = 20
    
    print(f"🚀 INICIANDO SCRAPING DO EXAMTOPICS")
    print(f"📊 Total de páginas esperadas: {total_pages}")
    print(f"🔗 Links esperados por página: {expected_links_per_page}")
    print(f"📈 Total de links esperados: {total_pages * expected_links_per_page}")
    print("="*60)
    
    try:
        while page_count < total_pages:
            page_count += 1
            
            print(f"\n📄 PÁGINA {page_count}/{total_pages} ({(page_count/total_pages)*100:.1f}%)")
            print(f"🌐 URL: {current_url}")
            
            page_loaded = False
            for attempt in range(3):
                try:
                    print(f"⏳ Carregando página... (tentativa {attempt + 1}/3)")
                    driver.get(current_url)
                    page_loaded = True
                    print(f"✅ Página carregada com sucesso!")
                    break
                except WebDriverException as e:
                    print(f"❌ Erro ao carregar página (tentativa {attempt + 1}): {e}")
                    if attempt == 2:
                        raise e
                    time.sleep(5)
            
            if not page_loaded:
                print(f"💥 FALHA CRÍTICA: Não foi possível carregar a página {page_count}")
                break
            
            print(f"🔍 Extraindo links da página {page_count}...")
            page_links = extract_page_links(driver, base_url)
            all_links.extend(page_links)
            
            links_found = len(page_links)
            total_links = len(all_links)
            
            if links_found == expected_links_per_page:
                print(f"✅ Links extraídos: {links_found}/{expected_links_per_page} (PERFEITO!)")
            elif links_found > 0:
                print(f"⚠️  Links extraídos: {links_found}/{expected_links_per_page} (MENOS QUE O ESPERADO)")
            else:
                print(f"❌ Links extraídos: {links_found}/{expected_links_per_page} (NENHUM LINK ENCONTRADO!)")
            
            print(f"📊 Total acumulado: {total_links} links")
            print(f"⏱️  Progresso: {(total_links/(total_pages*expected_links_per_page))*100:.1f}% do total esperado")
            
            print(f"🔍 Procurando botão 'Next'...")
            try:
                pagination_section = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "span.pagination-nav"))
                )
                next_button = pagination_section.find_element(By.XPATH, ".//a[contains(text(), 'Next')]")
                next_href = next_button.get_attribute("href")
                
                if next_href and next_href != current_url:
                    print(f"✅ Botão 'Next' encontrado! Próxima URL: {next_href}")
                    current_url = next_href
                    
                    wait_time = random.uniform(2, 5)
                    print(f"⏸️  Aguardando {wait_time:.1f}s antes da próxima página...")
                    time.sleep(wait_time)
                else:
                    print(f"🏁 FINAL ALCANÇADO: Não há mais páginas para processar.")
                    break
            except (NoSuchElementException, TimeoutException) as e:
                print(f"🏁 FINAL ALCANÇADO: Botão 'Next' não encontrado na página {page_count}. Erro: {e}")
                try:
                    next_page_num = page_count + 1
                    next_link = driver.find_element(By.XPATH, f"//a[@href='/discussions/amazon/{next_page_num}/']")
                    next_href = next_link.get_attribute("href")
                    print(f"✅ Link alternativo encontrado: {next_href}")
                    current_url = base_url + next_href if next_href.startswith('/') else next_href
                    time.sleep(random.uniform(2, 5))
                except:
                    print(f"❌ Método alternativo também falhou. Finalizando...")
                    break
            
            if page_count % 10 == 0:
                print(f"💾 SALVANDO PROGRESSO... ({page_count} páginas processadas)")
                save_progress(all_links, page_count)
                print(f"📈 Progresso salvo! Média de {len(all_links)/page_count:.1f} links por página")
                
    except KeyboardInterrupt:
        print(f"\n⏹️  INTERROMPIDO PELO USUÁRIO na página {page_count}")
        print(f"📊 Links coletados até agora: {len(all_links)}")
    except Exception as e:
        print(f"\n💥 ERRO CRÍTICO na página {page_count}: {e}")
        print(f"📊 Links coletados até o erro: {len(all_links)}")
    finally:
        print(f"\n🔒 Fechando navegador...")
        driver.quit()
    
    return all_links

def save_progress(links, page_count):
    filename = f"examtopics_progress_page_{page_count}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump({
            'page_count': page_count,
            'total_links': len(links),
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'links': links
        }, f, indent=2, ensure_ascii=False)

def save_links(links):
    print(f"\n💾 SALVANDO RESULTADOS FINAIS...")
    
    with open("examtopics_links.txt", 'w', encoding='utf-8') as f:
        for item in links:
            f.write(item['url'] + '\n')
    print(f"✅ URLs salvos em: examtopics_links.txt")
    
    with open("examtopics_data.json", 'w', encoding='utf-8') as f:
        json.dump(links, f, indent=2, ensure_ascii=False)
    print(f"✅ Dados completos salvos em: examtopics_data.json")
    
    with open("examtopics_summary.txt", 'w', encoding='utf-8') as f:
        f.write(f"📊 RELATÓRIO FINAL DO SCRAPING EXAMTOPICS\n")
        f.write(f"="*50 + "\n\n")
        f.write(f"Total de links coletados: {len(links)}\n")
        f.write(f"Data da coleta: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Links esperados (567 páginas x 20): 11,340\n")
        f.write(f"Percentual coletado: {(len(links)/11340)*100:.1f}%\n\n")
        
        authors = {}
        for item in links:
            author = item.get('author', 'Desconhecido')
            authors[author] = authors.get(author, 0) + 1
        
        f.write(f"Top 10 autores mais ativos:\n")
        for i, (author, count) in enumerate(sorted(authors.items(), key=lambda x: x[1], reverse=True)[:10]):
            f.write(f"{i+1}. {author}: {count} questões\n")
        
        f.write(f"\nPrimeiros 10 links coletados:\n")
        for i, item in enumerate(links[:10]):
            f.write(f"{i+1}. {item['title']}\n")
            f.write(f"   URL: {item['url']}\n")
            f.write(f"   Autor: {item.get('author', 'N/A')}\n")
            f.write(f"   Replies: {item.get('replies', 'N/A')}\n")
            f.write(f"   Views: {item.get('views', 'N/A')}\n\n")
    
    print(f"✅ Resumo detalhado salvo em: examtopics_summary.txt")
    print(f"\n🎉 TODOS OS ARQUIVOS SALVOS COM SUCESSO!")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🎯 EXAMTOPICS SCRAPER - VERSÃO PROFISSIONAL")
    print("="*60)
    
    start_time = time.time()
    
    try:
        links = scrape_examtopics_links()
        
        print("\n" + "="*60)
        print("📊 RESULTADOS FINAIS")
        print("="*60)
        print(f"✅ Total de links coletados: {len(links)}")
        print(f"🎯 Meta (567 páginas x 20 links): 11,340")
        print(f"📈 Percentual alcançado: {(len(links)/11340)*100:.1f}%")
        
        if links:
            save_links(links)
            elapsed_time = time.time() - start_time
            hours = int(elapsed_time // 3600)
            minutes = int((elapsed_time % 3600) // 60)
            seconds = int(elapsed_time % 60)
            
            print(f"\n⏱️  TEMPO TOTAL: {hours:02d}h {minutes:02d}m {seconds:02d}s")
            print(f"⚡ Velocidade média: {len(links)/(elapsed_time/60):.1f} links/minuto")
            print(f"\n🎉 SCRAPING CONCLUÍDO COM SUCESSO!")
        else:
            print(f"\n❌ NENHUM LINK FOI COLETADO!")
            print(f"🔍 Verifique a conexão e a estrutura do site.")
            
    except KeyboardInterrupt:
        print(f"\n\n⏹️  SCRAPING INTERROMPIDO PELO USUÁRIO")
        print(f"📊 Verifique os arquivos de progresso salvos.")
    except Exception as e:
        print(f"\n\n💥 ERRO FATAL: {e}")
        print(f"🔧 Verifique sua conexão com a internet e tente novamente.")
        print(f"📋 Logs detalhados foram exibidos acima.")
    
    print("\n" + "="*60)