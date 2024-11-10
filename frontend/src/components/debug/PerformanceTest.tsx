// src/components/debug/PerformanceTest.tsx

import React, { useEffect, useState } from 'react';
import { useUserStore } from '../../lib/stores/userStore';
import { performanceMonitor } from '../../lib/utils/performanceMonitor';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';

const PerformanceTest: React.FC = () => {
  const { credits, fetchCredits, isLoading } = useUserStore();
  const [metrics, setMetrics] = useState<any[]>([]);

  // Simulate rapid repeated calls
  const testDeduplication = async () => {
    console.log('Starting deduplication test...');
    
    // Make 5 parallel requests
    await Promise.all([
      fetchCredits(),
      fetchCredits(),
      fetchCredits(),
      fetchCredits(),
      fetchCredits()
    ]);

    // Display metrics after requests
    const currentMetrics = performanceMonitor.getMetrics();
    setMetrics(currentMetrics);
  };

  useEffect(() => {
    // Initial fetch to set baseline
    fetchCredits();
  }, []);

  return (
    <Card className="max-w-2xl mx-auto mt-8">
      <CardHeader>
        <CardTitle>Performance Test Dashboard</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 border rounded">
            <h3 className="font-medium">Current Credits</h3>
            <p>{credits}</p>
            <p className="text-sm text-gray-500">
              {isLoading ? 'Loading...' : 'Idle'}
            </p>
          </div>
          
          <div className="p-4 border rounded">
            <h3 className="font-medium">API Metrics</h3>
            <p>
              Avg Response Time:{' '}
              {performanceMonitor.getAverageMetric('api', 'fetchCredits').toFixed(2)}ms
            </p>
          </div>
        </div>

        <div className="flex gap-4">
          <Button 
            onClick={testDeduplication}
            disabled={isLoading}
          >
            Test Deduplication (5 parallel requests)
          </Button>
          
          <Button 
            variant="outline"
            onClick={() => {
              performanceMonitor.clearMetrics();
              setMetrics([]);
            }}
          >
            Clear Metrics
          </Button>
        </div>

        {metrics.length > 0 && (
          <div className="mt-4">
            <h3 className="font-medium mb-2">Recent Metrics</h3>
            <div className="max-h-60 overflow-auto">
              <pre className="text-sm bg-gray-50 p-4 rounded">
                {JSON.stringify(metrics.slice(-5), null, 2)}
              </pre>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default PerformanceTest;