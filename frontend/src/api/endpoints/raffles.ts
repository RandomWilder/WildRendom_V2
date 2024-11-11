import apiClient from '../client';
import { cacheService, CacheDuration } from '../../services/cacheService';

export enum RaffleStatus {
  DRAFT = 'draft',
  COMING_SOON = 'coming_soon',
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  SOLD_OUT = 'sold_out',
  ENDED = 'ended',
  CANCELLED = 'cancelled'
}

export interface Raffle {
  id: number;
  title: string;
  description?: string;
  ticketPrice: number;
  totalTickets: number;
  availableTickets: number;
  maxTicketsPerUser: number;
  startTime: string;
  endTime: string;
  status: RaffleStatus;
}

interface RaffleApiResponse {
  id: number;
  title: string;
  description?: string;
  ticket_price: number;
  total_tickets: number;
  available_tickets?: number;
  max_tickets_per_user: number;
  start_time?: string;
  end_time: string;
  status: string;
  prize_pool_id?: number;
}

const CACHE_KEYS = {
  activeRaffles: 'raffles:active',
  raffleDetails: (id: number) => `raffle:${id}`,
  raffleStats: (id: number) => `raffle:${id}:stats`
};

const transformRaffle = (raffle: RaffleApiResponse): Raffle => ({
  id: raffle.id,
  title: raffle.title,
  description: raffle.description,
  ticketPrice: raffle.ticket_price,
  totalTickets: raffle.total_tickets,
  availableTickets: raffle.available_tickets || raffle.total_tickets,
  maxTicketsPerUser: raffle.max_tickets_per_user,
  startTime: raffle.start_time || raffle.end_time,
  endTime: raffle.end_time,
  status: raffle.status as RaffleStatus
});

const raffleEndpoints = {
  getActiveRaffles: async (): Promise<Raffle[]> => {
    try {
      // Check cache first
      const cached = cacheService.get<Raffle[]>(CACHE_KEYS.activeRaffles);
      if (cached) {
        console.log('Returning cached raffles');
        return cached;
      }

      console.log('Fetching fresh raffles data');
      const { data } = await apiClient.get<RaffleApiResponse[]>('/raffles', {
        params: { status: RaffleStatus.ACTIVE }
      });

      // Transform and cache the data
      const transformedRaffles = Array.isArray(data) 
        ? data.map(transformRaffle)
        : [];

      cacheService.set(
        CACHE_KEYS.activeRaffles,
        transformedRaffles,
        CacheDuration.SHORT // 30 seconds
      );

      return transformedRaffles;
    } catch (error) {
      console.error('Raffle endpoint error:', error);
      throw error;
    }
  },

  getRaffle: async (id: number): Promise<Raffle> => {
    const cacheKey = CACHE_KEYS.raffleDetails(id);
    const cached = cacheService.get<Raffle>(cacheKey);
    if (cached) return cached;

    const { data } = await apiClient.get<RaffleApiResponse>(`/raffles/${id}`);
    const transformed = transformRaffle(data);
    
    cacheService.set(cacheKey, transformed, CacheDuration.SHORT);
    return transformed;
  },

  getRaffleStats: async (id: number): Promise<RaffleStats> => {
    // Stats are not cached due to real-time nature
    const { data } = await apiClient.get<RaffleStats>(`/raffles/${id}/stats`);
    return data;
  },

  // Subscribe to raffle updates
  subscribeToRaffle: (id: number, callback: (raffle: Raffle | null) => void) => {
    return cacheService.subscribe(CACHE_KEYS.raffleDetails(id), callback);
  },

  // Manually invalidate cache when needed
  invalidateRaffleCache: (id?: number) => {
    if (id) {
      cacheService.invalidate(CACHE_KEYS.raffleDetails(id));
    } else {
      cacheService.invalidatePattern(/^raffle:/);
    }
  }
};

export interface RaffleStats {
  totalTickets: number;
  soldTickets: number;
  availableTickets: number;
  instantWinsDiscovered: number;
  totalSales: number;
}

export default raffleEndpoints;