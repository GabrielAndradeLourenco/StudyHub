#!/bin/bash
# Script para sincronizar questões processadas com o backend
# Mantém a estrutura antiga funcionando + adiciona os novos

echo "🔄 Sincronizando questões processadas com o backend..."

# Criar diretório se não existir
mkdir -p "Questões/exams/questoes_processadas"

# Copiar APENAS os 3 arquivos que processamos
if [ -f "data/exams/processed/AWS Certified Generative AI Developer - Professional AIP-C01_questoes.json" ]; then
    cp "data/exams/processed/AWS Certified Generative AI Developer - Professional AIP-C01_questoes.json" \
       "Questões/exams/questoes_processadas/"
    echo "✅ Copiado: Generative AI Developer"
fi

if [ -f "data/exams/processed/AWS Certified AI Practitioner AIF-C01_questoes.json" ]; then
    cp "data/exams/processed/AWS Certified AI Practitioner AIF-C01_questoes.json" \
       "Questões/exams/questoes_processadas/"
    echo "✅ Copiado: AI Practitioner"
fi

if [ -f "data/exams/processed/AWS Certified Data Engineer - Associate DEA-C01_questoes.json" ]; then
    cp "data/exams/processed/AWS Certified Data Engineer - Associate DEA-C01_questoes.json" \
       "Questões/exams/questoes_processadas/"
    echo "✅ Copiado: Data Engineer"
fi

echo ""
echo "🎉 Sincronização concluída!"
echo ""
echo "⚠️  Próximo passo: Adicionar o Generative AI no backend/app.py"
