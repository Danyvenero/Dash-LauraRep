import { useState, useEffect } from 'react'
import api from '../services/api'
import toast from 'react-hot-toast'
import Plot from 'react-plotly.js'

export default function KPIsPropostas() {
  const [data, setData] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [tipoGrafico, setTipoGrafico] = useState<'barra' | 'heatmap'>('barra')
  const [filtros, setFiltros] = useState({
    ano_inicio: 2020,
    ano_fim: 2025,
    mes_inicio: 1,
    mes_fim: 12,
    top_n: 20,
  })

  useEffect(() => {
    // TODO: Implementar carregamento de dados de propostas
    setIsLoading(false)
  }, [filtros])

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
        KPIs de Propostas e Análise de Gaps
      </h1>
      <p className="text-gray-600 dark:text-gray-400 mb-8">
        Identifique oportunidades de venda analisando o que seus clientes cotam vs. o que eles e o mercado compram
      </p>

      {/* Filtros */}
      <div className="card mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">Ano (Início - Fim)</label>
            <div className="flex gap-2">
              <input
                type="number"
                value={filtros.ano_inicio}
                onChange={(e) =>
                  setFiltros({ ...filtros, ano_inicio: parseInt(e.target.value) })
                }
                className="input"
                min="2020"
                max="2025"
              />
              <input
                type="number"
                value={filtros.ano_fim}
                onChange={(e) =>
                  setFiltros({ ...filtros, ano_fim: parseInt(e.target.value) })
                }
                className="input"
                min="2020"
                max="2025"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Mês (Início - Fim)</label>
            <div className="flex gap-2">
              <input
                type="number"
                value={filtros.mes_inicio}
                onChange={(e) =>
                  setFiltros({ ...filtros, mes_inicio: parseInt(e.target.value) })
                }
                className="input"
                min="1"
                max="12"
              />
              <input
                type="number"
                value={filtros.mes_fim}
                onChange={(e) =>
                  setFiltros({ ...filtros, mes_fim: parseInt(e.target.value) })
                }
                className="input"
                min="1"
                max="12"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Top N Clientes</label>
            <input
              type="number"
              value={filtros.top_n}
              onChange={(e) =>
                setFiltros({ ...filtros, top_n: parseInt(e.target.value) })
              }
              className="input"
              min="1"
              max="100"
            />
          </div>
        </div>
      </div>

      {/* Tipo de Gráfico */}
      <div className="card mb-6">
        <div className="flex gap-4">
          <label className="flex items-center">
            <input
              type="radio"
              value="barra"
              checked={tipoGrafico === 'barra'}
              onChange={(e) => setTipoGrafico(e.target.value as 'barra' | 'heatmap')}
              className="mr-2"
            />
            Comparativo (Barra)
          </label>
          <label className="flex items-center">
            <input
              type="radio"
              value="heatmap"
              checked={tipoGrafico === 'heatmap'}
              onChange={(e) => setTipoGrafico(e.target.value as 'barra' | 'heatmap')}
              className="mr-2"
            />
            Heatmap
          </label>
        </div>
      </div>

      {/* Gráfico */}
      {isLoading ? (
        <div className="flex items-center justify-center h-96">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-weg-blue"></div>
        </div>
      ) : (
        <div className="card">
          <p className="text-gray-600 dark:text-gray-400 text-center py-12">
            Funcionalidade em desenvolvimento. Em breve você poderá visualizar análises de propostas aqui.
          </p>
        </div>
      )}

      {/* Sugestão de Estoque */}
      <div className="card mt-6">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Sugestão de Lista de Compra para Estoque</h3>
          <button
            onClick={() => {
              toast.info('Funcionalidade em desenvolvimento')
            }}
            className="btn-primary"
          >
            Gerar e Baixar Lista (.xlsx)
          </button>
        </div>
      </div>
    </div>
  )
}
