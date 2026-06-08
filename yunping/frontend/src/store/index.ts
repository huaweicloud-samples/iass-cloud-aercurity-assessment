import { create } from 'zustand';

interface AppState {
  token: string;
  userInfo: any | null;
  currentBaseId: string;
  currentBaseName: string;
  setToken: (token: string) => void;
  setUserInfo: (user: any) => void;
  setCurrentBase: (id: string, name: string) => void;
  logout: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  token: localStorage.getItem('token') || '',
  userInfo: null,
  currentBaseId: '',
  currentBaseName: '',
  setToken: (token) => {
    localStorage.setItem('token', token);
    set({ token });
  },
  setUserInfo: (user) => set({ userInfo: user }),
  setCurrentBase: (id, name) => set({ currentBaseId: id, currentBaseName: name }),
  logout: () => {
    localStorage.removeItem('token');
    set({ token: '', userInfo: null, currentBaseId: '', currentBaseName: '' });
  },
}));
