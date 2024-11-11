import { motion } from 'framer-motion';
import { Clock, Star, Ticket } from 'lucide-react';
import { format } from 'date-fns';
import { cn } from '@/lib/utils';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';

export interface TicketCardProps {
  ticketNumber: string;
  raffleTitle: string;
  endTime: string;
  isRevealed: boolean;
  instantWin: boolean;
  onReveal?: () => void;
  className?: string;
}

export const TicketCard = ({
  ticketNumber,
  raffleTitle,
  endTime,
  isRevealed,
  instantWin,
  onReveal,
  className
}: TicketCardProps) => {
  const formattedEndTime = format(new Date(endTime), 'MMM d, yyyy h:mm a');

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className={cn('relative', className)}
    >
      <Card className={cn(
        'h-full transition-colors border-2',
        isRevealed
          ? 'bg-gradient-to-br from-violet-100 to-indigo-100 border-indigo-200'
          : 'bg-gradient-to-br from-amber-50 to-orange-50 border-amber-200',
        instantWin && 'border-yellow-400 shadow-lg',
      )}>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg font-bold text-gray-800">
              #{ticketNumber}
            </CardTitle>
            {instantWin && (
              <Star className="w-5 h-5 text-yellow-500 animate-pulse" />
            )}
          </div>
          <CardDescription className="text-sm text-gray-600 truncate">
            {raffleTitle}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex items-center text-sm text-gray-600">
              <Clock className="w-4 h-4 mr-1" />
              <span>{formattedEndTime}</span>
            </div>
            {!isRevealed && onReveal && (
              <button
                onClick={onReveal}
                className="w-full px-4 py-2 mt-2 text-sm font-medium text-white transition-colors rounded-md bg-gradient-to-r from-indigo-500 to-purple-500 hover:from-indigo-600 hover:to-purple-600 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
              >
                <div className="flex items-center justify-center">
                  <Ticket className="w-4 h-4 mr-2" />
                  Reveal Ticket
                </div>
              </button>
            )}
          </div>
        </CardContent>
      </Card>
      {instantWin && (
        <div className="absolute -top-2 -right-2">
          <div className="px-2 py-1 text-xs font-bold text-yellow-800 bg-yellow-300 rounded-full shadow-sm">
            Instant Win!
          </div>
        </div>
      )}
    </motion.div>
  );
};