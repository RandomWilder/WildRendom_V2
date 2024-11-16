import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import {
  Plus,
  Lock,
  LockOpen // Changed from Unlock to LockOpen
} from 'lucide-react';
import PrizeTemplatesList from './PrizeTemplatesList';

const PrizeManagement = () => {
  const [activeTab, setActiveTab] = useState('prizes');

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Prize Management</h1>
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
                <div>Name</div>
                <div>Prizes</div>
                <div>Total Value</div>
                <div>Status</div>
                <div>Date Range</div>
                <div>Actions</div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="divide-y">
                {/* Sample pool row */}
                <div className="grid grid-cols-6 gap-4 py-4 items-center">
                  <div>Summer Pool 2024</div>
                  <div>10</div>
                  <div>$1,000.00</div>
                  <div>
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      Unlocked
                    </span>
                  </div>
                  <div>Jun 1 - Aug 31</div>
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline">
                      <LockOpen className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default PrizeManagement;