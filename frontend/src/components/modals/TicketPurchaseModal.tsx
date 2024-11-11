import { useState } from 'react';
import { Loader2, Ticket as TicketIcon, AlertCircle } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useTicketStore } from '@/lib/stores/ticketStore';
import type { RaffleDisplay } from '@/lib/stores/raffleStore';

interface TicketPurchaseModalProps {
  isOpen: boolean;
  onClose: () => void;
  raffle: RaffleDisplay;
}

const TicketPurchaseModal = ({
  isOpen,
  onClose,
  raffle
}: TicketPurchaseModalProps) => {
  const [quantity, setQuantity] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const { purchaseTickets, isLoading } = useTicketStore();

  const totalCost = quantity * raffle.ticket_price;
  const isValidQuantity = quantity > 0 && 
    quantity <= raffle.limits.max_tickets_per_user && 
    quantity <= raffle.tickets.available;

  const handleQuantityChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = Math.min(
      Math.max(1, parseInt(e.target.value) || 0),
      Math.min(raffle.limits.max_tickets_per_user, raffle.tickets.available)
    );
    setQuantity(value);
    setError(null);
  };

  const handlePurchase = async () => {
    if (!isValidQuantity) return;
    setError(null);

    try {
      await purchaseTickets(raffle.id, quantity);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to purchase tickets');
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Purchase Tickets</DialogTitle>
          <DialogDescription>{raffle.title}</DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <label className="text-sm font-medium">
              Quantity (Max: {Math.min(raffle.limits.max_tickets_per_user, raffle.tickets.available)})
            </label>
            <Input
              type="number"
              min={1}
              max={Math.min(raffle.limits.max_tickets_per_user, raffle.tickets.available)}
              value={quantity}
              onChange={handleQuantityChange}
              className="col-span-3"
              disabled={isLoading}
            />
          </div>

          <div className="grid gap-1">
            <div className="flex justify-between text-sm">
              <span>Price per ticket:</span>
              <span className="font-medium">{formatCurrency(raffle.ticket_price)}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span>Total cost:</span>
              <span className="font-medium">{formatCurrency(totalCost)}</span>
            </div>
          </div>

          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={isLoading}>
            Cancel
          </Button>
          <Button
            onClick={handlePurchase}
            disabled={!isValidQuantity || isLoading}
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Processing...
              </>
            ) : (
              <>
                <TicketIcon className="mr-2 h-4 w-4" />
                Purchase Tickets
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default TicketPurchaseModal;