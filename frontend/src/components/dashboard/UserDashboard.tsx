// src/components/dashboard/UserDashboard.tsx

import React, { useEffect, useState } from 'react';
import { useAuth } from '../../lib/auth/auth-context';
import { useRaffleStore, type RaffleDisplay } from '../../lib/stores/raffleStore';
import RaffleCard from './RaffleCard';  // This is correct now
import TicketPurchaseModal from '../modals/TicketPurchaseModal';  // Updated path
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Card, CardContent } from '@/components/ui/card';
import { Trophy, AlertCircle, Loader2 } from 'lucide-react';

const UserDashboard: React.FC = () => {
  const { user } = useAuth();
  const {
    raffles,
    isLoading,
    error,
    fetchRaffles
  } = useRaffleStore();

  const [selectedRaffle, setSelectedRaffle] = useState<RaffleDisplay | null>(null);

  useEffect(() => {
    fetchRaffles();
    // Set up periodic refresh
    const refreshInterval = setInterval(() => {
      fetchRaffles();
    }, 30000); // Refresh every 30 seconds

    return () => clearInterval(refreshInterval);
  }, [fetchRaffles]);

  const handlePurchaseClick = (raffle: RaffleDisplay) => {
    setSelectedRaffle(raffle);
  };

  const handleModalClose = () => {
    setSelectedRaffle(null);
    // Refresh raffles to get updated counts
    fetchRaffles();
  };

  const renderRafflesList = () => {
    if (isLoading) {
      return (
        <Card>
          <CardContent className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin" />
            <span className="ml-2 text-muted-foreground">Loading raffles...</span>
          </CardContent>
        </Card>
      );
    }

    if (error) {
      return (
        <Card>
          <CardContent className="flex items-center justify-center py-8 text-destructive">
            <AlertCircle className="h-5 w-5 mr-2" />
            <span>{error}</span>
          </CardContent>
        </Card>
      );
    }

    if (!raffles.length) {
      return (
        <Card>
          <CardContent className="flex items-center justify-center py-8 text-muted-foreground">
            <AlertCircle className="h-5 w-5 mr-2" />
            <span>No raffles available at the moment</span>
          </CardContent>
        </Card>
      );
    }

    return raffles.map(raffle => (
      <RaffleCard
        key={raffle.id}
        raffle={raffle}
        onPurchase={() => handlePurchaseClick(raffle)}
      />
    ));
  };

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
          <TabsTrigger value="active">Raffles</TabsTrigger>
          <TabsTrigger value="tickets">My Tickets</TabsTrigger>
          <TabsTrigger value="wins">My Wins</TabsTrigger>
        </TabsList>

        <TabsContent value="active">
          {renderRafflesList()}
        </TabsContent>

        <TabsContent value="tickets">
          <Card>
            <CardContent className="py-8 text-center text-muted-foreground">
              Ticket history coming soon...
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="wins">
          <Card>
            <CardContent className="py-8 text-center text-muted-foreground">
              Wins history coming soon...
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {selectedRaffle && (
        <TicketPurchaseModal
          isOpen={true}
          onClose={handleModalClose}
          raffle={selectedRaffle}
        />
      )}
    </div>
  );
};

export default UserDashboard;