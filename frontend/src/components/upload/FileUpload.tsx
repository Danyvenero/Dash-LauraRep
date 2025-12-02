import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import api from '../../services/api'
import toast from 'react-hot-toast'

interface FileUploadProps {
  type: 'vendas' | 'cotacoes'
  onSuccess?: () => void
}

export default function FileUpload({ type, onSuccess }: FileUploadProps) {
  const [isUploading, setIsUploading] = useState(false)

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return

    const file = acceptedFiles[0]
    
    // Validar extensão
    if (!file.name.match(/\.(xlsx|xls)$/i)) {
      toast.error('Apenas arquivos Excel (.xlsx ou .xls) são permitidos')
      return
    }

    setIsUploading(true)
    const formData = new FormData()
    formData.append('file', file)

    try {
      const endpoint = type === 'vendas' ? '/uploads/vendas' : '/uploads/cotacoes'
      const response = await api.post(endpoint, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      if (response.data.success) {
        toast.success(response.data.message || 'Arquivo carregado com sucesso!')
        onSuccess?.()
      } else {
        toast.error(response.data.message || 'Arquivo já foi carregado anteriormente')
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erro ao fazer upload do arquivo')
    } finally {
      setIsUploading(false)
    }
  }, [type, onSuccess])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
    },
    maxFiles: 1,
    disabled: isUploading,
  })

  return (
    <div
      {...getRootProps()}
      className={`
        border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
        transition-colors
        ${
          isDragActive
            ? 'border-weg-blue bg-weg-light dark:bg-gray-800'
            : 'border-gray-300 dark:border-gray-600 hover:border-weg-blue'
        }
        ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}
      `}
    >
      <input {...getInputProps()} />
      {isUploading ? (
        <div className="space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-weg-blue mx-auto"></div>
          <p className="text-gray-600 dark:text-gray-400">Enviando arquivo...</p>
        </div>
      ) : (
        <div className="space-y-4">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            stroke="currentColor"
            fill="none"
            viewBox="0 0 48 48"
          >
            <path
              d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-4h4m-4-4v4m0-4v-4m-4 4h.02"
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {isDragActive
                ? 'Solte o arquivo aqui'
                : 'Arraste um arquivo Excel aqui ou clique para selecionar'}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-500 mt-2">
              Apenas arquivos .xlsx ou .xls
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
