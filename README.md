# ProjectPokemon

Aplicação web de enciclopédia Pokémon com Pokedex interativa, filtros dinâmicos
(tipo, geração), página de detalhe de cada Pokémon com redes de aprendizagem,
habilidades, fraquezas e resistências, e comparação de estatísticas com gráfico
radar. Backend completo a fazer proxy da API pública PokeAPI.

## Stack

- Backend: Django 5 + Django REST Framework (Python)
- Frontend: React 19 + Vite (JavaScript)
- Gráficos: Recharts (radar de estatísticas)
- API externa: PokeAPI (com cache no backend)

## Como correr

Backend (com UV):

    cd backend
    uv sync
    cp .env.example .env   # preencher a SECRET_KEY
    uv run python manage.py migrate
    uv run python manage.py runserver

Frontend:

    cd frontend
    npm install
    npm run dev

Abrir `http://localhost:5173`, o frontend fala com a API em
`http://localhost:8000` configurada em `CORS_ALLOWED_ORIGINS`.

## Estrutura

- `backend/`, API Django REST (app `pokemon`, throttling e cache da PokeAPI)
- `frontend/`, SPA React (Vite)
- `.github/workflows/ci.yml`, CI básico (lint e testes)
- `IDEA.md`, nota inicial de visão do projeto

### Nota sobre dados sensíveis

O ficheiro `.env` (chave secreta, config de ambiente) **não é commitado**. Usar
`.env.example` como modelo.
