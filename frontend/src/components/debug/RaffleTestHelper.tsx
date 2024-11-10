// src/components/debug/RaffleTestHelper.tsx

import React from 'react';
import { useRaffleStore } from '../../lib/stores/raffleStore';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';

const RaffleTestHelper: React.FC = () => {
  const { raffles, isLoading, fetchRaffles } = useRaffleStore();

  const runParallelTest = async () => {
    console.log('Starting parallel raffle requests test...');
    
    // Make three parallel requests
    await Promise.all([
      fetchRaffles(),
      fetchRaffles(),
      fetchRaffles()
    ]);

    console.log('All raffle requests completed');
  };

  return (
    <Card className="mb-6 border-2 border-green-200">
      <CardHeader className="bg-green-50">
        <CardTitle className="text-lg text-green-800">Raffle Fetch Test</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-4">
          <Button 
            onClick={runParallelTest}
            disabled={isLoading}
          >
            Test Parallel Raffle Requests
          </Button>
          <div>Active Raffles: {raffles.length}</div>
          {isLoading && <div>Loading...</div>}
        </div>
      </CardContent>
    </Card>
  );
};

export default RaffleTestHelper;