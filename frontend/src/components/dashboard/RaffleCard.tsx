import React from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Ticket, Clock, Gift, CircleDot } from 'lucide-react';

interface RaffleCardProps {
  raffle: {
    id: number;
    title: string;
    description: string;
    status: 'active' | 'coming_soon' | 'ended';
    ticket_price: number;
    start_time: string;
    end_time: string;
    tickets: {
      available: number;
      total: number;
      instant_win_eligible: number;
      instant_wins_discovered: number;
    };
    limits: {
      max_tickets_per_user: number;
    };
  };
  onPurchase: (raffleId: number) => void;
}

export const RaffleCard: React.FC<RaffleCardProps> = ({ raffle, onPurchase }) => {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString(undefined, {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const getStatusDetails = () => {
    switch (raffle.status) {
      case 'coming_soon':
        return {
          label: 'Coming Soon',
          timeLabel: 'Starts',
          timeValue: formatDate(raffle.start_time),
          buttonDisabled: true,
          buttonText: 'Coming Soon',
          statusColor: 'text-blue-600'
        };
      case 'active':
        return {
          label: 'Active',
          timeLabel: 'Ends',
          timeValue: formatDate(raffle.end_time),
          buttonDisabled: raffle.tickets.available === 0,
          buttonText: raffle.tickets.available === 0 ? 'Sold Out' : 'Buy Tickets',
          statusColor: 'text-green-600'
        };
      case 'ended':
        return {
          label: 'Ended',
          timeLabel: 'Ended',
          timeValue: formatDate(raffle.end_time),
          buttonDisabled: true,
          buttonText: 'Ended',
          statusColor: 'text-gray-600'
        };
      default:
        return {
          label: '',
          timeLabel: '',
          timeValue: '',
          buttonDisabled: true,
          buttonText: '',
          statusColor: ''
        };
    }
  };

  const statusDetails = getStatusDetails();

  return (
    <Card className="mb-4">
      <CardHeader>
        <div className="flex justify-between items-start">
          <div className="space-y-2 flex-1">
            <div className="flex items-center gap-2">
              <CardTitle>{raffle.title}</CardTitle>
              <span className={`text-sm font-medium ${statusDetails.statusColor}`}>
                <CircleDot className="h-4 w-4 inline mr-1" />
                {statusDetails.label}
              </span>
            </div>
            <CardDescription className="text-sm text-gray-600">
              {raffle.description}
            </CardDescription>
            <div className="flex flex-col gap-1 text-sm">
              <div className="flex items-center gap-2">
                <Ticket className="h-4 w-4" />
                <span>{formatCurrency(raffle.ticket_price)} per ticket</span>
              </div>
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4" />
                <span>{statusDetails.timeLabel}: {statusDetails.timeValue}</span>
              </div>
            </div>
          </div>
          <Button 
            variant="outline"
            onClick={() => onPurchase(raffle.id)}
            disabled={statusDetails.buttonDisabled}
            className="ml-4"
          >
            {statusDetails.buttonText}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="flex items-center gap-2">
            <span className="text-gray-500">Available:</span>
            <span className="font-medium">
              {raffle.tickets.available.toLocaleString()}/{raffle.tickets.total.toLocaleString()}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-gray-500">Max per user:</span>
            <span className="font-medium">{raffle.limits.max_tickets_per_user}</span>
          </div>
          {raffle.tickets.instant_win_eligible > 0 && (
            <div className="col-span-2 flex items-center gap-2">
              <Gift className="h-4 w-4 text-yellow-500" />
              <span className="text-yellow-600">
                Instant Wins Found: {raffle.tickets.instant_wins_discovered}/{raffle.tickets.instant_win_eligible}
              </span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default RaffleCard;