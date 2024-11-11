import { ChevronDown, ChevronUp, Trophy } from 'lucide-react';
import { TicketCard } from './TicketCard';
import { cn } from '@/lib/utils';
import { useState } from 'react';

export interface RaffleTicket {
  id: string;
  ticketNumber: string;
  raffleTitle: string;
  endTime: string;
  isRevealed: boolean;
  instantWin: boolean;
}

export interface RaffleTicketGroupProps {
  raffleTitle: string;
  tickets: RaffleTicket[];
  onReveal?: (ticketId: string) => void;
  className?: string;
}

export const RaffleTicketGroup = ({
  raffleTitle,
  tickets,
  onReveal,
  className
}: RaffleTicketGroupProps) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const instantWinCount = tickets.filter(ticket => ticket.instantWin).length;

  return (
    <div className={cn('space-y-4', className)}>
      <div className="flex items-center justify-between p-2 bg-white rounded-lg shadow-sm">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center space-x-2 text-lg font-semibold text-gray-800 hover:text-gray-600 transition-colors"
          aria-expanded={isExpanded}
          aria-controls={`raffle-group-${raffleTitle.toLowerCase().replace(/\s+/g, '-')}`}
        >
          {isExpanded ? (
            <ChevronDown className="w-5 h-5" />
          ) : (
            <ChevronUp className="w-5 h-5" />
          )}
          <span>{raffleTitle}</span>
          <span className="text-sm font-normal text-gray-500">
            ({tickets.length} ticket{tickets.length !== 1 ? 's' : ''})
          </span>
        </button>
        {instantWinCount > 0 && (
          <div className="flex items-center px-3 py-1 text-sm font-medium text-yellow-800 bg-yellow-100 rounded-full">
            <Trophy className="w-4 h-4 mr-1 text-yellow-600" />
            {instantWinCount} Instant {instantWinCount === 1 ? 'Win' : 'Wins'}
          </div>
        )}
      </div>

      {isExpanded && (
        <div 
          id={`raffle-group-${raffleTitle.toLowerCase().replace(/\s+/g, '-')}`}
          className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4"
        >
          {tickets.map((ticket) => (
            <TicketCard
              key={ticket.id}
              ticketNumber={ticket.ticketNumber}
              raffleTitle={ticket.raffleTitle}
              endTime={ticket.endTime}
              isRevealed={ticket.isRevealed}
              instantWin={ticket.instantWin}
              onReveal={onReveal ? () => onReveal(ticket.id) : undefined}
            />
          ))}
        </div>
      )}
    </div>
  );
};