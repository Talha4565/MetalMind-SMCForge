import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { STORAGE_KEYS } from '@/config/constants';

type ThemeMode = 'light' | 'dark';

interface UiState {
  themeMode: ThemeMode;
  sidebarOpen: boolean;
  notificationsOpen: boolean;
}

interface UiActions {
  toggleTheme: () => void;
  setThemeMode: (mode: ThemeMode) => void;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  toggleNotifications: () => void;
  setNotificationsOpen: (open: boolean) => void;
}

type UiStore = UiState & UiActions;

/**
 * UI Store
 * Manages UI state (theme, sidebar, etc.)
 */
export const useUiStore = create<UiStore>()(
  persist(
    (set) => ({
      // State
      themeMode: 'light',
      sidebarOpen: true,
      notificationsOpen: false,

      // Actions
      toggleTheme: () =>
        set((state) => ({
          themeMode: state.themeMode === 'light' ? 'dark' : 'light',
        })),

      setThemeMode: (mode) =>
        set({ themeMode: mode }),

      toggleSidebar: () =>
        set((state) => ({
          sidebarOpen: !state.sidebarOpen,
        })),

      setSidebarOpen: (open) =>
        set({ sidebarOpen: open }),

      toggleNotifications: () =>
        set((state) => ({
          notificationsOpen: !state.notificationsOpen,
        })),

      setNotificationsOpen: (open) =>
        set({ notificationsOpen: open }),
    }),
    {
      name: STORAGE_KEYS.theme,
      partialize: (state) => ({
        themeMode: state.themeMode,
      }),
    }
  )
);
