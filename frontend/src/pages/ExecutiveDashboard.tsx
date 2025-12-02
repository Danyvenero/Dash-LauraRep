import { useState, useEffect } from 'react'
import api from '../services/api'
import toast from 'react-hot-toast'
import { formatCurrency, formatPercent } from '../utils/format'
import LineChart from '../components/charts/LineChart'

interface ExecutiveKPIs {
  entrada_pedidos: string
  valor_carteira: string
  faturamento: string
}

export default function ExecutiveDashboard() {
  const [kpis, setKpis] = useState<ExecutiveKPIs | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [trendData, setTrendData] = useState<any[]>([])

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setIsLoading(true)
    try {
      const [kpisResponse, trendsResponse] = await Promise.all([
        api.get('/kpis/gerais'),
        api.get('/trends/mensal', { params: { meses: 12 } }),
      ])
      
      setKpis(kpisResponse.data)
      
      // Preparar dados de tendência
      if (trendsResponse.data && trendsResponse.data.length > 0) {
        setTrendData(trendsResponse.data.map((item: any) => ({
          mes: item.mes,
          entrada: item.entrada || 0,
          carteira: item.carteira || 0,
          faturamento: item.faturamento || 0,
        })))
      }
    } catch (error: any) {
      toast.error('Erro ao carregar dados do dashboard executivo')
      console.error(error)
    } finally {
      setIsLoading(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-weg-blue"></div>
      </div>
    )
  }

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
        Dashboard Executivo
      </h1>
      <p className="text-gray-600 dark:text-gray-400 mb-8">
        Visão consolidada das principais métricas de performance comercial
      </p>

      {/* KPIs Principais */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="card bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20">
          <div className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">
            Entrada de Pedidos
          </div>
          <div className="text-4xl font-bold text-blue-600 dark:text-blue-400">
            {kpis?.entrada_pedidos || 'R$ 0,00'}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400 mt-2">
            Soma de 'Vlr. Entrada'
          </div>
        </div>

        <div className="card bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20">
          <div className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">
            Valor em Carteira
          </div>
          <div className="text-4xl font-bold text-green-600 dark:text-green-400">
            {kpis?.valor_carteira || 'R$ 0,00'}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400 mt-2">
            Soma de 'Vlr. Carteira'
          </div>
        </div>

        <div className="card bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20">
          <div className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">
            Faturamento (ROL)
          </div>
          <div className="text-4xl font-bold text-purple-600 dark:text-purple-400">
            {kpis?.faturamento || 'R$ 0,00'}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400 mt-2">
            Soma de 'Vlr. ROL'
          </div>
        </div>
      </div>

      {/* Gráfico de Tendência */}
      {trendData.length > 0 ? (
        <div className="card mb-6">
          <h3 className="text-lg font-semibold mb-4">Evolução dos Últimos 12 Meses</h3>
          <LineChart
            data={trendData}
            lines={[
              { dataKey: 'entrada', name: 'Entrada de Pedidos', color: '#3b82f6' },
              { dataKey: 'carteira', name: 'Valor em Carteira', color: '#10b981' },
              { dataKey: 'faturamento', name: 'Faturamento', color: '#8b5cf6' },
            ]}
            xKey="mes"
            height={400}
          />
        </div>
      ) : (
        <div className="card text-center py-12">
          <p className="text-gray-600 dark:text-gray-400">
            Dados de tendência serão exibidos aqui quando disponíveis.
          </p>
        </div>
      )}

      {/* Alertas e Insights */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">📊 Insights Rápidos</h3>
          <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
            <li>• Verifique a página de Funil para clientes que precisam de atenção</li>
            <li>• Analise KPIs por Cliente para identificar oportunidades</li>
            <li>• Revise a análise de Propostas para gaps de conversão</li>
          </ul>
        </div>

        <div className="card">
          <h3 className="text-lg font-semibold mb-4">⚡ Ações Recomendadas</h3>
          <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
            <li>• Faça upload de dados atualizados nas Configurações</li>
            <li>• Execute o ETL para processar novos dados</li>
            <li>• Exporte relatórios para análise detalhada</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
