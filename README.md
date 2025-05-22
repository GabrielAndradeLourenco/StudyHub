# StudyHub Project 📚✨

![StudyHub Banner](https://img.shields.io/badge/StudyHub-Learning%20Platform-blue?style=for-the-badge)

## 🚀 Visão Geral

StudyHub é uma plataforma moderna de estudos que permite aos usuários praticar e aprimorar seus conhecimentos através de questões interativas. Desenvolvida com Angular no frontend e Flask no backend, a aplicação oferece uma experiência de usuário fluida e responsiva para maximizar o aprendizado.

## ✨ Funcionalidades

- **Sessões de Estudo Interativas**: Crie e gerencie sessões de estudo personalizadas
- **Questões com Múltiplas Escolhas**: Suporte para questões com uma ou múltiplas respostas corretas
- **Feedback Instantâneo**: Receba feedback imediato sobre suas respostas
- **Histórico de Desempenho**: Acompanhe seu progresso e revise sessões anteriores
- **Interface Moderna**: Design intuitivo e responsivo desenvolvido com Angular

## 🛠️ Tecnologias Utilizadas

### Frontend
- **Angular**: Framework para construção de interfaces modernas e reativas
- **TypeScript**: Linguagem fortemente tipada para desenvolvimento escalável
- **SCSS**: Estilização avançada com pré-processador CSS

### Backend
- **Flask**: Framework web Python leve e flexível
- **SQLAlchemy**: ORM para interação com banco de dados
- **SQLite**: Banco de dados relacional para armazenamento de dados

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

## 📱 Capturas de Tela



## 🔄 Fluxo de Trabalho

1. **Início**: Escolha entre iniciar uma nova sessão ou continuar uma existente
2. **Questões**: Responda às questões selecionando as opções corretas
3. **Feedback**: Receba feedback imediato sobre suas respostas
4. **Resultados**: Visualize seu desempenho ao final da sessão
5. **Histórico**: Acesse sessões anteriores para revisar seu progresso

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou enviar pull requests.

## 📄 Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes.
