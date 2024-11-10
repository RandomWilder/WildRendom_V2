// src/components/dashboard/RaffleCard.tsx

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Ticket, Clock } from 'lucide-react';

interface RaffleCardProps {
    raffle: {
      id: number;
      title: string;
      ticketPrice: number;
      availableTickets: number | null | undefined;
      totalTickets: number;
      endTime: string;
      maxTicketsPerUser: number;
    };
    onPurchase: (raffleId: number) => void;
  }

const formatAvailability = (available: number | undefined | null, total: number): string => {
    const availableNum = typeof available === 'number' ? available : 0;
    const totalNum = typeof total === 'number' ? total : 0;
    return `${availableNum}/${totalNum}`;
  };

const RaffleCard: React.FC<RaffleCardProps> = ({ raffle, onPurchase }) => {
  const availabilityDisplay = formatAvailability(raffle.availableTickets, raffle.totalTickets);

  return (
    <Card className="mb-4">
      <CardHeader>
        <div className="flex justify-between items-start">
          <div>
            <CardTitle>{raffle.title}</CardTitle>
            <div className="mt-2">
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <Ticket className="h-4 w-4" />
                <span>${raffle.ticketPrice} per ticket</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-600 mt-1">
                <Clock className="h-4 w-4" />
                <span>Ends: {new Date(raffle.endTime).toLocaleDateString()}</span>
              </div>
            </div>
          </div>
          <Button
            variant="outline"
            onClick={() => onPurchase(raffle.id)}
            className="ml-4"
            disabled={!raffle.availableTickets || raffle.availableTickets <= 0}
          >
            {!raffle.availableTickets || raffle.availableTickets <= 0 ? 'Sold Out' : 'Buy Tickets'}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="flex items-center gap-2">
            <span className="text-gray-500">Available:</span>
            <span className="font-medium">{availabilityDisplay}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-gray-500">Max per user:</span>
            <span className="font-medium">{raffle.maxTicketsPerUser}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default RaffleCard;