import { useState, useEffect } from 'react';
import raffleEndpoints, { Raffle, RaffleStats } from '../api/endpoints/raffles';

interface UseRaffleReturn {
  raffle: Raffle | null;
  stats: RaffleStats | null;
  isLoading: boolean;
  error: string | null;
  refreshRaffle: () => Promise<void>;
}

export const useRaffle = (raffleId: number): UseRaffleReturn => {
  const [raffle, setRaffle] = useState<Raffle | null>(null);
  const [stats, setStats] = useState<RaffleStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchRaffleData = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const [raffleData, statsData] = await Promise.all([
        raffleEndpoints.getRaffle(raffleId),
        raffleEndpoints.getRaffleStats(raffleId)
      ]);

      setRaffle(raffleData);
      setStats(statsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load raffle');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchRaffleData();

    // Subscribe to raffle updates
    const unsubscribe = raffleEndpoints.subscribeToRaffle(raffleId, (updatedRaffle) => {
      if (updatedRaffle) {
        setRaffle(updatedRaffle);
        // Fetch fresh stats when raffle updates
        raffleEndpoints.getRaffleStats(raffleId)
          .then(setStats)
          .catch(console.error);
      }
    });

    // Set up periodic stats refresh (every 30 seconds)
    const statsInterval = setInterval(() => {
      raffleEndpoints.getRaffleStats(raffleId)
        .then(setStats)
        .catch(console.error);
    }, 30000);

    return () => {
      unsubscribe();
      clearInterval(statsInterval);
    };
  }, [raffleId]);

  return {
    raffle,
    stats,
    isLoading,
    error,
    refreshRaffle: fetchRaffleData
  };
};