import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface UIState {
  sidebarCollapsed: boolean;
  theme: 'light' | 'dark';
  catalogViewMode: 'grid' | 'list';
  toggleSidebar: () => void;
  toggleTheme: () => void;
  setCatalogViewMode: (mode: 'grid' | 'list') => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      sidebarCollapsed: false,
      theme: 'light',
      catalogViewMode: 'grid',
      toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
      toggleTheme: () =>
        set((s) => {
          const newTheme = s.theme === 'light' ? 'dark' : 'light';
          if (newTheme === 'dark') {
            document.documentElement.classList.add('dark');
          } else {
            document.documentElement.classList.remove('dark');
          }
          return { theme: newTheme };
        }),
      setCatalogViewMode: (mode) => set({ catalogViewMode: mode }),
    }),
    { name: 'mcp-router-ui' }
  )
);

// Apply dark class on initial hydration from localStorage
const initialTheme = useUIStore.getState().theme;
if (initialTheme === 'dark') {
  document.documentElement.classList.add('dark');
}
// Also handle async hydration from persist middleware
useUIStore.subscribe((state) => {
  if (state.theme === 'dark') {
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.classList.remove('dark');
  }
});
