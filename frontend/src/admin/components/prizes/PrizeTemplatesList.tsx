import { useState, useEffect } from 'react';
import { SortableDataTable } from '../ui/SortableDataTable';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Plus, Filter, Search } from 'lucide-react';
import { useToast } from '../../hooks/useToast';
import { Badge } from '../ui/badge';
import { apiClient } from '../../../api/client';
import { PrizeTemplateForm } from './PrizeTemplateForm';

// Type definitions
interface PrizeTemplate {
  id: number;
  name: string;
  type: 'Instant_Win' | 'Draw_Win';
  tier: 'platinum' | 'gold' | 'silver' | 'bronze';
  retail_value: number;
  cash_value: number;
  credit_value: number;
  status: string;
  expiry_days: number;
  claim_deadline_hours?: number;
  auto_claim_credit: boolean;
  created_at: string;
}

// Define tier styles
const tierStyles = {
  platinum: 'bg-slate-300 text-slate-900 border-slate-400',
  gold: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  silver: 'bg-gray-100 text-gray-800 border-gray-300',
  bronze: 'bg-orange-100 text-orange-800 border-orange-300',
} as const;

// Define status styles
const statusStyles = {
  active: 'bg-green-100 text-green-800',
  inactive: 'bg-gray-100 text-gray-800',
  depleted: 'bg-red-100 text-red-800',
  expired: 'bg-yellow-100 text-yellow-800',
} as const;

// Custom currency formatter
const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD'
  }).format(amount);
};

const PrizeTemplatesList = () => {
  const [templates, setTemplates] = useState<PrizeTemplate[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const { toast } = useToast();

  const fetchTemplates = async () => {
    try {
      setIsLoading(true);
      const response = await apiClient.get<PrizeTemplate[]>('/api/admin/prizes/');
      setTemplates(response.data);
    } catch (error: any) {
      toast({
        title: "Error loading prize templates",
        description: error.response?.data?.error || "An error occurred",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTemplates();
  }, []);

  const handleCreateSuccess = () => {
    fetchTemplates();
  };

  const columns = [
    { 
      key: 'id', 
      title: 'ID',
      sortable: true,
      render: (template: PrizeTemplate) => (
        <span className="font-mono text-sm">{template.id}</span>
      )
    },
    { 
      key: 'name', 
      title: 'Name',
      sortable: true
    },
    { 
      key: 'type', 
      title: 'Type',
      sortable: true,
      render: (template: PrizeTemplate) => (
        <Badge variant="outline">
          {template.type.replace('_', ' ')}
        </Badge>
      )
    },
    { 
      key: 'tier', 
      title: 'Tier',
      sortable: true,
      render: (template: PrizeTemplate) => (
        <Badge className={tierStyles[template.tier]}>
          {template.tier.charAt(0).toUpperCase() + template.tier.slice(1)}
        </Badge>
      )
    },
    { 
      key: 'retail_value', 
      title: 'Retail Value',
      sortable: true,
      render: (template: PrizeTemplate) => formatCurrency(template.retail_value)
    },
    { 
      key: 'cash_value', 
      title: 'Cash Value',
      sortable: true,
      render: (template: PrizeTemplate) => formatCurrency(template.cash_value)
    },
    { 
      key: 'credit_value', 
      title: 'Credit Value',
      sortable: true,
      render: (template: PrizeTemplate) => formatCurrency(template.credit_value)
    },
    {
      key: 'status',
      title: 'Status',
      sortable: true,
      render: (template: PrizeTemplate) => (
        <Badge className={statusStyles[template.status as keyof typeof statusStyles]}>
          {template.status}
        </Badge>
      )
    },
    { 
      key: 'expiry_days', 
      title: 'Expiry Days',
      sortable: true,
      render: (template: PrizeTemplate) => `${template.expiry_days} days`
    },
    { 
      key: 'created_at', 
      title: 'Created',
      sortable: true,
      render: (template: PrizeTemplate) => 
        new Date(template.created_at).toLocaleDateString()
    }
  ];

  const filteredTemplates = searchTerm
    ? templates.filter(template => 
        template.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        template.type.toLowerCase().includes(searchTerm.toLowerCase()) ||
        template.tier.toLowerCase().includes(searchTerm.toLowerCase()) ||
        template.id.toString().includes(searchTerm)
      )
    : templates;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Prize Templates</h1>
        <Button 
          onClick={() => setIsCreateModalOpen(true)}
          className="flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          New Template
        </Button>
      </div>

      <div className="flex gap-4 items-center">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500 h-4 w-4" />
          <Input
            placeholder="Search templates..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
        <Button variant="outline">
          <Filter className="w-4 h-4 mr-2" />
          Filter
        </Button>
      </div>

      <div className="bg-white rounded-lg shadow">
        {isLoading ? (
          <div className="flex items-center justify-center h-48">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
          </div>
        ) : (
          <SortableDataTable 
            columns={columns} 
            data={filteredTemplates} 
            className="w-full"
          />
        )}
      </div>

      <PrizeTemplateForm 
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSuccess={handleCreateSuccess}
      />
    </div>
  );
};

export default PrizeTemplatesList;