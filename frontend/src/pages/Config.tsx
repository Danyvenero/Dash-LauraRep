import { useState, useEffect } from 'react'
import api from '../services/api'
import toast from 'react-hot-toast'
import FileUpload from '../components/upload/FileUpload'

interface User {
  id: number
  username: string
  created_at: string
  is_active: boolean
}

export default function Config() {
  const [users, setUsers] = useState<User[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [showUpload, setShowUpload] = useState(false)

  useEffect(() => {
    loadUsers()
  }, [])

  const loadUsers = async () => {
    try {
      const response = await api.get('/users/')
      setUsers(response.data)
    } catch (error) {
      toast.error('Erro ao carregar usuários')
    } finally {
      setIsLoading(false)
    }
  }

  const handleDeleteUser = async (userId: number) => {
    if (!confirm('Tem certeza que deseja deletar este usuário?')) return

    try {
      await api.delete(`/users/${userId}`)
      toast.success('Usuário deletado com sucesso')
      loadUsers()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erro ao deletar usuário')
    }
  }

  const handleWipeData = async () => {
    if (!confirm('PERIGO: Esta ação é irreversível e apagará TODOS os dados. Deseja continuar?')) {
      return
    }

    try {
      const response = await api.post('/etl/wipe')
      toast.success(response.data.message || 'Dados limpos com sucesso')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erro ao limpar dados')
    }
  }

  const handleRunETL = async () => {
    try {
      const response = await api.post('/etl/run')
      toast.success(response.data.message || 'ETL executado com sucesso')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erro ao processar dados')
    }
  }

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
        Configurações
      </h1>
      <p className="text-gray-600 dark:text-gray-400 mb-8">
        Gestão de usuários, upload de dados e configurações do sistema
      </p>

      {/* Upload de Dados */}
      <div className="card mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">Upload de Dados</h2>
          <button
            onClick={() => setShowUpload(!showUpload)}
            className="btn-primary"
          >
            {showUpload ? 'Ocultar' : 'Mostrar Upload'}
          </button>
        </div>

        {showUpload && (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium mb-2">
                Upload de Vendas (Anual)
              </label>
              <FileUpload
                type="vendas"
                onSuccess={() => {
                  toast.success('Dados de vendas carregados! Execute o ETL para processar.')
                }}
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">
                Upload de Cotações (Materiais + Ano)
              </label>
              <FileUpload
                type="cotacoes"
                onSuccess={() => {
                  toast.success('Dados de cotações carregados! Execute o ETL para processar.')
                }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Gestão de Usuários */}
      <div className="card mb-6">
        <h2 className="text-xl font-semibold mb-4">Gestão de Usuários</h2>
        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-weg-blue"></div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
                    ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
                    Usuário
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
                    Criado em
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
                    Ações
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                {users.map((user) => (
                  <tr key={user.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                      {user.id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                      {user.username}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {new Date(user.created_at).toLocaleDateString('pt-BR')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <button
                        onClick={() => handleDeleteUser(user.id)}
                        className="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300"
                      >
                        Deletar
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Ações Perigosas */}
      <div className="card border-2 border-red-300 dark:border-red-700">
        <h2 className="text-xl font-semibold mb-4 text-red-600 dark:text-red-400">
          Ações Perigosas
        </h2>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          Cuidado: As ações abaixo não podem ser desfeitas.
        </p>

        <div className="space-y-4">
          <button
            onClick={handleWipeData}
            className="btn-secondary bg-red-600 hover:bg-red-700 text-white"
          >
            Limpar Todos os Dados Brutos e Processados
          </button>

          <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
              Execute o processo de transformação para atualizar os dashboards com os últimos dados carregados.
            </p>
            <button
              onClick={handleRunETL}
              className="btn-primary"
            >
              Processar Dados Brutos e Atualizar Análises
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
