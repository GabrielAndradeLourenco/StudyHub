# StudyHub Project 📚✨

![StudyHub Banner](https://img.shields.io/badge/StudyHub-Learning%20Platform-blue?style=for-the-badge)

## 🚀 Visão Geral

StudyHub é uma plataforma moderna de estudos que permite aos usuários praticar e aprimorar seus conhecimentos através de questões interativas. Desenvolvida com Angular no frontend e Flask no backend, a aplicação oferece uma experiência de usuário fluida e responsiva para maximizar o aprendizado. Com um design adaptável para dispositivos móveis e desktop, o StudyHub proporciona flexibilidade para estudar em qualquer lugar e a qualquer momento.

## ✨ Funcionalidades

- **Sessões de Estudo Interativas**: Crie e gerencie sessões de estudo personalizadas
- **Escolha da Questão Inicial**: Selecione em qual questão deseja começar o simulado
- **Questões com Múltiplas Escolhas**: Suporte para questões com uma ou múltiplas respostas corretas
- **Feedback Instantâneo**: Receba feedback imediato sobre suas respostas
- **Histórico de Desempenho**: Acompanhe seu progresso e revise sessões anteriores
- **Interface Moderna**: Design intuitivo e responsivo para desktop e dispositivos móveis

## 🛠️ Tecnologias Utilizadas

### Frontend
- **Angular**: Framework para construção de interfaces modernas e reativas
- **TypeScript**: Linguagem fortemente tipada para desenvolvimento escalável
- **SCSS**: Estilização avançada com pré-processador CSS
- **Bootstrap Icons**: Biblioteca de ícones para melhorar a experiência visual
- **Design Responsivo**: Interface adaptável para desktop e dispositivos móveis

### Backend
- **Flask**: Framework web Python leve e flexível
- **SQLAlchemy**: ORM para interação com banco de dados
- **SQLite**: Banco de dados relacional para armazenamento de dados
- **Gunicorn**: Servidor WSGI HTTP para Python

## 📋 Estrutura do Projeto

```
StudyHub_Project/
├── backend/             # API Flask
│   ├── app.py           # Aplicação principal e endpoints da API
│   └── requirements.txt # Dependências do backend
├── frontend/            # Aplicação Angular
│   └── studyhub-frontend/
│       ├── src/         # Código fonte do frontend
│       └── ...          # Arquivos de configuração Angular
├── instance/            # Banco de dados SQLite
├── questoes_processadas.json  # Dados das questões
├── build.sh             # Script para build no Render
├── render.yaml          # Configuração para deploy no Render
└── run.py               # Script para inicialização do banco de dados
```

## 🚀 Como Executar

### Pré-requisitos
- Python 3.8+
- Node.js 14+
- Angular CLI

### Configuração do Backend
1. Navegue até o diretório do backend:
   ```bash
   cd backend
   ```

2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

3. Inicialize o banco de dados:
   ```bash
   cd ..
   python -m flask --app run.py init-db
   ```

4. Inicie o servidor Flask:
   ```bash
   cd backend
   python app.py
   ```
   O servidor estará disponível em `http://localhost:5002`

### Configuração do Frontend
1. Navegue até o diretório do frontend:
   ```bash
   cd frontend/studyhub-frontend
   ```

2. Instale as dependências:
   ```bash
   npm install
   ```

3. Inicie o servidor de desenvolvimento:
   ```bash
   ng serve
   ```
   O aplicativo estará disponível em `http://localhost:4200`

## 🌐 Deploy no Render

O StudyHub está configurado para ser facilmente implantado na plataforma Render.

### Configuração Automática
1. Faça fork deste repositório para sua conta GitHub
2. No Render, vá para o Dashboard e clique em "New +"
3. Selecione "Blueprint" e conecte seu repositório GitHub
4. O Render detectará automaticamente o arquivo `render.yaml` e configurará os serviços

### Configuração Manual
1. **Para o Backend**:
   - Crie um novo "Web Service"
   - Conecte seu repositório GitHub
   - Escolha "Python" como ambiente
   - Defina o comando de build: `./build.sh`
   - Defina o comando de start: `gunicorn backend.app:app`
   - Adicione a variável de ambiente: `FLASK_ENV=production`

2. **Para o Frontend**:
   - Crie um novo "Static Site"
   - Conecte seu repositório GitHub
   - Defina o comando de build: `cd frontend/studyhub-frontend && npm install && npm run build`
   - Defina o diretório de publicação: `frontend/studyhub-frontend/dist/studyhub-frontend`
   - Adicione a regra de reescrita: `/* /index.html 200`

## 📱 Capturas de Tela

### Interface Responsiva
A plataforma foi projetada para funcionar perfeitamente em dispositivos desktop e móveis, com uma interface que se adapta automaticamente ao tamanho da tela.

### Principais Recursos Visuais
- **Design Moderno**: Interface limpa com paleta de cores harmoniosa
- **Navegação Intuitiva**: Botões grandes e fáceis de usar em dispositivos móveis
- **Feedback Visual**: Indicadores claros para respostas corretas e incorretas
- **Modal de Seleção**: Escolha facilmente em qual questão deseja começar

## 🔄 Fluxo de Trabalho

1. **Início**: Escolha entre iniciar uma nova sessão, selecionar uma questão específica para começar, ou continuar uma sessão existente
2. **Questões**: Responda às questões selecionando as opções corretas
3. **Feedback**: Receba feedback imediato sobre suas respostas
4. **Navegação**: Avance para a próxima questão ou retorne às anteriores
5. **Resultados**: Visualize seu desempenho ao final da sessão
6. **Histórico**: Acesse sessões anteriores para revisar seu progresso

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou enviar pull requests.

## 📄 Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes.