import { create } from 'zustand'

type Toast = { id: string, type: 'success'|'error', message: string }

interface UIState {
  toasts: Toast[]
  pushToast: (t: Omit<Toast,'id'>) => void
  removeToast: (id: string) => void
}

export const useUIStore = create<UIState>((set) => ({
  toasts: [],
  pushToast: (t) => set((s) => ({ toasts: [...s.toasts, { ...t, id: Math.random().toString(36).slice(2) }] })),
  removeToast: (id) => set((s) => ({ toasts: s.toasts.filter(x=>x.id!==id) })),
}))

