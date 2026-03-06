from __future__ import annotations

from datetime import date, datetime
from typing import Dict, List, Optional

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


class ActivityItem(BaseModel):
    categoria: str
    quantidade: float = Field(ge=0)
    pontos_unitarios: float = Field(ge=0)


class ScoreRequest(BaseModel):
    nome: str
    cargo: str
    data_inicio_servico: str
    atividades: List[ActivityItem] = Field(default_factory=list)


class SearchRequest(BaseModel):
    nome: str
    data_inicio_servico: str
    palavras_chave: List[str] = Field(default_factory=list)
    unidade_geradora: Optional[str] = None
    tipo_documento: Optional[str] = None


class SearchResult(BaseModel):
    fonte: str
    titulo: str
    url: str
    estrategia: str


def years_of_service(start_date: date, reference: Optional[date] = None) -> float:
    reference = reference or date.today()
    delta_days = (reference - start_date).days
    if delta_days < 0:
        raise ValueError("Data de início não pode ser no futuro.")
    return round(delta_days / 365.25, 2)


def parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError("Use o formato de data YYYY-MM-DD.") from exc


def service_points(anos: float) -> float:
    # Fórmula simples de referência: 1 ponto por ano + bônus após 10 anos.
    base = anos
    bonus = max(0.0, (anos - 10) * 0.5)
    return round(base + bonus, 2)




def resolve_year_window(data_inicio_servico: str) -> str:
    inicio = parse_date(data_inicio_servico)
    ano_inicio = inicio.year
    ano_atual = date.today().year
    return f"{ano_inicio}-{ano_atual}"

