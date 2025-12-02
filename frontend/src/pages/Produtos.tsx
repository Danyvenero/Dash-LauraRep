import { useState, useEffect } from 'react'
import api from '../services/api'
import toast from 'react-hot-toast'
import Plot from 'react-plotly.js'

interface ProdutoMatrix {
  cod_cliente: string
  cliente: string
  material: string
  quantidade: number
  quantidade_faturada: number
  pct_nao_comprado: number
}

export default function Produtos() {
  const [data, setData] = useState<ProdutoMatrix[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [filtros, setFiltros] = useState({
    top_produtos: 20,
    top_clientes: 15,
    ano: null as number | null,
    unidade_negocio: [] as string[],
    paleta: 'Viridis',
  })

  useEffect(() => {
    loadData()
  }, [filtros])

  const loadData = async () => {
    setIsLoading(true)
    try {
      const params: any = {
        top_produtos: filtros.top_produtos,
        top_clientes: filtros.top_clientes,
      }
      if (filtros.ano) params.ano = filtros.ano
      if (filtros.unidade_negocio.length > 0) {
        params.unidade_negocio = filtros.unidade_negocio
      }

      const response = await api.get('/kpis/produtos/matrix', { params })
      setData(response.data)
    } catch (error: any) {
      toast.error('Erro ao carregar dados de produtos')
      console.error(error)
    } finally {
      setIsLoading(false)
    }
  }

  // Preparar dados para o gráfico de bolhas
  const plotData = data.map((item) => ({
    x: item.material,
    y: item.cliente,
    size: item.quantidade,
    color: item.pct_nao_comprado,
    text: `${item.cliente}<br>Material: ${item.material}<br>Qtd Cotada: ${item.quantidade}<br>% Não Comprado: ${item.pct_nao_comprado.toFixed(1)}%`,
  }))

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
        Produtos (Bolhas)
      </h1>
      <p className="text-gray-600 dark:text-gray-400 mb-8">
        Análise visual de clientes vs produtos com métricas de cotação e compra
      </p>

      {/* Filtros */}
      <div className="card mb-6">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">Top N Produtos</label>
            <input
              type="number"
              value={filtros.top_produtos}
              onChange={(e) =>
                setFiltros({ ...filtros, top_produtos: parseInt(e.target.value) })
              }
              className="input"
              min="5"
              max="100"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Top N Clientes</label>
            <input
              type="number"
              value={filtros.top_clientes}
              onChange={(e) =>
                setFiltros({ ...filtros, top_clientes: parseInt(e.target.value) })
              }
              className="input"
              min="5"
              max="50"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Ano</label>
            <select
              value={filtros.ano || ''}
              onChange={(e) =>
                setFiltros({
                  ...filtros,
                  ano: e.target.value ? parseInt(e.target.value) : null,
                })
              }
              className="input"
            >
              <option value="">Todos</option>
              <option value="2023">2023</option>
              <option value="2024">2024</option>
              <option value="2025">2025</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Paleta de Cores</label>
            <select
              value={filtros.paleta}
              onChange={(e) => setFiltros({ ...filtros, paleta: e.target.value })}
              className="input"
            >
              <option value="Viridis">Viridis</option>
              <option value="Blues">Blues</option>
              <option value="Reds">Reds</option>
              <option value="RdYlBu">RdYlBu</option>
            </select>
          </div>
        </div>
      </div>

      {/* Gráfico de Bolhas */}
      {isLoading ? (
        <div className="flex items-center justify-center h-96">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-weg-blue"></div>
        </div>
      ) : data.length > 0 ? (
        <div className="card">
          <Plot
            data={[
              {
                x: plotData.map((d) => d.x),
                y: plotData.map((d) => d.y),
                mode: 'markers',
                type: 'scatter',
                marker: {
                  size: plotData.map((d) => Math.max(10, d.size / 10)),
                  color: plotData.map((d) => d.color),
                  colorscale: filtros.paleta,
                  showscale: true,
                  colorbar: {
                    title: '% Não Comprado',
                  },
                },
                text: plotData.map((d) => d.text),
                hovertemplate: '%{text}<extra></extra>',
              },
            ]}
            layout={{
              title: 'Análise de Bolhas - Clientes vs Produtos',
              xaxis: { 
                title: 'Produtos (Material)',
                gridcolor: '#e5e7eb',
              },
              yaxis: { 
                title: 'Clientes',
                gridcolor: '#e5e7eb',
              },
              height: 600,
              paper_bgcolor: 'transparent',
              plot_bgcolor: 'transparent',
              font: {
                color: document.documentElement.classList.contains('dark') ? '#f3f4f6' : '#374151',
              },
              template: document.documentElement.classList.contains('dark') ? 'plotly_dark' : 'plotly_white',
            }}
            config={{ responsive: true }}
            style={{ width: '100%', height: '100%' }}
          />
        </div>
      ) : (
        <div className="card text-center py-12">
          <p className="text-gray-600 dark:text-gray-400">
            Nenhum dado disponível. Faça upload de dados nas Configurações.
          </p>
        </div>
      )}

      {/* Botões de Ação */}
      {!isLoading && data.length > 0 && (
        <div className="mt-6 flex gap-4">
          <button
            onClick={async () => {
              try {
                // TODO: Implementar export CSV
                toast.info('Funcionalidade em desenvolvimento')
              } catch (error) {
                toast.error('Erro ao exportar CSV')
              }
            }}
            className="btn-secondary"
          >
            Download CSV
          </button>
          <button
            onClick={async () => {
              try {
                // TODO: Implementar export PDF
                toast.info('Funcionalidade em desenvolvimento')
              } catch (error) {
                toast.error('Erro ao gerar PDF')
              }
            }}
            className="btn-primary"
          >
            Gerar PDF por Cliente
          </button>
        </div>
      )}
    </div>
  )
}
