import { useEffect } from 'react'
import { useThemeStore } from '../store/themeStore'

export function useDarkMode() {
  const { isDark, setTheme } = useThemeStore()

  useEffect(() => {
    // Aplicar tema ao montar
    setTheme(isDark)
  }, [isDark, setTheme])

  return isDark
}
