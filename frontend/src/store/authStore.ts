import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import api from '../services/api'

interface User {
  id: number
  username: string
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  setUser: (user: User) => void
  setToken: (token: string) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      
      login: async (username: string, password: string) => {
        const response = await api.post('/auth/login', new URLSearchParams({
          username,
          password,
        }), {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
        })
        
        const { access_token, user_id, username: userUsername } = response.data
        
        set({
          token: access_token,
          user: { id: user_id, username: userUsername },
          isAuthenticated: true,
        })
        
        // Configurar token no axios
        api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
      },
      
      logout: () => {
        set({
          user: null,
          token: null,
          isAuthenticated: false,
        })
        delete api.defaults.headers.common['Authorization']
      },
      
      setUser: (user: User) => set({ user }),
      setToken: (token: string) => {
        set({ token })
        api.defaults.headers.common['Authorization'] = `Bearer ${token}`
      },
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => localStorage),
    }
  )
)