def build_search_queries(req: SearchRequest) -> List[SearchResult]:
    nome_aspas = f'"{req.nome}"'
    extra = " ".join(req.palavras_chave)
    unidade = req.unidade_geradora or "(opcional)"
    tipo = req.tipo_documento or "(opcional)"
    recorte_anos = resolve_year_window(req.data_inicio_servico)

    return [
        SearchResult(
            fonte="SIPPAGweb",
            titulo="Busca de portarias no SIPPAGweb",
            url="https://sippag-web.ifce.edu.br/portarias",
            estrategia=(
                f"Acessar https://sippag-web.ifce.edu.br/portarias; no campo Interessado usar {nome_aspas}; "
                f"refinar por ano no intervalo {recorte_anos} e palavra-chave '{extra or 'comissão/contrato'}'."
            url="https://sippag-web.ifce.edu.br/boletim",
            estrategia=(
                f"Abrir Transparência > Documentos > Portarias; pesquisar interessado {nome_aspas} "
                f"e palavra-chave '{extra or 'comissão/contrato'}'."
            ),
        ),
        SearchResult(
            fonte="SEI/IFCE",
            titulo="Pesquisa avançada no SEI",
            url=(
                "https://sei.ifce.edu.br/sei/publicacoes/controlador_publicacoes.php"
                "?acao=publicacao_pesquisar&acao_origem=publicacao_pesquisar&id_orgao_publicacao=0&id_serie=3&rdo_data_publicacao=I"
            ),
            estrategia=(
                f"Acessar pesquisa avançada no SEI (lupa): texto {nome_aspas} {extra}; "
                f"unidade geradora: {unidade}; tipo de documento: {tipo}; "
                f"aplicar recorte temporal aproximado de {recorte_anos}; testar variações com aspas."
                f"Usar texto de pesquisa {nome_aspas} {extra}; unidade geradora: {unidade}; "
                f"tipo de documento: {tipo}."
            ),
        ),
        SearchResult(
            fonte="Boletim de Serviços (Google)",
            titulo="Busca refinada em PDFs públicos",
            url="https://portal.ifce.edu.br/institucional/documentos-institucionais/boletim-de-servicos/reitoria/",
            estrategia=(
                f'Pesquisar no Google: "boletim de serviços" {nome_aspas} filetype:pdf site:ifce.edu.br {extra} {recorte_anos} (pode incluir SIAPE/assunto para refinar)'.strip()
                f'Pesquisar no Google: "boletim de serviços" {nome_aspas} filetype:pdf site:ifce.edu.br {extra}'.strip()
            ),
        ),
        SearchResult(
            fonte="Boletim Reitoria 2018",
            titulo="Acervo histórico de boletins",
            url="https://portal.ifce.edu.br/institucional/documentos-institucionais/boletim-de-servicos/reitoria/2018/",
            estrategia="Consultar edições por ano e filtrar pelo nome do servidor.",
        ),
        SearchResult(
            fonte="Boletim Campus Juazeiro do Norte",
            titulo="Boletins do campus",
            url="https://portal.ifce.edu.br/campus/juazeirodonorte/boletim-de-servico/",
            estrategia="Pesquisar nome e cargo no boletim local do campus.",
        ),
        SearchResult(
            fonte="Boletim Campus Acaraú",
            titulo="Boletins de 2015 em diante",
            url="https://portal.ifce.edu.br/campus/acarau/documentos-institucionais/boletins-de-servico-do-campus-acarau/2015/",
            estrategia="Verificar portarias, ordens de serviço e termos de designação.",
        ),

        SearchResult(
            fonte="Declarações funcionais",
            titulo="Recomendação da PROGEP",
            url="https://portal.ifce.edu.br/institucional/documentos-institucionais/boletim-de-servicos/reitoria/",
            estrategia=(
                "Neste momento, priorizar documentos oficiais já publicados e evitar solicitar novas "
                "declarações até confirmação no decreto regulamentador."
            ),
        ),
    ]


async def call_sei_mcp_prompt(req: SearchRequest) -> Dict[str, str]:
    """
    Integração opcional com um serviço MCP HTTP.
    Defina SEI_MCP_URL para um endpoint compatível com prompt de busca.
    """

    import os

    mcp_url = os.getenv("SEI_MCP_URL")
    if not mcp_url:
        return {
            "status": "não configurado",
            "mensagem": "Defina a variável SEI_MCP_URL para habilitar consulta externa ao MCP do SEI.",
        }

    payload = {
        "prompt": (
            "Localize publicações e portarias no contexto IFCE para o servidor "
            f"{req.nome} com termos adicionais: {', '.join(req.palavras_chave) or 'nenhum'}."
        )
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(mcp_url, json=payload)
            response.raise_for_status()
            data = response.json()
    except Exception as exc:  # noqa: BLE001
        return {"status": "erro", "mensagem": f"Falha na integração MCP: {exc}"}

    return {"status": "ok", "mensagem": str(data)[:2000]}


app = FastAPI(title="Calculadora + Busca RSC-PCCTAE")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/api/calculate")
def calculate(req: ScoreRequest) -> Dict[str, object]:
    try:
        start = parse_date(req.data_inicio_servico)
        anos = years_of_service(start)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    pontos_atividades = round(sum(item.quantidade * item.pontos_unitarios for item in req.atividades), 2)
    pontos_tempo_servico = service_points(anos)
    total = round(pontos_atividades + pontos_tempo_servico, 2)

    return {
        "nome": req.nome,
        "cargo": req.cargo,
        "anos_servico_publico": anos,
        "pontos_tempo_servico": pontos_tempo_servico,
        "pontos_atividades": pontos_atividades,
        "total_pontos": total,
    }


@app.post("/api/search")
async def search(req: SearchRequest) -> Dict[str, object]:
    try:
        recorte_anos = resolve_year_window(req.data_inicio_servico)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    orientacoes = build_search_queries(req)
    mcp_data = await call_sei_mcp_prompt(req)

    return {
        "recorte_anos": recorte_anos,
        "nome_consultado": req.nome,
        "orientacoes_busca": [item.model_dump() for item in orientacoes],
        "integracao_mcp": mcp_data,
    }
