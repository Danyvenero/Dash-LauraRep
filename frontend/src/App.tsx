import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { useAuthStore } from './store/authStore'
import Login from './pages/Login'
import Overview from './pages/Overview'
import ExecutiveDashboard from './pages/ExecutiveDashboard'
import KPIsCliente from './pages/KPIsCliente'
import KPIsPropostas from './pages/KPIsPropostas'
import Produtos from './pages/Produtos'
import Funil from './pages/Funil'
import Config from './pages/Config'
import Layout from './components/layout/Layout'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  
  return <>{children}</>
}

function App() {
  return (
    <>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/"
            element={
              <PrivateRoute>
                <Layout />
              </PrivateRoute>
            }
          >
            <Route index element={<Navigate to="/overview" replace />} />
            <Route path="overview" element={<Overview />} />
            <Route path="executivo" element={<ExecutiveDashboard />} />
            <Route path="kpis-cliente" element={<KPIsCliente />} />
            <Route path="kpis-propostas" element={<KPIsPropostas />} />
            <Route path="produtos" element={<Produtos />} />
            <Route path="funil" element={<Funil />} />
            <Route path="config" element={<Config />} />
          </Route>
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" />
    </>
  )
}

export default App
