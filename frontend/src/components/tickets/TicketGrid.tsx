import { useEffect, useState, useCallback } from 'react';
import { Loader2 } from 'lucide-react';
import { RaffleTicketGroup } from './RaffleTicketGroup';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useTicketStore, Ticket } from '@/lib/stores/ticketStore';

const TicketGrid = () => {
  const { tickets, isLoading, error, fetchUserTickets, revealTickets } = useTicketStore();
  const [displayCount, setDisplayCount] = useState(12);
  const [revealingTickets, setRevealingTickets] = useState<Set<string>>(new Set());

  useEffect(() => {
    console.log('Fetching tickets...');
    fetchUserTickets();
  }, [fetchUserTickets]);

  // Enhanced reveal handler with loading state management
  const handleReveal = useCallback(async (ticketId: string) => {
    // Prevent duplicate reveals
    if (revealingTickets.has(ticketId)) {
      return;
    }

    try {
      setRevealingTickets(prev => new Set(prev).add(ticketId));
      await revealTickets([ticketId]);
    } catch (err) {
      console.error('Failed to reveal ticket:', err);
    } finally {
      setRevealingTickets(prev => {
        const next = new Set(prev);
        next.delete(ticketId);
        return next;
      });
    }
  }, [revealTickets]);

  // Group tickets by raffle
  const groupedTickets = tickets.slice(0, displayCount).reduce((acc, ticket) => {
    const raffleId = ticket.raffleId;
    if (!acc[raffleId]) {
      acc[raffleId] = [];
    }
    acc[raffleId].push({
      ...ticket,
      raffleTitle: ticket.raffleTitle || `Raffle #${raffleId}`,
      status: ticket.status || 'sold',
      isRevealed: Boolean(ticket.isRevealed),
      instantWin: Boolean(ticket.instantWin),
      instantWinEligible: Boolean(ticket.instantWinEligible),
      endTime: ticket.endTime || new Date().toISOString()
    });
    return acc;
  }, {} as Record<number, Ticket[]>);

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center p-8 space-y-4">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
        <p className="text-gray-500">Loading your tickets...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {Object.entries(groupedTickets).map(([raffleId, raffleTickets]) => (
        <RaffleTicketGroup
          key={raffleId}
          raffleTitle={raffleTickets[0]?.raffleTitle || `Raffle #${raffleId}`}
          tickets={raffleTickets.map(ticket => ({
            id: ticket.id,
            ticketId: ticket.ticketId,
            ticketNumber: ticket.ticketNumber,
            raffleTitle: ticket.raffleTitle,
            endTime: ticket.endTime,
            status: ticket.status,
            isRevealed: ticket.isRevealed,
            instantWin: ticket.instantWin,
            instantWinEligible: ticket.instantWinEligible,
            prizeInstance: ticket.prizeInstance,
            isRevealing: revealingTickets.has(ticket.id)
          }))}
          onReveal={handleReveal}
        />
      ))}
      
      {displayCount < tickets.length && (
        <div className="flex justify-center pt-4">
          <Button
            onClick={() => setDisplayCount(prev => prev + 12)}
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

export default TicketGrid;