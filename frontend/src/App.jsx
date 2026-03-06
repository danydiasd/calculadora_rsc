import { useMemo, useState } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

const orientacoes = [
  'Ofício-Circular no 17/2026/GAB-PROGEP/PROGEP/REITORIA-IFCE',
  'SIPPAGweb: use Transparência > Documentos > Portarias e preencha interessado + palavra-chave.',
  'SEI/IFCE: na pesquisa avançada, combine nome em aspas, unidade geradora e tipo de documento.',
  'Boletim de Serviços: prefira busca no Google com "boletim de serviços" "NOME" filetype:pdf site:ifce.edu.br.',
]

function App() {
  const [form, setForm] = useState({
    nome: '',
    cargo: '',
    data_inicio_servico: '',
    palavra1: '',
    palavra2: '',
    unidade_geradora: '',
    tipo_documento: 'Portaria',
  })

  const [atividades, setAtividades] = useState([
    { categoria: 'Projetos institucionais', quantidade: 0, pontos_unitarios: 2 },
    { categoria: 'Publicações técnicas', quantidade: 0, pontos_unitarios: 3 },
    { categoria: 'Comissões / designações', quantidade: 0, pontos_unitarios: 1.5 },
  ])

  const [resultado, setResultado] = useState(null)
  const [busca, setBusca] = useState(null)
  const [erro, setErro] = useState('')
  const [loading, setLoading] = useState(false)

  const palavrasChave = useMemo(
    () => [form.palavra1, form.palavra2].map((p) => p.trim()).filter(Boolean),
    [form.palavra1, form.palavra2]
  )

  const atualizarCampo = (key, value) => setForm((f) => ({ ...f, [key]: value }))

  const atualizarAtividade = (idx, key, value) => {
    setAtividades((items) => items.map((item, i) => (i === idx ? { ...item, [key]: Number(value) } : item)))
  }

  const calcular = async (e) => {
    e.preventDefault()
    setErro('')
    setLoading(true)

    try {
      const [calcRes, searchRes] = await Promise.all([
        fetch(`${API_BASE}/api/calculate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            nome: form.nome,
            cargo: form.cargo,
            data_inicio_servico: form.data_inicio_servico,
            atividades,
          }),
        }),
        fetch(`${API_BASE}/api/search`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            nome: form.nome,
            palavras_chave: palavrasChave,
            unidade_geradora: form.unidade_geradora,
            tipo_documento: form.tipo_documento,
          }),
        }),
      ])

      if (!calcRes.ok) throw new Error('Falha no cálculo de pontos.')
      if (!searchRes.ok) throw new Error('Falha na busca de documentos.')

      setResultado(await calcRes.json())
      setBusca(await searchRes.json())
    } catch (err) {
      setErro(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="container">
      <h1>RSC-PCCTAE • Busca de documentos + Calculadora</h1>
      <p className="subtitle">Página  para cálculo RSC  e orientação de busca nominal</p>

      <section className="card">
        <h2>Documento base</h2>
        <img className="oficio-image" src="/oficio-anexo.svg" alt="Ofício-Circular 17/2026 PROGEP IFCE" />
      </section>

      <section className="card">
        <h2>Dados do servidor</h2>
        <form onSubmit={calcular}>
          <div className="grid">
            <label>
              Nome
              <input value={form.nome} onChange={(e) => atualizarCampo('nome', e.target.value)} required />
            </label>
            <label>
              Cargo
              <input value={form.cargo} onChange={(e) => atualizarCampo('cargo', e.target.value)} required />
            </label>
            <label>
              Início no serviço público
              <input
                type="date"
                value={form.data_inicio_servico}
                onChange={(e) => atualizarCampo('data_inicio_servico', e.target.value)}
                required
              />
            </label>
            <label>
              Unidade geradora (SEI)
              <input value={form.unidade_geradora} onChange={(e) => atualizarCampo('unidade_geradora', e.target.value)} />
            </label>
            <label>
              Tipo de documento
              <input value={form.tipo_documento} onChange={(e) => atualizarCampo('tipo_documento', e.target.value)} />
            </label>
            <label>
              Palavra-chave 1
              <input value={form.palavra1} onChange={(e) => atualizarCampo('palavra1', e.target.value)} />
            </label>
            <label>
              Palavra-chave 2
              <input value={form.palavra2} onChange={(e) => atualizarCampo('palavra2', e.target.value)} />
            </label>
          </div>

          <h3>Atividades para pontuação</h3>
          {atividades.map((atv, idx) => (
            <div className="atividade" key={atv.categoria}>
              <strong>{atv.categoria}</strong>
              <label>
                Quantidade
                <input
                  type="number"
                  min="0"
                  step="1"
                  value={atv.quantidade}
                  onChange={(e) => atualizarAtividade(idx, 'quantidade', e.target.value)}
                />
              </label>
              <label>
                Pontos/unit
                <input
                  type="number"
                  min="0"
                  step="0.5"
                  value={atv.pontos_unitarios}
                  onChange={(e) => atualizarAtividade(idx, 'pontos_unitarios', e.target.value)}
                />
              </label>
            </div>
          ))}

          <button disabled={loading}>{loading ? 'Calculando...' : 'Calcular e buscar'}</button>
        </form>
        {erro && <p className="error">{erro}</p>}
      </section>

      <section className="card">
        <h2>Orientações (baseadas no Ofício-Circular nº 17/2026/GAB-PROGEP/PROGEP/REITORIA-IFCE)</h2>
        <ul>
          {orientacoes.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>

      {resultado && (
        <section className="card result">
          <h2>Resultado da calculadora</h2>
          <p><strong>Servidor:</strong> {resultado.nome}</p>
          <p><strong>Cargo:</strong> {resultado.cargo}</p>
          <p><strong>Anos de serviço público:</strong> {resultado.anos_servico_publico}</p>
          <p><strong>Pontos de tempo de serviço:</strong> {resultado.pontos_tempo_servico}</p>
          <p><strong>Pontos de atividades:</strong> {resultado.pontos_atividades}</p>
          <p><strong>Total:</strong> {resultado.total_pontos}</p>
        </section>
      )}

      {busca && (
        <section className="card">
          <h2>Rotas de busca para "{busca.nome_consultado}"</h2>
          {busca.orientacoes_busca.map((item) => (
            <article key={item.url} className="search-item">
              <h3>{item.fonte}</h3>
              <p>{item.estrategia}</p>
              <a href={item.url} target="_blank" rel="noreferrer">{item.titulo}</a>
            </article>
          ))}
          <p><strong>Integração MCP (SEI):</strong> {busca.integracao_mcp?.mensagem}</p>
        </section>
      )}

      <footer className="footer">Página em React consumindo API Python</footer>
    </main>
  )
}

export default App
