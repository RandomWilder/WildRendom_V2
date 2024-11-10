// src/types/raffle.ts

export interface Raffle {
    id: number;
    title: string;
    description?: string;
    ticketPrice: number;
    startTime: string;
    endTime: string;
    totalTickets: number;
    availableTickets: number;
    maxTicketsPerUser: number;
    status: RaffleStatus;
    instantWinCount?: number;
    drawConfiguration?: {
      numberOfDraws: number;
      distributionType: 'single' | 'split';
      prizeValuePerDraw: number;
      drawTime: string;
    };
  }
  
  export enum RaffleStatus {
    DRAFT = 'draft',
    COMING_SOON = 'coming_soon',
    ACTIVE = 'active',
    INACTIVE = 'inactive',
    SOLD_OUT = 'sold_out',
    ENDED = 'ended',
    CANCELLED = 'cancelled'
  }
  
  export interface Ticket {
    id: string;
    ticketId: string;
    ticketNumber: string;
    raffleId: number;
    userId: number;
    purchaseTime: string;
    status: TicketStatus;
    isRevealed: boolean;
    revealTime?: string;
    instantWin: boolean;
    transactionId?: number;
  }
  
  export enum TicketStatus {
    AVAILABLE = 'available',
    SOLD = 'sold',
    REVEALED = 'revealed',
    CANCELLED = 'cancelled',
    VOID = 'void'
  }