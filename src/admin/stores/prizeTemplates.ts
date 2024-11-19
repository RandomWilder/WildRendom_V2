import { create } from 'zustand';
import { apiClient } from '@/api/client';
import { PrizeTemplate } from '@/types/prize';

interface PrizeTemplateStore {
  templates: PrizeTemplate[];
  isLoading: boolean;
  error: string | null;
  fetchTemplates: () => Promise<void>;
  createTemplate: (template: Partial<PrizeTemplate>) => Promise<void>;
}

export const usePrizeTemplateStore = create<PrizeTemplateStore>((set) => ({
  templates: [],
  isLoading: false,
  error: null,

  fetchTemplates: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiClient.get<PrizeTemplate[]>('/api/admin/prizes/');
      set({ templates: response.data });
    } catch (error: any) {
      set({ error: error.response?.data?.error || 'Failed to fetch templates' });
      throw error;
    } finally {
      set({ isLoading: false });
    }
  },

  createTemplate: async (template) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiClient.post('/api/admin/prizes/create', template);
      set((state) => ({
        templates: [...state.templates, response.data]
      }));
    } catch (error: any) {
      set({ error: error.response?.data?.error || 'Failed to create template' });
      throw error;
    } finally {
      set({ isLoading: false });
    }
  }
}));
