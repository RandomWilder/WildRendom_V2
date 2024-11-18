export type PrizeType = 'Instant_Win' | 'Draw_Win' | 'Promotional' | 'Custom';
export type PrizeTier = 'platinum' | 'gold' | 'silver' | 'bronze';

export interface Prize {
  id: number;
  name: string;
  description?: string;
  type: PrizeType;
  tier: PrizeTier;
  tierPriority?: number;
  retailValue: number;
  cashValue: number;
  creditValue: number;
  totalQuantity: number | null;
  availableQuantity: number | null;
  totalClaimed: number;
  winLimitPerUser: number | null;
  winLimitPeriodDays: number | null;
  status: 'active' | 'inactive' | 'depleted' | 'expired';
  claimDeadlineHours: number | null;
  autoClaimCredit: boolean;
  createdAt: string;
  updatedAt?: string;
  createdById: number;
}

export interface PrizeTemplate extends Prize {
  winOdds: number;
  totalAllocated: number;
  expiryDays: number;
  claimProcessorType: 'credit' | 'digital' | 'physical';
}