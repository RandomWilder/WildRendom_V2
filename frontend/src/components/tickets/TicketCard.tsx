import { motion } from 'framer-motion';
import { Clock, Star, Ticket, Trophy, Loader2 } from 'lucide-react';
import { format, parseISO } from 'date-fns';
import { cn } from '@/lib/utils';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';

export interface TicketCardProps {
  ticketNumber: string;
  raffleTitle: string;
  endTime: string;
  status: 'available' | 'sold' | 'revealed' | 'claimed';
  isRevealed: boolean;
  instantWin: boolean;
  instantWinEligible?: boolean;
  isRevealing?: boolean;
  prizeInstance?: {
    name: string;
    retailValue: number;
    cashValue: number;
    creditValue: number;
  };
  onReveal?: () => void;
  onDiscoverPrize?: () => void;
  onClaimPrize?: (valueType: 'retail' | 'cash' | 'credit') => void;
  className?: string;
}

export const TicketCard = ({
  ticketNumber,
  raffleTitle,
  endTime,
  status,
  isRevealed,
  instantWin,
  instantWinEligible,
  isRevealing = false,
  prizeInstance,
  onReveal,
  onDiscoverPrize,
  onClaimPrize,
  className
}: TicketCardProps) => {
  const formattedEndTime = endTime ? format(parseISO(endTime), 'MMM d, yyyy h:mm a') : 'No end time';

  const renderContent = () => {
    if (isRevealing) {
      return (
        <div className="flex flex-col items-center justify-center h-full space-y-4">
          <p className="text-lg font-semibold">#{ticketNumber}</p>
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <p className="text-sm text-gray-600">Revealing ticket...</p>
        </div>
      );
    }

    if (!isRevealed) {
      return (
        <div className="flex flex-col items-center justify-center h-full space-y-4">
          <p className="text-lg font-semibold text-center">#{ticketNumber}</p>
          <Button 
            onClick={onReveal}
            className="w-full bg-blue-500 hover:bg-blue-600 text-white"
            disabled={isRevealing}
          >
            <Ticket className="w-4 h-4 mr-2" />
            Reveal Ticket
          </Button>
          <div className="flex items-center space-x-2 text-gray-400">
            <Clock className="w-4 h-4" />
            <p className="text-xs">{formattedEndTime}</p>
          </div>
        </div>
      );
    }

    if (status === 'revealed' && !instantWinEligible) {
      return (
        <div className="flex flex-col items-center justify-center h-full space-y-4">
          <p className="text-lg font-semibold">#{ticketNumber}</p>
          <Star className="w-6 h-6 text-gray-400" />
          <p className="text-sm text-center text-gray-600">
            No Instant Win, but this is a chance to win {raffleTitle}
          </p>
          <p className="text-xs text-gray-500">{formattedEndTime}</p>
        </div>
      );
    }

    if (status === 'revealed' && instantWinEligible && !prizeInstance) {
      return (
        <div className="flex flex-col items-center justify-center h-full space-y-4">
          <CardHeader className="text-center p-0">
            <CardTitle className="text-lg font-semibold">#{ticketNumber}</CardTitle>
            <CardDescription className="text-yellow-600">Instant Win Eligible!</CardDescription>
          </CardHeader>
          <Trophy className="w-8 h-8 text-yellow-500 animate-bounce" />
          <p className="text-lg font-semibold text-center">
            You are an instant winner!
          </p>
          <Button 
            onClick={onDiscoverPrize}
            className="w-full bg-yellow-500 hover:bg-yellow-600 text-white"
            disabled={isRevealing}
          >
            Discover Your Prize
          </Button>
          <p className="text-xs text-gray-500">{formattedEndTime}</p>
        </div>
      );
    }

    if (prizeInstance && status !== 'claimed') {
      return (
        <div className="flex flex-col items-center justify-center h-full space-y-4">
          <CardHeader className="text-center p-0">
            <CardTitle className="text-lg">{prizeInstance.name}</CardTitle>
            <CardDescription>Select Your Prize Value</CardDescription>
          </CardHeader>
          <div className="space-y-2 w-full">
            <Button
              onClick={() => onClaimPrize?.('retail')}
              className="w-full bg-green-500 hover:bg-green-600 text-white"
              disabled={isRevealing}
            >
              Claim Retail Value (${prizeInstance.retailValue})
            </Button>
            <Button
              onClick={() => onClaimPrize?.('cash')}
              className="w-full bg-blue-500 hover:bg-blue-600 text-white"
              disabled={isRevealing}
            >
              Claim Cash Value (${prizeInstance.cashValue})
            </Button>
            <Button
              onClick={() => onClaimPrize?.('credit')}
              className="w-full bg-purple-500 hover:bg-purple-600 text-white"
              disabled={isRevealing}
            >
              Claim Site Credit (${prizeInstance.creditValue})
            </Button>
          </div>
          <p className="text-xs text-gray-500">
            Ticket #{ticketNumber} | {formattedEndTime}
          </p>
        </div>
      );
    }

    if (status === 'claimed') {
      return (
        <div className="flex flex-col items-center justify-center h-full space-y-4">
          <div className="relative w-full text-center">
            <CardHeader className="p-0">
              <CardTitle className="text-lg">{prizeInstance?.name}</CardTitle>
            </CardHeader>
            <div className="absolute -rotate-12 top-0 right-0">
              <span className="px-2 py-1 text-sm font-bold text-green-600 border-2 border-green-600 rounded">
                CLAIMED
              </span>
            </div>
          </div>
          <Trophy className="w-6 h-6 text-yellow-500" />
          <p className="text-sm text-center text-gray-600">
            You still have a chance at {raffleTitle} with this ticket
          </p>
          <p className="text-xs text-gray-500">
            Ticket #{ticketNumber} | {formattedEndTime}
          </p>
        </div>
      );
    }

    return null;
  };

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className={cn('relative', className)}
    >
      <Card className={cn(
        'h-full transition-all transform',
        !isRevealed && instantWin && 'bg-gradient-to-br from-amber-50 to-orange-50 border-amber-200',
        !isRevealed && !instantWin && 'bg-gradient-to-br from-gray-50 to-slate-50 border-gray-200',
        isRevealed && !instantWinEligible && 'bg-gradient-to-br from-gray-50 to-blue-50 border-blue-200',
        isRevealed && instantWinEligible && 'bg-gradient-to-br from-yellow-50 to-amber-50 border-yellow-200',
        status === 'claimed' && 'bg-gradient-to-br from-green-50 to-emerald-50 border-green-200',
        isRevealing && 'opacity-75'
      )}>
        <CardContent className="p-6">
          {renderContent()}
        </CardContent>
      </Card>
    </motion.div>
  );
};