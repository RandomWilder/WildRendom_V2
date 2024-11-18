
import { create } from 'zustand';

interface PrizeTemplate {

  id: string;

  name: string;

  // Add other template properties as needed

}



interface PrizeTemplateStore {

  templates: PrizeTemplate[];

  isLoading: boolean;

  error: string | null;

  fetchTemplates: () => Promise<void>;

}



export const usePrizeTemplateStore = create<PrizeTemplateStore>((set) => ({

  templates: [],

  isLoading: false,

  error: null,

  fetchTemplates: async () => {

    set({ isLoading: true });

    try {

      // Implement your fetch logic here

      const templates: PrizeTemplate[] = [];

      set({ templates, error: null });

    } catch (error) {

      set({ error: 'Failed to fetch templates' });

    } finally {

      set({ isLoading: false });

    }

  },

}));
