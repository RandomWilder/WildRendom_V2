export interface TicketPurchaseRequest {
    quantity: number;
  }
  
  export interface PurchasedTicket {
    ticket_id: string;
    ticket_number: string;
    purchase_time: string;
    status: 'available' | 'sold' | 'revealed';
    transaction_id: string;
  }
  
  export interface TicketPurchaseResponse {
    tickets: PurchasedTicket[];
    transaction: {
      amount: number;
      credits_remaining: number;
    };
  }
  
  export interface TicketState {
    id: string;
    ticketId: string;
    ticketNumber: string;
    raffleId: number;
    raffleTitle: string;
    endTime: string;
    isRevealed: boolean;
    instantWin: boolean;
    purchaseTime: string;
    transactionId: string;
    status: 'available' | 'sold' | 'revealed';
  }