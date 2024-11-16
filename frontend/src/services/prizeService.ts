// src/services/prizeService.ts

import { apiClient } from '../api/client';

export interface PrizeTemplate {
  name: string;
  type: string;
  tier: string;
  retail_value: string;
  cash_value: string;
  credit_value: string;
  status: string;
  description: string | null;
  created_at: string;
  updated_at: string | null;
  total_allocated: number;
  total_claimed: number;
}

export const fetchPrizeTemplates = async (token: string) => {
  try {
    const response = await apiClient.get<PrizeTemplate[]>('/api/admin/prizes/', {  // Note the trailing slash
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error fetching prize templates:', error);
    throw error;
  }
};