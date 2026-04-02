#!/bin/bash
# Script para organizar toda a estrutura do projeto

echo "🧹 Organizando estrutura do projeto..."

# Criar estrutura de diretórios
mkdir -p data/exams/raw
mkdir -p data/exams/processed

# Mover arquivos base para data/
if [ -f "questoes_base.json" ]; then
    mv questoes_base.json data/
    echo "✅ Movido questoes_base.json para data/"
fi

if [ -f "questoes_processadas.json" ]; then
    mv questoes_processadas.json data/
    echo "✅ Movido questoes_processadas.json para data/"
fi

# Copiar exames raw (URLs organizadas por exame)
cp "Questões/exams/"*.json data/exams/raw/ 2>/dev/null
echo "✅ Copiados arquivos de exames para data/exams/raw/"

# Copiar questões processadas
cp "Questões/exams/questoes_processadas/"*_questoes.json data/exams/processed/ 2>/dev/null
echo "✅ Copiados arquivos processados para data/exams/processed/"

echo ""
echo "🎉 Organização concluída!"
echo ""
echo "📁 Nova estrutura:"
echo "   data/"
echo "   ├── questoes_base.json (todas as URLs coletadas)"
echo "   └── exams/"
echo "       ├── raw/ (URLs organizadas por exame)"
echo "       └── processed/ (questões completas após scraping)"
