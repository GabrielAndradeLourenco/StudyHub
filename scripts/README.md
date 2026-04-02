# Scripts de Scraping - StudyHub

Scripts para coletar e processar questões do ExamTopics.

## 📋 Ordem de Execução

### 1. Coletar URLs (collect_examtopics_urls.py)
Navega em todas as páginas de discussões do ExamTopics e coleta URLs das questões.

```bash
python scripts/collect_examtopics_urls.py
```

**Saída:** `data/questoes_base.json` (todas as URLs coletadas)

---

### 2. Filtrar e Organizar por Exame (filter_and_organize_exams.py)
Filtra questões específicas e organiza por exame.

```bash
python scripts/filter_and_organize_exams.py
```

**Configuração:** Edite `EXAMES_FILTRAR` no script para escolher quais exames processar.

**Saída:** `data/exams/raw/[Nome do Exame].json`

---

### 3. Fazer Scraping Completo (process_questions.py)
Faz scraping detalhado de cada questão (enunciado, opções, resposta sugerida).

```bash
python scripts/process_questions.py
```

**Saída:** `data/exams/processed/[Nome do Exame]_questoes.json`

---

## 🛠️ Scripts Auxiliares

### scraper_selenium.py
Scraper individual que processa um arquivo específico de URLs.

### scraper_genai.py
Scraper específico para o exame Generative AI Developer.

---

## 📦 Dependências

```bash
pip install selenium beautifulsoup4
```

---

## 🎯 Exames Atualmente Configurados

- AWS Certified Generative AI Developer - Professional AIP-C01
- AWS Certified AI Practitioner AIF-C01
- AWS Certified Data Engineer - Associate DEA-C01

Para adicionar mais exames, edite `EXAMES_FILTRAR` em `filter_and_organize_exams.py`.
