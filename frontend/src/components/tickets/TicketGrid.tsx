import { useEffect, useMemo, useState } from 'react';
import { Loader2 } from 'lucide-react';
import { useTicketStore } from '@/lib/stores/ticketStore';
import { RaffleTicketGroup, RaffleTicket } from './RaffleTicketGroup';
import { Button } from '@/components/ui/button';

const TICKETS_PER_PAGE = 12;

type StoreTicket = {
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
};

export const TicketGrid = () => {
  const { tickets, isLoading, error, fetchUserTickets, revealTickets } = useTicketStore();
  const [displayCount, setDisplayCount] = useState(TICKETS_PER_PAGE);
  
  useEffect(() => {
    fetchUserTickets();
  }, [fetchUserTickets]);

  const groupedTickets = useMemo(() => {
    const groups: Record<string, RaffleTicket[]> = {};
    
    (tickets as StoreTicket[]).slice(0, displayCount).forEach(ticket => {
      if (!groups[ticket.raffleId]) {
        groups[ticket.raffleId] = [];
      }
      groups[ticket.raffleId].push({
        id: ticket.id,
        ticketNumber: ticket.ticketNumber,
        raffleTitle: ticket.raffleTitle,
        endTime: ticket.endTime,
        isRevealed: ticket.isRevealed,
        instantWin: ticket.instantWin
      });
    });
    
    return groups;
  }, [tickets, displayCount]);

  const handleReveal = async (ticketId: string) => {
    try {
      await revealTickets([ticketId]);
    } catch (err) {
      console.error('Failed to reveal ticket:', err);
    }
  };

  const handleLoadMore = () => {
    setDisplayCount(prev => prev + TICKETS_PER_PAGE);
  };

  if (error) {
    return (
      <div className="flex items-center justify-center p-8 text-red-500">
        Error loading tickets: {error}
      </div>
    );
  }

  if (isLoading && !tickets.length) {
    return (
      <div className="flex flex-col items-center justify-center p-8 space-y-4">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
        <p className="text-gray-500">Loading your tickets...</p>
      </div>
    );
  }

  if (!tickets.length) {
    return (
      <div className="flex flex-col items-center justify-center p-8 space-y-4">
        <div className="text-lg font-medium text-gray-600">No tickets yet</div>
        <p className="text-gray-500">Purchase tickets from active raffles to see them here</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {Object.entries(groupedTickets).map(([raffleId, raffleTickets]) => (
        <RaffleTicketGroup
          key={raffleId}
          raffleTitle={raffleTickets[0].raffleTitle}
          tickets={raffleTickets}
          onReveal={handleReveal}
        />
      ))}
      
      {displayCount < tickets.length && (
        <div className="flex justify-center pt-4">
          <Button
            onClick={handleLoadMore}
            variant="outline"
            className="min-w-[200px]"
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Loading...
              </>
            ) : (
              `Load More (${tickets.length - displayCount} remaining)`
            )}
          </Button>
        </div>
      )}
    </div>
  );
};