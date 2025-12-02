import { useState, useEffect } from 'react'
import api from '../services/api'
import toast from 'react-hot-toast'
import { formatCurrency, formatDate, formatPercent } from '../utils/format'
import ScatterChart from '../components/charts/ScatterChart'
import LineChart from '../components/charts/LineChart'

interface KPICliente {
  cod_cliente: string
  cliente: string
  ultima_compra: string | null
  total_comprado_valor: number
  total_comprado_qtd: number
  mix_produtos: number
  unidades_negocio: number
  dias_sem_compra: number
  total_cotado_qtd: number
  pct_mix_produtos: number
  pct_nao_comprado: number
}

export default function KPIsCliente() {
  const [kpis, setKpis] = useState<KPICliente[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [filtros, setFiltros] = useState({
    ano_inicio: 2024,
    ano_fim: 2024,
    mes_inicio: 1,
    mes_fim: 12,
    top_n: 20,
  })

  useEffect(() => {
    loadKPIs()
  }, [filtros])

  const loadKPIs = async () => {
    setIsLoading(true)
    try {
      const response = await api.post('/kpis/cliente', filtros)
      setKpis(response.data)
    } catch (error: any) {
      toast.error('Erro ao carregar KPIs por cliente')
      console.error(error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
        KPIs por Cliente
      </h1>
      <p className="text-gray-600 dark:text-gray-400 mb-8">
        Análise detalhada do comportamento de compra e cotação de cada cliente
      </p>

      {/* Filtros */}
      <div className="card mb-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">
              Ano (Início - Fim)
            </label>
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
            <label className="block text-sm font-medium mb-2">Top N</label>
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

      {/* Gráfico Scatter */}
      {!isLoading && kpis.length > 0 && (
        <div className="card mb-6">
          <h3 className="text-lg font-semibold mb-4">Valor Faturado x Dias sem Compra</h3>
          <ScatterChart
            data={kpis.map((kpi) => ({
              x: kpi.total_comprado_valor,
              y: kpi.dias_sem_compra,
              size: kpi.mix_produtos * 2,
              name: kpi.cliente,
            }))}
            xLabel="Valor Total Comprado (R$)"
            yLabel="Dias sem Compra"
            height={400}
          />
        </div>
      )}

      {/* Tabela */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-weg-blue"></div>
        </div>
      ) : (
        <div className="card overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Cliente
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Valor Comprado
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Dias sem Compra
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Mix Produtos
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  % Não Comprado
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {kpis.map((kpi) => (
                <tr key={kpi.cod_cliente} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900 dark:text-white">
                      {kpi.cliente}
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                      {kpi.cod_cliente}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    {formatCurrency(kpi.total_comprado_valor)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    {kpi.dias_sem_compra}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    {kpi.mix_produtos}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span
                      className={`font-medium ${
                        kpi.pct_nao_comprado > 50
                          ? 'text-red-600'
                          : kpi.pct_nao_comprado > 25
                          ? 'text-yellow-600'
                          : 'text-green-600'
                      }`}
                    >
                      {formatPercent(kpi.pct_nao_comprado)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Botão Download CSV */}
      {!isLoading && kpis.length > 0 && (
        <div className="mt-4">
          <button
            onClick={async () => {
              try {
                const response = await api.get('/reports/csv/kpis-cliente', {
                  responseType: 'blob',
                })
                const url = window.URL.createObjectURL(new Blob([response.data]))
                const link = document.createElement('a')
                link.href = url
                link.setAttribute('download', 'kpis_cliente.csv')
                document.body.appendChild(link)
                link.click()
                link.remove()
                toast.success('CSV baixado com sucesso!')
              } catch (error) {
                toast.error('Erro ao baixar CSV')
              }
            }}
            className="btn-secondary"
          >
            Download CSV
          </button>
        </div>
      )}
    </div>
  )
}
