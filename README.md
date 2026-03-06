# Calculadora + Busca RSC-PCCTAE

Aplicação full-stack com:
- **Backend em Python (FastAPI)** para cálculo de pontos e anos de serviço público;
- **Frontend em React (Vite)** para cadastro de servidor, cálculo e orientação de busca por nome;
- Rotas de busca baseadas nas orientações do ofício (SIPPAGweb, SEI/IFCE e Boletins de Serviço);
- Integração opcional com uma LLM/MCP do SEI via variável `SEI_MCP_URL`.

## Funcionalidades implementadas

1. **Busca orientada por artigo/orientações do ofício**
   - Sugestões de pesquisa no SIPPAGweb;
   - Sugestões de pesquisa avançada no SEI;
   - Sugestões para busca em boletins com Google (`filetype:pdf site:ifce.edu.br`);
   - Links diretos para os portais informados.

2. **Calculadora de pontos**
   - Campos: nome, cargo, data de início no serviço público;
   - Cálculo automático de anos de serviço;
   - Pontos por atividades (quantidade × pontos unitários);
   - Pontuação extra por tempo de serviço.

3. **Integração LLM/MCP (opcional)**
   - Endpoint `/api/search` tenta consultar um MCP/LLM externo quando `SEI_MCP_URL` está configurado.

## Como executar

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Opcional para apontar o frontend para outra API:
```bash
VITE_API_BASE=http://localhost:8000 npm run dev
```

## Endpoints
- `GET /api/health`
- `POST /api/calculate`
- `POST /api/search`
