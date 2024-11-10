// src/components/modals/TicketPurchaseModal.tsx

import React, { useState, useEffect } from 'react';
import { useAuth } from '../../lib/auth/auth-context';
import { Raffle } from '../../types/raffle';
import { useTicketStore } from '../../lib/stores/ticketStore';
import { useUserStore } from '../../lib/stores/userStore';
import { useRaffleStore } from '../../lib/stores/raffleStore';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
} from '@/components/ui/card';
import {
  Alert,
  AlertDescription,
  AlertTitle,
} from '@/components/ui/alert';
import { Input } from '@/components/ui/input';
import { Ticket, AlertCircle, CreditCard, Loader2 } from 'lucide-react';

interface TicketPurchaseModalProps {
  isOpen: boolean;
  onClose: () => void;
  raffle: Raffle;
}

const TicketPurchaseModal: React.FC<TicketPurchaseModalProps> = ({
  isOpen,
  onClose,
  raffle
}) => {
  // State Management
  const { user } = useAuth();
  const purchaseTickets = useTicketStore(state => state.purchaseTickets);
  const isLoading = useTicketStore(state => state.isLoading);
  const error = useTicketStore(state => state.error);
  const credits = useUserStore(state => state.credits);
  const fetchCredits = useUserStore(state => state.fetchCredits);
  const getAvailableTickets = useRaffleStore(state => state.getAvailableTickets);

  // Local State
  const [quantity, setQuantity] = useState(1);
  const [availableTickets, setAvailableTickets] = useState(raffle.availableTickets);
  const [isPurchasing, setIsPurchasing] = useState(false);
  const [purchaseError, setPurchaseError] = useState<string | null>(null);

  const totalCost = quantity * raffle.ticketPrice;
  const canAfford = credits >= totalCost;
  const isValidQuantity = quantity > 0 && 
    quantity <= raffle.maxTicketsPerUser && 
    quantity <= availableTickets;

  useEffect(() => {
    fetchCredits();
    updateAvailableTickets();
  }, []);

  const updateAvailableTickets = async () => {
    const available = await getAvailableTickets(raffle.id);
    setAvailableTickets(available);
  };

  const handleQuantityChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value) || 0;
    setQuantity(Math.min(
      value, 
      raffle.maxTicketsPerUser, 
      availableTickets
    ));
  };

  const handlePurchase = async () => {
    if (!isValidQuantity || !canAfford) return;
    
    setIsPurchasing(true);
    setPurchaseError(null);

    try {
      await purchaseTickets(raffle.id, quantity);
      await fetchCredits(); // Refresh user credits
      await updateAvailableTickets(); // Refresh available tickets
      onClose();
    } catch (err) {
      setPurchaseError('Failed to process purchase. Please try again.');
    } finally {
      setIsPurchasing(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Purchase Tickets</DialogTitle>
          <DialogDescription>
            {raffle.title}
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex justify-between items-center mb-4">
                <div className="flex items-center gap-2">
                  <Ticket className="h-4 w-4" />
                  <span>Price per ticket:</span>
                </div>
                <span className="font-semibold">${raffle.ticketPrice}</span>
              </div>
              
              <div className="flex justify-between items-center mb-4">
                <span>Quantity:</span>
                <Input
                  type="number"
                  min={1}
                  max={Math.min(raffle.maxTicketsPerUser, availableTickets)}
                  value={quantity}
                  onChange={handleQuantityChange}
                  className="w-24 text-right"
                  disabled={isPurchasing}
                />
              </div>

              <div className="flex justify-between items-center font-semibold">
                <span>Total cost:</span>
                <span>${totalCost}</span>
              </div>

              {availableTickets < raffle.maxTicketsPerUser && (
                <div className="mt-2 text-sm text-yellow-600">
                  Only {availableTickets} tickets remaining
                </div>
              )}
            </CardContent>
          </Card>

          <div className="flex items-center gap-2">
            <CreditCard className="h-4 w-4" />
            <span>Your balance:</span>
            <span className={`font-semibold ${canAfford ? 'text-green-600' : 'text-red-600'}`}>
              ${credits}
            </span>
          </div>

          {(error || purchaseError) && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>{error || purchaseError}</AlertDescription>
            </Alert>
          )}
        </div>

        <DialogFooter>
          <Button 
            variant="outline" 
            onClick={onClose}
            disabled={isPurchasing}
          >
            Cancel
          </Button>
          <Button 
            onClick={handlePurchase}
            disabled={!isValidQuantity || !canAfford || isPurchasing}
          >
            {isPurchasing ? (
              <span className="flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                Processing...
              </span>
            ) : (
              'Purchase Tickets'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default TicketPurchaseModal;