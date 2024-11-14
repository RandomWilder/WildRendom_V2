import { useEffect, useState } from 'react';
import { useAuth } from '@/lib/auth/auth-context';
import { useRaffleStore } from '@/lib/stores/raffleStore';
import RaffleCard from './RaffleCard';
import TicketPurchaseModal from '../modals/TicketPurchaseModal';
import TicketGrid from '../tickets/TicketGrid';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Card, CardContent } from '@/components/ui/card';
import { Trophy, AlertCircle, Loader2 } from 'lucide-react';

type Raffle = {
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

const UserDashboard = () => {
  const { user } = useAuth();
  const { raffles, isLoading, error, fetchRaffles } = useRaffleStore();
  const [selectedRaffle, setSelectedRaffle] = useState<Raffle | null>(null);
  const [activeTab, setActiveTab] = useState('active');

  useEffect(() => {
    fetchRaffles();
    const refreshInterval = setInterval(() => {
      if (activeTab === 'active') {
        fetchRaffles();
      }
    }, 30000);

    return () => clearInterval(refreshInterval);
  }, [fetchRaffles, activeTab]);

  const handlePurchaseClick = (raffle: Raffle) => {
    setSelectedRaffle(raffle);
  };

  const handleModalClose = () => {
    setSelectedRaffle(null);
    fetchRaffles();
  };

  const handleTabChange = (value: string) => {
    setActiveTab(value);
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
          <CardContent className="py-8 text-center text-muted-foreground">
            No raffles available at the moment
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

  const renderTicketsTab = () => (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6">
        <TicketGrid />
      </div>
    </div>
  );

  const renderWinsTab = () => (
    <Card>
      <CardContent className="py-8 text-center text-muted-foreground">
        <p className="text-lg font-medium mb-2">Wins History Coming Soon</p>
        <p className="text-sm text-gray-500">
          Track your winning tickets and claims in one place.
        </p>
      </CardContent>
    </Card>
  );

  return (
    <div className="container mx-auto px-4 py-6">
      {/* Header Section */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">
          Welcome, {user?.username}
        </h1>
        <div className="flex items-center gap-2 bg-white px-4 py-2 rounded-lg shadow-sm">
          <Trophy className="h-5 w-5 text-yellow-500" />
          <span className="font-semibold">
            {user?.siteCredits?.toLocaleString(undefined, {
              style: 'currency',
              currency: 'USD',
              minimumFractionDigits: 0,
              maximumFractionDigits: 0,
            })} Credits
          </span>
        </div>
      </div>

      {/* Tabs Section */}
      <Tabs 
        defaultValue="active" 
        className="w-full"
        onValueChange={handleTabChange}
      >
        <TabsList className="grid w-full grid-cols-3 mb-6">
          <TabsTrigger value="active">Raffles</TabsTrigger>
          <TabsTrigger value="tickets">My Tickets</TabsTrigger>
          <TabsTrigger value="wins">My Wins</TabsTrigger>
        </TabsList>

        <TabsContent value="active" className="space-y-4">
          {renderRafflesList()}
        </TabsContent>

        <TabsContent value="tickets">
          {renderTicketsTab()}
        </TabsContent>

        <TabsContent value="wins">
          {renderWinsTab()}
        </TabsContent>
      </Tabs>

      {/* Purchase Modal */}
      {selectedRaffle && (
        <TicketPurchaseModal
          isOpen={true}
          onClose={handleModalClose}
          raffle={{
            id: selectedRaffle.id,
            title: selectedRaffle.title,
            ticketPrice: selectedRaffle.ticket_price,
            maxTicketsPerUser: selectedRaffle.limits.max_tickets_per_user,
            availableTickets: selectedRaffle.tickets.available
          }}
        />
      )}
    </div>
  );
};

export default UserDashboard;