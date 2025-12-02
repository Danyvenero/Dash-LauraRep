import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'
import { useThemeStore } from './store/themeStore'

// Aplicar tema ao carregar
const storedTheme = localStorage.getItem('theme-storage')
if (storedTheme) {
  try {
    const theme = JSON.parse(storedTheme)
    if (theme?.state?.isDark) {
      document.documentElement.classList.add('dark')
    }
  } catch (e) {
    // Ignore parse errors
  }
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
