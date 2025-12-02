import { useEffect, useState } from 'react'
import api from '../services/api'
import toast from 'react-hot-toast'
import { formatCurrency } from '../utils/format'

interface KPIsGerais {
  entrada_pedidos: string
  valor_carteira: string
  faturamento: string
}

export default function Overview() {
  const [kpis, setKpis] = useState<KPIsGerais | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    loadKPIs()
  }, [])

  const loadKPIs = async () => {
    try {
      const response = await api.get('/kpis/gerais')
      setKpis(response.data)
    } catch (error: any) {
      toast.error('Erro ao carregar KPIs')
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
        Visão Geral
      </h1>
      <p className="text-gray-600 dark:text-gray-400 mb-8">
        Principais indicadores de performance comercial
      </p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <div className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
            Entrada de Pedidos
          </div>
          <div className="text-3xl font-bold text-weg-blue">
            {kpis?.entrada_pedidos || 'R$ 0,00'}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400 mt-2">
            Soma de 'Vlr. Entrada'
          </div>
        </div>

        <div className="card">
          <div className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
            Valor em Carteira
          </div>
          <div className="text-3xl font-bold text-green-600">
            {kpis?.valor_carteira || 'R$ 0,00'}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400 mt-2">
            Soma de 'Vlr. Carteira'
          </div>
        </div>

        <div className="card">
          <div className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
            Faturamento (ROL)
          </div>
          <div className="text-3xl font-bold text-purple-600">
            {kpis?.faturamento || 'R$ 0,00'}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400 mt-2">
            Soma de 'Vlr. ROL'
          </div>
        </div>
      </div>
    </div>
  )
}
