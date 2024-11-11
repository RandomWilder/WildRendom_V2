export interface Ticket {
    id: string;
    ticketId: string;
    ticketNumber: string;
    raffleId: number;
    raffleTitle: string;
    userId?: number;
    purchaseTime: string;
    endTime: string;
    status: 'available' | 'sold' | 'revealed';
    isRevealed: boolean;
    revealTime?: string;
    instantWin: boolean;
    transactionId?: number;
  }
  
  export interface RaffleTicketGroup {
    raffleId: number;
    raffleTitle: string;
    tickets: Ticket[];
  }