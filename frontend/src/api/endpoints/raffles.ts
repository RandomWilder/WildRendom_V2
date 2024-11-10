import apiClient from '../client';

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

// Interface matching API response format
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

// Transform function to convert snake_case to camelCase
const transformRaffle = (raffle: RaffleApiResponse): Raffle => ({
  id: raffle.id,
  title: raffle.title,
  description: raffle.description,
  ticketPrice: raffle.ticket_price,
  totalTickets: raffle.total_tickets,
  availableTickets: raffle.available_tickets || raffle.total_tickets, // fallback if not provided
  maxTicketsPerUser: raffle.max_tickets_per_user,
  startTime: raffle.start_time || raffle.end_time, // fallback to end_time if not provided
  endTime: raffle.end_time,
  status: raffle.status as RaffleStatus
});

const raffleEndpoints = {
  getActiveRaffles: async (): Promise<Raffle[]> => {
    try {
      console.log('Making request to /raffles endpoint');
      const { data } = await apiClient.get<RaffleApiResponse[]>('/raffles', {
        params: {
          status: RaffleStatus.ACTIVE
        }
      });
      
      console.log('Raw API response:', data);
      
      // Transform each raffle to match our interface
      const transformedRaffles = Array.isArray(data) 
        ? data.map(transformRaffle)
        : [];

      console.log('Transformed raffles:', transformedRaffles);
      
      return transformedRaffles;
    } catch (error) {
      console.error('Raffle endpoint error:', error);
      throw error;
    }
  },

  getRaffle: async (id: number): Promise<Raffle> => {
    const { data } = await apiClient.get<RaffleApiResponse>(`/raffles/${id}`);
    return transformRaffle(data);
  },

  getRaffleStats: async (id: number): Promise<RaffleStats> => {
    const { data } = await apiClient.get<RaffleStats>(`/raffles/${id}/stats`);
    return data;
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