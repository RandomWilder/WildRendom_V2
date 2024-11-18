import { create } from 'zustand';
import { PrizePool, PrizeInstance, PrizeAllocationRequest, PrizePoolValidation } from '@/types/prize-pool';
import { apiClient } from '@/api/client';

interface PrizePoolStore {
  pools: PrizePool[];
  selectedPool: PrizePool | null;
  isLoading: boolean;
  error: string | null;
  fetchPools: () => Promise<void>;
  createPool: (data: Pick<PrizePool, 'name' | 'description'>) => Promise<PrizePool>;
  lockPool: (poolId: number) => Promise<{ success: boolean; validation: PrizePoolValidation }>;
  allocatePrize: (poolId: number, data: PrizeAllocationRequest) => Promise<PrizeInstance[]>;
  setSelectedPool: (pool: PrizePool | null) => void;
}

export const usePrizePoolStore = create<PrizePoolStore>((set, get) => ({
  pools: [],
  selectedPool: null,
  isLoading: false,
  error: null,

  fetchPools: async () => {
    try {
      set({ isLoading: true, error: null });
      const response = await apiClient.get<PrizePool[]>('/api/admin/prizes/pools');
      set({ pools: response.data, isLoading: false });
    } catch (error: any) {
      set({ 
        error: error.response?.data?.error || 'Failed to fetch prize pools',
        isLoading: false 
      });
    }
  },

  createPool: async (data) => {
    try {
      set({ isLoading: true, error: null });
      const response = await apiClient.post<PrizePool>('/api/admin/prizes/pools', data);
      const newPool = response.data;
      set(state => ({
        pools: [...state.pools, newPool],
        isLoading: false
      }));
      return newPool;
    } catch (error: any) {
      set({ 
        error: error.response?.data?.error || 'Failed to create prize pool',
        isLoading: false 
      });
      throw error;
    }
  },

  lockPool: async (poolId) => {
    try {
      set({ isLoading: true, error: null });
      const response = await apiClient.put<{
        success: boolean;
        validation: PrizePoolValidation;
      }>(`/api/prizes/pools/${poolId}/lock`);

      if (response.data.success) {
        set(state => ({
          pools: state.pools.map(pool =>
            pool.id === poolId ? { ...pool, status: 'locked' } : pool
          ),
          isLoading: false
        }));
      }
      return response.data;
    } catch (error: any) {
      set({ 
        error: error.response?.data?.error || 'Failed to lock prize pool',
        isLoading: false 
      });
      throw error;
    }
  },

  allocatePrize: async (poolId, data) => {
    try {
      set({ isLoading: true, error: null });
      const response = await apiClient.post<{ allocated_instances: PrizeInstance[] }>(
        `/api/admin/prizes/pools/${poolId}/allocate`,
        data
      );
      
      // Update pool instance counts using snake_case format
      const pool = get().pools.find(p => p.id === poolId);
      if (pool) {
        set(state => ({
          pools: state.pools.map(p =>
            p.id === poolId
              ? {
                  ...p,
                  total_instances: p.total_instances + data.instanceCount,
                  instant_win_count:
                    p.instant_win_count + (data.instanceCount > 1 ? data.instanceCount : 0),
                  draw_win_count: p.draw_win_count + (data.instanceCount === 1 ? 1 : 0),
                  values: {
                    ...p.values,
                    // Update values if needed based on the new allocation
                    retail_total: p.values.retail_total,
                    cash_total: p.values.cash_total,
                    credit_total: p.values.credit_total,
                  }
                }
              : p
          ),
          isLoading: false
        }));
      }
      
      return response.data.allocated_instances;
    } catch (error: any) {
      set({ 
        error: error.response?.data?.error || 'Failed to allocate prize',
        isLoading: false 
      });
      throw error;
    }
  },

  setSelectedPool: (pool) => set({ selectedPool: pool })
}));