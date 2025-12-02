import { useState, useEffect } from 'react'
import api from '../services/api'
import toast from 'react-hot-toast'
import { formatCurrency, formatPercent } from '../utils/format'

interface FunilMetrics {
  total_clientes_cotaram: number
  total_clientes_compraram: number
  taxa_conversao_geral: number
  lista_a: Array<{
    cod_cliente: string
    cliente: string
    quantidade: number
    quantidade_faturada: number
    conversao_pct: number
  }>
  lista_b: Array<{
    cod_cliente: string
    cliente: string
    dias_sem_compra: number
    quantidade_faturada: number
  }>
}

export default function Funil() {
  const [metrics, setMetrics] = useState<FunilMetrics | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [filtros, setFiltros] = useState({
    periodo_meses: 12,
    threshold_conversao: 20,
    threshold_dias_risco: 90,
  })

  useEffect(() => {
    loadMetrics()
  }, [filtros])

  const loadMetrics = async () => {
    setIsLoading(true)
    try {
      const response = await api.get('/kpis/funil', {
        params: filtros,
      })
      setMetrics(response.data)
    } catch (error: any) {
      toast.error('Erro ao carregar métricas do funil')
      console.error(error)
    } finally {
      setIsLoading(false)
    }
  }

  const downloadListaA = async () => {
    try {
      const response = await api.get('/reports/csv/funil-lista-a', {
        responseType: 'blob',
      })
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', 'funil_lista_a.csv')
      document.body.appendChild(link)
      link.click()
      link.remove()
      toast.success('CSV baixado com sucesso!')
    } catch (error) {
      toast.error('Erro ao baixar CSV')
    }
  }

  const downloadListaB = async () => {
    try {
      const response = await api.get('/reports/csv/funil-lista-b', {
        responseType: 'blob',
      })
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', 'funil_lista_b.csv')
      document.body.appendChild(link)
      link.click()
      link.remove()
      toast.success('CSV baixado com sucesso!')
    } catch (error) {
      toast.error('Erro ao baixar CSV')
    }
  }

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
        Funil & Ações
      </h1>
      <p className="text-gray-600 dark:text-gray-400 mb-8">
        Identifique clientes que precisam de atenção especial e ações comerciais
      </p>

      {/* Filtros */}
      <div className="card mb-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">Período de Análise (meses)</label>
            <input
              type="number"
              value={filtros.periodo_meses}
              onChange={(e) =>
                setFiltros({ ...filtros, periodo_meses: parseInt(e.target.value) })
              }
              className="input"
              min="1"
              max="24"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              Threshold % Conversão Baixa
            </label>
            <input
              type="number"
              value={filtros.threshold_conversao}
              onChange={(e) =>
                setFiltros({ ...filtros, threshold_conversao: parseFloat(e.target.value) })
              }
              className="input"
              min="0"
              max="100"
              step="5"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Dias sem Compra (Risco)</label>
            <input
              type="number"
              value={filtros.threshold_dias_risco}
              onChange={(e) =>
                setFiltros({ ...filtros, threshold_dias_risco: parseInt(e.target.value) })
              }
              className="input"
              min="30"
              max="365"
              step="10"
            />
          </div>
        </div>
      </div>

      {/* Métricas do Funil */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-weg-blue"></div>
        </div>
      ) : metrics ? (
        <>
          <div className="card mb-6">
            <h2 className="text-xl font-semibold mb-4">Resumo do Funil</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
                <div className="text-sm text-gray-600 dark:text-gray-400">Clientes que Cotaram</div>
                <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                  {metrics.total_clientes_cotaram}
                </div>
              </div>
              <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
                <div className="text-sm text-gray-600 dark:text-gray-400">Clientes que Compraram</div>
                <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                  {metrics.total_clientes_compraram}
                </div>
              </div>
              <div className="bg-purple-50 dark:bg-purple-900/20 p-4 rounded-lg">
                <div className="text-sm text-gray-600 dark:text-gray-400">Taxa de Conversão Geral</div>
                <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                  {formatPercent(metrics.taxa_conversao_geral)}
                </div>
              </div>
            </div>
          </div>

          {/* Listas de Ação */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Lista A */}
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold">Lista A - Baixa Conversão, Alto Volume</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Clientes que cotam muito mas compram pouco
                  </p>
                </div>
                <button onClick={downloadListaA} className="btn-secondary text-sm">
                  Download CSV
                </button>
              </div>
              <div className="max-h-96 overflow-y-auto">
                <table className="min-w-full text-sm">
                  <thead className="bg-gray-50 dark:bg-gray-700 sticky top-0">
                    <tr>
                      <th className="px-4 py-2 text-left">Cliente</th>
                      <th className="px-4 py-2 text-left">Qtd Cotada</th>
                      <th className="px-4 py-2 text-left">Conversão</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                    {metrics.lista_a.slice(0, 20).map((item, idx) => (
                      <tr key={idx} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                        <td className="px-4 py-2">{item.cliente}</td>
                        <td className="px-4 py-2">{item.quantidade.toLocaleString()}</td>
                        <td className="px-4 py-2">
                          <span className="text-red-600 dark:text-red-400 font-medium">
                            {formatPercent(item.conversao_pct)}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Lista B */}
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold">Lista B - Risco de Inatividade</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Clientes com muito tempo sem comprar
                  </p>
                </div>
                <button onClick={downloadListaB} className="btn-secondary text-sm">
                  Download CSV
                </button>
              </div>
              <div className="max-h-96 overflow-y-auto">
                <table className="min-w-full text-sm">
                  <thead className="bg-gray-50 dark:bg-gray-700 sticky top-0">
                    <tr>
                      <th className="px-4 py-2 text-left">Cliente</th>
                      <th className="px-4 py-2 text-left">Dias sem Compra</th>
                      <th className="px-4 py-2 text-left">Última Compra</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                    {metrics.lista_b.slice(0, 20).map((item, idx) => (
                      <tr key={idx} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                        <td className="px-4 py-2">{item.cliente}</td>
                        <td className="px-4 py-2">
                          <span className="text-orange-600 dark:text-orange-400 font-medium">
                            {item.dias_sem_compra}
                          </span>
                        </td>
                        <td className="px-4 py-2">
                          {item.quantidade_faturada > 0 ? 'Sim' : 'Nunca comprou'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </>
      ) : (
        <div className="card text-center py-12">
          <p className="text-gray-600 dark:text-gray-400">
            Nenhum dado disponível. Faça upload de dados nas Configurações.
          </p>
        </div>
      )}
    </div>
  )
}
