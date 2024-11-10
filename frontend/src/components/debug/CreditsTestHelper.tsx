// src/components/debug/CreditsTestHelper.tsx

import React from 'react';
import { useUserStore } from '../../lib/stores/userStore';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';

const CreditsTestHelper: React.FC = () => {
  const { credits, fetchCredits, isLoading } = useUserStore();

  const runParallelTest = async () => {
    console.log('Starting parallel requests test...');
    
    // Make three parallel requests
    await Promise.all([
      fetchCredits(),
      fetchCredits(),
      fetchCredits()
    ]);

    console.log('All parallel requests completed');
  };

  return (
    <Card className="mb-6 border-2 border-blue-200">
      <CardHeader className="bg-blue-50">
        <CardTitle className="text-lg text-blue-800">Credits Fetch Test</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-4">
          <Button 
            onClick={runParallelTest}
            disabled={isLoading}
          >
            Test Parallel Requests
          </Button>
          <div>Current Credits: {credits}</div>
          {isLoading && <div>Loading...</div>}
        </div>
      </CardContent>
    </Card>
  );
};

export default CreditsTestHelper;