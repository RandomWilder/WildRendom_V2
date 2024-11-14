import { useState } from 'react';
import { Loader2, AlertCircle, Check } from 'lucide-react';
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
import { formatCurrency } from '@/lib/utils/format';
import { getAuthHeader } from '@/lib/auth/auth-utils';

type PurchaseStep = 'quantity' | 'reservation' | 'processing' | 'confirmation' | 'success' | 'error';

interface PurchaseFlowProps {
  isOpen: boolean;
  onClose: () => void;
  raffle: {
    id: number;
    title: string;
    ticketPrice: number;
    maxTicketsPerUser: number;
    availableTickets: number;
  };
}

export default function TicketPurchaseModal({ isOpen, onClose, raffle }: PurchaseFlowProps) {
  const [currentStep, setCurrentStep] = useState<PurchaseStep>('quantity');
  const [quantity, setQuantity] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const [paymentIntent, setPaymentIntent] = useState<any>(null);
  const [purchasedTickets, setPurchasedTickets] = useState<any[]>([]);

  const totalCost = quantity * raffle.ticketPrice;
  const isValidQuantity = quantity > 0 && 
    quantity <= raffle.maxTicketsPerUser && 
    quantity <= raffle.availableTickets;

  const handleQuantityChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = Math.min(
      Math.max(1, parseInt(e.target.value) || 0),
      Math.min(raffle.maxTicketsPerUser, raffle.availableTickets)
    );
    setQuantity(value);
    setError(null);
  };

  const getAuthToken = () => {
    const token = localStorage.getItem('auth_token');
    if (!token) return null;
    try {
      // Remove quotes if they exist
      return token.replace(/^["'](.+(?=["']$))["']$/, '$1');
    } catch (e) {
      return null;
    }
  };

  const createReservation = async () => {
    const token = getAuthToken();
    if (!token) {
      setError('Authentication token not found. Please log in again.');
      setCurrentStep('error');
      return;
    }

    try {
      setCurrentStep('reservation');
      const response = await fetch('/api/reservations/tickets', {
        method: 'POST',
        headers: getAuthHeader(), // This will include the Authorization header with the token
        body: JSON.stringify({
          raffle_id: raffle.id,
          quantity,
        }),
      });

      const data = await response.json();
      
      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Session expired. Please log in again.');
        }
        throw new Error(data.error || 'Failed to create reservation');
      }

      await createPaymentIntent(data.reservation.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create reservation');
      setCurrentStep('error');
    }
  };

  const createPaymentIntent = async (reservationId: string) => {
    const token = getAuthToken();
    if (!token) {
      setError('Authentication token not found. Please log in again.');
      setCurrentStep('error');
      return;
    }

    try {
      setCurrentStep('processing');
      const response = await fetch('/api/payments/intents', {
        method: 'POST',
        headers: getAuthHeader(),  // This includes both Content-Type and Authorization
        body: JSON.stringify({ reservation_id: reservationId }),
      });

      const data = await response.json();

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Session expired. Please log in again.');
        }
        throw new Error(data.error || 'Failed to process payment');
      }

      setPaymentIntent(data.payment_intent);
      setCurrentStep('confirmation');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Payment processing failed');
      setCurrentStep('error');
    }
  };

  const confirmPurchase = async () => {
    const token = getAuthToken();
    if (!token) {
      setError('Authentication token not found. Please log in again.');
      setCurrentStep('error');
      return;
    }

    try {
      setCurrentStep('processing');
      const response = await fetch(`/api/payments/intents/${paymentIntent.id}/confirm`, {
        method: 'POST',
        headers: getAuthHeader(),  // This includes both Content-Type and Authorization
      });

      const data = await response.json();
      
      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Session expired. Please log in again.');
        }
        throw new Error(data.error || 'Failed to confirm purchase');
      }

      setPurchasedTickets(data.tickets);
      setCurrentStep('success');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Purchase confirmation failed');
      setCurrentStep('error');
    }
  };

  const renderStep = () => {
    switch (currentStep) {
      case 'quantity':
        return (
          <>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <label htmlFor="quantity" className="text-sm font-semibold text-gray-700">
                  Quantity (Max: {Math.min(raffle.maxTicketsPerUser, raffle.availableTickets)})
                </label>
                <Input
                  id="quantity"
                  type="number"
                  min={1}
                  max={Math.min(raffle.maxTicketsPerUser, raffle.availableTickets)}
                  value={quantity}
                  onChange={handleQuantityChange}
                  className="border-2 border-gray-300 focus:border-blue-500"
                />
              </div>

              <div className="grid gap-1 bg-gray-100 p-4 rounded-lg">
                <div className="flex justify-between text-sm text-gray-600">
                  <span>Price per ticket:</span>
                  <span className="font-medium text-gray-900">{formatCurrency(raffle.ticketPrice)}</span>
                </div>
                <div className="flex justify-between text-sm font-bold text-gray-900 pt-2 border-t border-gray-200">
                  <span>Total cost:</span>
                  <span>{formatCurrency(totalCost)}</span>
                </div>
              </div>
            </div>

            <DialogFooter className="bg-gray-50 px-6 py-4 mt-4">
              <Button variant="outline" onClick={onClose} className="border-2 hover:bg-gray-100">
                Cancel
              </Button>
              <Button 
                onClick={createReservation}
                disabled={!isValidQuantity}
                className="bg-blue-600 hover:bg-blue-700 text-white"
              >
                Continue to Purchase
              </Button>
            </DialogFooter>
          </>
        );

      case 'reservation':
      case 'processing':
        return (
          <div className="py-12 text-center">
            <Loader2 className="mx-auto h-8 w-8 animate-spin text-blue-600" />
            <p className="mt-4 text-gray-600">Processing your purchase...</p>
          </div>
        );

      case 'confirmation':
        return (
          <>
            <div className="py-4">
              <Alert className="bg-blue-50 border-blue-200 text-blue-800">
                <AlertDescription>
                  Please confirm your purchase of {quantity} tickets for {formatCurrency(totalCost)}.
                </AlertDescription>
              </Alert>

              <div className="mt-6 space-y-3 bg-gray-100 p-4 rounded-lg">
                <div className="flex justify-between text-gray-700">
                  <span>Tickets:</span>
                  <span className="font-medium">{quantity}</span>
                </div>
                <div className="flex justify-between text-gray-900 font-semibold pt-2 border-t border-gray-200">
                  <span>Total Cost:</span>
                  <span>{formatCurrency(totalCost)}</span>
                </div>
              </div>
            </div>

            <DialogFooter className="bg-gray-50 px-6 py-4 mt-4">
              <Button variant="outline" onClick={onClose} className="border-2 hover:bg-gray-100">
                Cancel
              </Button>
              <Button 
                onClick={confirmPurchase}
                className="bg-green-600 hover:bg-green-700 text-white"
              >
                Confirm Purchase
              </Button>
            </DialogFooter>
          </>
        );

      case 'success':
        return (
          <div className="py-8 text-center">
            <div className="mx-auto h-12 w-12 rounded-full bg-green-100 flex items-center justify-center">
              <Check className="h-6 w-6 text-green-600" />
            </div>
            <h3 className="mt-4 text-lg font-medium text-gray-900">Purchase Successful!</h3>
            <p className="mt-2 text-sm text-gray-600">
              You have successfully purchased {quantity} tickets.
            </p>
            <div className="mt-6 bg-gray-100 p-4 rounded-lg">
              <p className="font-medium text-gray-900">Your ticket numbers:</p>
              <div className="mt-3 space-y-1">
                {purchasedTickets.map(ticket => (
                  <div key={ticket.ticket_id} className="text-gray-700">
                    #{ticket.ticket_number}
                  </div>
                ))}
              </div>
            </div>
            <Button 
              className="mt-6 bg-blue-600 hover:bg-blue-700 text-white" 
              onClick={onClose}
            >
              View My Tickets
            </Button>
          </div>
        );

      case 'error':
        return (
          <div className="py-8 text-center">
            <div className="mx-auto h-12 w-12 rounded-full bg-red-100 flex items-center justify-center">
              <AlertCircle className="h-6 w-6 text-red-600" />
            </div>
            <h3 className="mt-4 text-lg font-medium text-gray-900">Purchase Failed</h3>
            <div className="mt-2 mx-auto max-w-[300px]">
              <Alert variant="destructive" className="bg-red-50 border-red-200">
                <AlertDescription className="text-red-800">{error}</AlertDescription>
              </Alert>
            </div>
            <Button 
              className="mt-6 border-2 border-gray-300 hover:bg-gray-100" 
              variant="outline" 
              onClick={() => setCurrentStep('quantity')}
            >
              Try Again
            </Button>
          </div>
        );
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px] bg-white">
        <DialogHeader className="bg-gray-50 px-6 py-4 rounded-t-lg">
          <DialogTitle className="text-xl text-gray-900">Purchase Tickets</DialogTitle>
          <DialogDescription className="text-gray-600">{raffle.title}</DialogDescription>
        </DialogHeader>

        <div className="px-6">{renderStep()}</div>
      </DialogContent>
    </Dialog>
  );
}