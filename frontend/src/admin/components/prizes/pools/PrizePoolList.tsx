import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Lock, LockOpen, Plus } from 'lucide-react';
import { PrizePool } from '@/types/prizes';
import { usePrizePoolStore } from '@/admin/stores/prizePools';
import { usePrizeTemplateStore } from '@/admin/stores/prizetemplates';
import PrizeTemplatesList from '../PrizeTemplatesList';
import { PrizeAllocationModal } from './PrizeAllocationModal';

const PrizeManagement = () => {
  const [activeTab, setActiveTab] = useState('prizes');
  const { pools, isLoading, error, fetchPools } = usePrizePoolStore();
  const { templates: prizeTemplates, fetchTemplates } = usePrizeTemplateStore();
  const [selectedPool, setSelectedPool] = useState<PrizePool | null>(null);
  const [showAllocationModal, setShowAllocationModal] = useState(false);

  // Fetch pools when tab changes to 'pools'
  const handleTabChange = (value: string) => {
    setActiveTab(value);
    if (value === 'pools') {
      fetchPools();
    }
  };

  // Fetch prize templates on mount
  useEffect(() => {
    fetchTemplates();
  }, [fetchTemplates]);

  const handleAllocate = (pool: PrizePool) => {
    setSelectedPool(pool);
    setShowAllocationModal(true);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Prize Management</h1>
      </div>

      <Tabs value={activeTab} onValueChange={handleTabChange}>
        <TabsList>
          <TabsTrigger value="prizes">Prize Templates</TabsTrigger>
          <TabsTrigger value="pools">Prize Pools</TabsTrigger>
        </TabsList>

        <TabsContent value="prizes" className="mt-4">
          <PrizeTemplatesList />
        </TabsContent>

        <TabsContent value="pools" className="mt-4 space-y-4">
          <Card>
            <CardHeader className="bg-gray-50">
              <div className="grid grid-cols-6 gap-4 font-semibold text-sm">
                <div>Name</div>
                <div>Prizes</div>
                <div>Total Value</div>
                <div>Status</div>
                <div>Date Range</div>
                <div>Actions</div>
              </div>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="flex justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
                </div>
              ) : error ? (
                <div className="text-center text-red-500 py-8">{error}</div>
              ) : (
                <div className="divide-y">
                  {pools.map((pool) => (
                    <div key={pool.id} className="grid grid-cols-6 gap-4 py-4 items-center">
                      <div>{pool.name}</div>
                      <div>{pool.total_instances}</div>
                      <div>${pool.values.retail_total.toLocaleString()}</div>
                      <div>
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
                          ${pool.status === 'unlocked' ? 'bg-blue-100 text-blue-800' : ''}
                          ${pool.status === 'locked' ? 'bg-yellow-100 text-yellow-800' : ''}
                          ${pool.status === 'assigned' ? 'bg-green-100 text-green-800' : ''}`}
                        >
                          {pool.status.charAt(0).toUpperCase() + pool.status.slice(1)}
                        </span>
                      </div>
                      <div>{pool.dateRange}</div>
                      <div className="flex gap-2">
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => handleAllocate(pool)}
                          disabled={pool.status !== 'unlocked'}
                        >
                          <Plus className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {selectedPool && (
        <PrizeAllocationModal
          isOpen={showAllocationModal}
          onClose={() => {
            setShowAllocationModal(false);
            setSelectedPool(null);
          }}
          pool={selectedPool}
          prizeTemplates={prizeTemplates}
          currentTotalOdds={selectedPool.total_odds || 0}
          onSuccess={() => {
            fetchPools();
            setShowAllocationModal(false);
            setSelectedPool(null);
          }}
        />
      )}
    </div>
  );
};

export default PrizeManagement;