# 🧠 Método Mente Calma — App

Sistema web completo com login para acompanhamento do protocolo alimentar TDAH de 30 dias.

## Como subir no Railway.app (R$5/mês aprox.)

### Passo 1 — Criar conta no GitHub
- Acesse github.com e crie uma conta gratuita

### Passo 2 — Criar repositório
- Clique em "New repository"
- Nome: mentecalma
- Clique "Create repository"
- Suba todos os arquivos desta pasta

### Passo 3 — Deploy no Railway
- Acesse railway.app
- Clique "Login with GitHub"
- Clique "New Project" → "Deploy from GitHub repo"
- Selecione o repositório "mentecalma"
- Railway detecta automaticamente o Python/Flask

### Passo 4 — Variáveis de ambiente
No Railway, vá em "Variables" e adicione:
- SECRET_KEY = (qualquer texto aleatório, ex: mentecalma2024xyz)

### Passo 5 — Domínio
- Clique em "Settings" → "Generate Domain"
- Você receberá um link tipo: mentecalma.up.railway.app 🎉

## Estrutura do projeto
```
mentecalma/
├── app.py              # Aplicação principal
├── requirements.txt    # Dependências Python
├── Procfile           # Configuração de servidor
└── templates/
    ├── base.html      # Layout base
    ├── login.html     # Página de login
    ├── register.html  # Cadastro
    ├── dashboard.html # Painel principal
    ├── checkin.html   # Check-in diário
    ├── history.html   # Histórico
    └── progress.html  # Gráficos e progresso
```

## Tecnologias
- Python + Flask
- SQLite (banco de dados)
- HTML/CSS puro (sem frameworks externos)
