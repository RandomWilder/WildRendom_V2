import { PrizeTemplate } from './prize';

export type PrizePoolStatus = 'unlocked' | 'locked' | 'assigned';

export interface PrizePool {
  id: number;
  name: string;
  description?: string;
  status: PrizePoolStatus;
  total_instances: number;
  instant_win_count: number;
  draw_win_count: number;
  values: {
    retail_total: number;
    cash_total: number;
    credit_total: number;
  };
}

export interface PrizeInstance {
  instanceId: string;
  prizeId: number;
  prize?: PrizeTemplate;
  individualOdds: number;
  status: 'available' | 'discovered' | 'claimed';
  values: {
    retail: number;
    cash: number;
    credit: number;
  };
}

export interface PrizeAllocationRequest {
  prize_template_id: number;
  instance_count: number;
  collective_odds: number;
}

export interface PrizePoolValidation {
  hasInstances: boolean;
  hasDrawWin: boolean;
  oddsTotal: number;
}

export interface PoolAuditEntry {
  id: number;
  action: string;
  userId: number;
  username: string;
  details: Record<string, any>;
  timestamp: string;
}

export interface CreatePoolResponse {
  pool_id: number;
  name: string;
  description?: string;
  total_instances: number;
  values: {
    retail_total: number;
    cash_total: number;
    credit_total: number;
  };
  status: PrizePoolStatus;
}

export interface AllocatePrizeResponse {
  allocated_instances: PrizeInstance[];
  pool_updated_totals: {
    total_instances: number;
    instant_win_count: number;
    draw_win_count: number;
    values: {
      retail_total: number;
      cash_total: number;
      credit_total: number;
    };
  };
}