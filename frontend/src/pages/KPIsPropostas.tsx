import { useState, useEffect } from 'react'
import api from '../services/api'
import toast from 'react-hot-toast'
import Plot from 'react-plotly.js'
import { formatPercent, formatNumber } from '../utils/format'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface ComparativoData {
  clientes: Array<{
    cod_cliente: string
    cliente: string
    quantidade: number
    quantidade_faturada: number
    valor_faturado: number
    pct_conversao: number
  }>
  resumo: {
    total_cotado: number
    total_comprado: number
    taxa_conversao: number
  }
}

interface HeatmapData {
  data: number[][]
  clientes: string[]
  produtos: string[]
}

export default function KPIsPropostas() {
  const [comparativoData, setComparativoData] = useState<ComparativoData | null>(null)
  const [heatmapData, setHeatmapData] = useState<HeatmapData | null>(null)
  const [sugestaoEstoque, setSugestaoEstoque] = useState<any[]>([])
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
    loadData()
  }, [filtros, tipoGrafico])

  const loadData = async () => {
    setIsLoading(true)
    try {
      if (tipoGrafico === 'barra') {
        const response = await api.get('/propostas/comparativo', { params: filtros })
        setComparativoData(response.data)
      } else {
        const response = await api.get('/propostas/heatmap', {
          params: {
            ano_inicio: filtros.ano_inicio,
            ano_fim: filtros.ano_fim,
            top_clientes: 15,
            top_produtos: 20,
          },
        })
        setHeatmapData(response.data)
      }
    } catch (error: any) {
      toast.error('Erro ao carregar dados de propostas')
      console.error(error)
    } finally {
      setIsLoading(false)
    }
  }

  const loadSugestaoEstoque = async () => {
    try {
      const response = await api.get('/propostas/sugestao-estoque')
      setSugestaoEstoque(response.data)
    } catch (error) {
      toast.error('Erro ao carregar sugestão de estoque')
    }
  }

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

      {/* Resumo */}
      {comparativoData && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="card">
            <div className="text-sm text-gray-600 dark:text-gray-400">Total Cotado</div>
            <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
              {formatNumber(comparativoData.resumo.total_cotado)}
            </div>
          </div>
          <div className="card">
            <div className="text-sm text-gray-600 dark:text-gray-400">Total Comprado</div>
            <div className="text-2xl font-bold text-green-600 dark:text-green-400">
              {formatNumber(comparativoData.resumo.total_comprado)}
            </div>
          </div>
          <div className="card">
            <div className="text-sm text-gray-600 dark:text-gray-400">Taxa de Conversão</div>
            <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
              {formatPercent(comparativoData.resumo.taxa_conversao)}
            </div>
          </div>
        </div>
      )}

      {/* Gráfico */}
      {isLoading ? (
        <div className="flex items-center justify-center h-96">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-weg-blue"></div>
        </div>
      ) : tipoGrafico === 'barra' && comparativoData ? (
        <div className="card mb-6">
          <h3 className="text-lg font-semibold mb-4">Taxa de Conversão por Cliente (Top {filtros.top_n})</h3>
          <ResponsiveContainer width="100%" height={500}>
            <BarChart data={comparativoData.clientes.slice(0, filtros.top_n)}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-gray-300 dark:stroke-gray-600" />
              <XAxis 
                dataKey="cliente" 
                angle={-45}
                textAnchor="end"
                height={150}
                className="text-gray-600 dark:text-gray-400"
              />
              <YAxis className="text-gray-600 dark:text-gray-400" />
              <Tooltip 
                contentStyle={{
                  backgroundColor: 'rgba(255, 255, 255, 0.95)',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                }}
                formatter={(value: number) => formatPercent(value)}
              />
              <Legend />
              <Bar 
                dataKey="pct_conversao" 
                name="Taxa de Conversão (%)"
                fill="#3b82f6"
                radius={[8, 8, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      ) : tipoGrafico === 'heatmap' && heatmapData ? (
        <div className="card mb-6">
          <h3 className="text-lg font-semibold mb-4">Heatmap: % Não Comprado por Cliente x Produto</h3>
          <Plot
            data={[
              {
                z: heatmapData.data,
                x: heatmapData.produtos,
                y: heatmapData.clientes,
                type: 'heatmap',
                colorscale: 'RdYlBu_r',
                showscale: true,
                colorbar: {
                  title: '% Não Comprado',
                },
              },
            ]}
            layout={{
              height: 600,
              xaxis: { 
                title: 'Produtos (Material)',
                gridcolor: '#e5e7eb',
              },
              yaxis: { 
                title: 'Clientes',
                gridcolor: '#e5e7eb',
              },
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

      {/* Tabela de Dados */}
      {comparativoData && comparativoData.clientes.length > 0 && (
        <div className="card mb-6">
          <h3 className="text-lg font-semibold mb-4">Detalhamento por Cliente</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
                    Cliente
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
                    Qtd Cotada
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
                    Qtd Comprada
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
                    Taxa Conversão
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                {comparativoData.clientes.map((item, idx) => (
                  <tr key={idx} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                      {item.cliente}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                      {formatNumber(item.quantidade)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                      {formatNumber(item.quantidade_faturada)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span
                        className={`font-medium ${
                          item.pct_conversao > 70
                            ? 'text-green-600'
                            : item.pct_conversao > 30
                            ? 'text-yellow-600'
                            : 'text-red-600'
                        }`}
                      >
                        {formatPercent(item.pct_conversao)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Sugestão de Estoque */}
      <div className="card mt-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Sugestão de Lista de Compra para Estoque</h3>
          <div className="flex gap-2">
            <button
              onClick={loadSugestaoEstoque}
              className="btn-secondary"
            >
              Carregar Sugestões
            </button>
            <button
              onClick={() => {
                if (sugestaoEstoque.length === 0) {
                  toast.error('Carregue as sugestões primeiro')
                  return
                }
                // Exportar para CSV
                const csv = [
                  ['Categoria', 'Código do Material', 'Descrição do Produto', 'Sugestão de Giro Mensal'],
                  ...sugestaoEstoque.map((item: any) => [
                    item.Categoria || '',
                    item['Código do Material'] || '',
                    item['Descrição do Produto'] || '',
                    item['Sugestão de Giro Mensal'] || '',
                  ]),
                ]
                  .map((row) => row.map((cell) => `"${cell}"`).join(','))
                  .join('\n')
                
                const blob = new Blob([csv], { type: 'text/csv;charset=utf-8-sig;' })
                const url = window.URL.createObjectURL(blob)
                const link = document.createElement('a')
                link.href = url
                link.setAttribute('download', 'sugestao_estoque.csv')
                document.body.appendChild(link)
                link.click()
                link.remove()
                toast.success('CSV baixado com sucesso!')
              }}
              className="btn-primary"
            >
              Baixar Lista (.csv)
            </button>
          </div>
        </div>
        
        {sugestaoEstoque.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
                    Categoria
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
                    Código Material
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
                    Descrição
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
                    Sugestão Giro Mensal
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                {sugestaoEstoque.map((item: any, idx: number) => (
                  <tr key={idx} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                      {item.Categoria || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                      {item['Código do Material'] || '-'}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900 dark:text-white">
                      {item['Descrição do Produto'] || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                      {formatNumber(item['Sugestão de Giro Mensal'] || 0)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
