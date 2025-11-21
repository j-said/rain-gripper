import { create } from 'zustand';

export const useAuthStore = create((set) => ({
  token: localStorage.getItem('auth_token') || null,
  user: null, // Will hold { user_id, email, name }

  setToken: (token) => {
    localStorage.setItem('auth_token', token);
    set({ token });
  },

  setUser: (user) => set({ user }),

  logout: () => {
    localStorage.removeItem('auth_token');
    set({ token: null, user: null });
  },
}));