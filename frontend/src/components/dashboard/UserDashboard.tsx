// src/components/dashboard/UserDashboard.tsx

import React, { useState, useEffect } from 'react';
import { useAuth } from '../../lib/auth/auth-context';
import raffleEndpoints, { Raffle } from '../../api/endpoints/raffles';
import TicketPurchaseModal from '../modals/TicketPurchaseModal';
import { 
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent
} from '@/components/ui/card';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger
} from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { 
  AlertCircle,
  Ticket,
  Trophy,
  Clock,
  Loader2
} from 'lucide-react';

const UserDashboard: React.FC = () => {
  const { user } = useAuth();
  const [activeRaffles, setActiveRaffles] = useState<Raffle[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedRaffle, setSelectedRaffle] = useState<Raffle | null>(null);
  const [isPurchaseModalOpen, setIsPurchaseModalOpen] = useState(false);

  useEffect(() => {
    const fetchRaffles = async () => {
      try {
        console.log('Fetching raffles...');
        const raffles = await raffleEndpoints.getActiveRaffles();
        console.log('Processed raffles:', {
          count: raffles.length,
          raffles: raffles.map(r => ({
            id: r.id,
            title: r.title,
            ticketPrice: r.ticketPrice,
            availableTickets: r.availableTickets,
            maxTicketsPerUser: r.maxTicketsPerUser,
            endTime: r.endTime
          }))
        });
        setActiveRaffles(raffles);
      } catch (err) {
        console.error('Error fetching raffles:', err);
        setError('Failed to load raffles. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchRaffles();
  }, []);

  const handlePurchaseClick = (raffle: Raffle) => {
    setSelectedRaffle(raffle);
    setIsPurchaseModalOpen(true);
  };

  const RaffleCard: React.FC<{ raffle: Raffle; onPurchase: (raffle: Raffle) => void }> = ({ 
    raffle, 
    onPurchase 
  }) => (
    <Card className="mb-4">
      <CardHeader>
        <div className="flex justify-between items-start">
          <div>
            <CardTitle>{raffle.title}</CardTitle>
            <CardDescription className="mt-2">
              <div className="flex items-center gap-2">
                <Ticket className="h-4 w-4" />
                <span>${raffle.ticketPrice} per ticket</span>
              </div>
              <div className="flex items-center gap-2 mt-1">
                <Clock className="h-4 w-4" />
                <span>Ends: {new Date(raffle.endTime).toLocaleDateString()}</span>
              </div>
            </CardDescription>
          </div>
          <Button 
            variant="outline"
            onClick={() => onPurchase(raffle)}
            className="ml-4"
            disabled={raffle.availableTickets === 0}
          >
            {raffle.availableTickets === 0 ? 'Sold Out' : 'Buy Tickets'}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="flex items-center gap-2">
            <span className="text-gray-500">Available:</span>
            <span className="font-medium">{raffle.availableTickets}/{raffle.totalTickets}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-gray-500">Max per user:</span>
            <span className="font-medium">{raffle.maxTicketsPerUser}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="container mx-auto px-4 py-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Welcome, {user?.username}</h1>
        <div className="flex items-center gap-2 bg-white px-4 py-2 rounded-lg shadow-sm">
          <Trophy className="h-5 w-5 text-yellow-500" />
          <span className="font-semibold">{user?.siteCredits} Credits</span>
        </div>
      </div>

      <Tabs defaultValue="active" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="active">Active Raffles</TabsTrigger>
          <TabsTrigger value="tickets">My Tickets</TabsTrigger>
          <TabsTrigger value="wins">My Wins</TabsTrigger>
        </TabsList>

        <TabsContent value="active">
          {loading ? (
            <div className="text-center py-8">
              <Loader2 className="h-8 w-8 animate-spin mx-auto" />
              <p className="mt-2">Loading raffles...</p>
            </div>
          ) : error ? (
            <Card>
              <CardContent className="flex items-center justify-center py-8 text-red-500">
                <AlertCircle className="h-5 w-5 mr-2" />
                <span>{error}</span>
              </CardContent>
            </Card>
          ) : activeRaffles.length > 0 ? (
            activeRaffles.map(raffle => (
              <RaffleCard 
                key={raffle.id} 
                raffle={raffle} 
                onPurchase={handlePurchaseClick}
              />
            ))
          ) : (
            <Card>
              <CardContent className="flex items-center justify-center py-8">
                <AlertCircle className="h-5 w-5 mr-2 text-gray-400" />
                <span>No active raffles at the moment</span>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="tickets">
          <Card>
            <CardContent className="py-8 text-center text-gray-500">
              Ticket history coming soon...
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="wins">
          <Card>
            <CardContent className="py-8 text-center text-gray-500">
              Wins history coming soon...
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {selectedRaffle && (
        <TicketPurchaseModal
          isOpen={isPurchaseModalOpen}
          onClose={() => {
            setIsPurchaseModalOpen(false);
            setSelectedRaffle(null);
          }}
          raffle={selectedRaffle}
        />
      )}
    </div>
  );
};

export default UserDashboard;