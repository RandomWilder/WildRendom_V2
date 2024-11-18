// PrizeManagement.tsx
import { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Plus, Lock, LockOpen, Pencil } from 'lucide-react';
import PrizeTemplatesList from './PrizeTemplatesList';
import { usePrizePoolStore } from '@/admin/stores/prizePools';
import { PrizePoolForm } from './pools/PrizePoolForm'; // Ensure the file exists

const PrizeManagement = () => {
  const [activeTab, setActiveTab] = useState('prizes');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const { pools, isLoading, error, fetchPools: originalFetchPools, lockPool } = usePrizePoolStore();

  const fetchPools = useCallback(() => {
    originalFetchPools();
  }, [originalFetchPools]);

  useEffect(() => {
    if (activeTab === 'pools') {
      fetchPools();
    }
  }, [activeTab, fetchPools]);

  const handleLockPool = async (poolId: number) => {
    try {
      await lockPool(poolId);
    } catch (error) {
      console.error('Failed to lock pool:', error);
    }
  };

  const handleCreateSuccess = () => {
    setShowCreateForm(false);
    fetchPools(); // Refresh the list after successful creation
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Prize Management</h1>
        {activeTab === 'pools' && (
          <Button
            onClick={() => setShowCreateForm(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            <Plus className="w-4 h-4 mr-2" />
            Create Pool
          </Button>
        )}
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
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
                <div>ID</div>
                <div>Name</div>
                <div>Prizes</div>
                <div>Total Value</div>
                <div>Status</div>
                <div>Actions</div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="divide-y">
                {isLoading ? (
                  <div className="py-4 text-center">Loading prize pools...</div>
                ) : error ? (
                  <div className="py-4 text-center text-red-500">{error}</div>
                ) : pools.length === 0 ? (
                  <div className="py-4 text-center text-gray-500">No prize pools found</div>
                ) : (
                  pools.map((pool) => (
                    <div key={pool.id} className="grid grid-cols-6 gap-4 py-4 items-center">
                      <div className="text-gray-500">#{pool.id}</div>
                      <div>{pool.name}</div>
                      <div>{pool.total_instances} (DW: {pool.draw_win_count})</div>
                      <div>
                        <div>${pool.values.retail_total.toLocaleString()}</div>
                        <div className="text-sm text-gray-500">
                          Cash: ${pool.values.cash_total.toLocaleString()} / 
                          Credits: ${pool.values.credit_total.toLocaleString()}
                        </div>
                      </div>
                      <div>
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
                          ${pool.status === 'unlocked' ? 'bg-blue-100 text-blue-800' : ''}
                          ${pool.status === 'locked' ? 'bg-yellow-100 text-yellow-800' : ''}
                          ${pool.status === 'assigned' ? 'bg-green-100 text-green-800' : ''}`}
                        >
                          {pool.status.charAt(0).toUpperCase() + pool.status.slice(1)}
                        </span>
                      </div>
                      <div className="flex gap-2">
                        {pool.status === 'unlocked' && (
                          <>
                            <Button 
                              size="sm" 
                              variant="outline"
                              title="Allocate Prize"
                            >
                              <Plus className="w-4 h-4" />
                            </Button>
                            <Button 
                              size="sm" 
                              variant="outline"
                              title="Edit Pool"
                            >
                              <Pencil className="w-4 h-4" />
                            </Button>
                          </>
                        )}
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => pool.status === 'unlocked' && handleLockPool(pool.id)}
                          disabled={pool.status !== 'unlocked'}
                        >
                          {pool.status === 'unlocked' ? (
                            <LockOpen className="w-4 h-4" />
                          ) : (
                            <Lock className="w-4 h-4" />
                          )}
                        </Button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {showCreateForm && (
        <PrizePoolForm
          isOpen={showCreateForm}
          onClose={() => setShowCreateForm(false)}
          onSuccess={handleCreateSuccess}
        />
      )}
    </div>
  );
};

export default PrizeManagement;