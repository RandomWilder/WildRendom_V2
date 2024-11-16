import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../ui/dialog';
import { Button } from '../ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Switch } from '../ui/switch';
import { useToast } from '../../hooks/useToast';
import { apiClient } from '../../../api/client';

// Keep all interfaces and initialFormData the same
interface PrizeTemplateFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

interface FormData {
  name: string;
  description: string;
  type: string;
  tier: string;
  retail_value: number;
  cash_value: number;
  credit_value: number;
  expiry_days: number;
  claim_deadline_hours: number;
  auto_claim_credit: boolean;
}

const initialFormData: FormData = {
  name: '',
  description: '',
  type: '',
  tier: '',
  retail_value: 0,
  cash_value: 0,
  credit_value: 0,
  expiry_days: 30,
  claim_deadline_hours: 72,
  auto_claim_credit: false,
};

export const PrizeTemplateForm = ({ isOpen, onClose, onSuccess }: PrizeTemplateFormProps) => {
  // Keep all state and handlers the same
  const [formData, setFormData] = useState<FormData>(initialFormData);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleNumberChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: parseFloat(value) || 0
    }));
  };

  const handleSelectChange = (name: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      await apiClient.post('/api/admin/prizes/create', formData);
      
      toast({
        title: "Success",
        description: "Prize template created successfully",
      });
      
      onSuccess();
      onClose();
      setFormData(initialFormData);
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.response?.data?.error || "Failed to create prize template",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[600px] p-4 bg-white">
        <DialogHeader className="mb-2">
          <DialogTitle>Create New Prize Template</DialogTitle>
        </DialogHeader>
        
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                required
              />
            </div>

            <div className="space-y-1">
              <Label htmlFor="type">Type</Label>
              <Select
                value={formData.type}
                onValueChange={(value) => handleSelectChange('type', value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select type" />
                </SelectTrigger>
                <SelectContent className="bg-gray-100 border shadow-md">
                  <SelectItem value="Instant_Win">Instant Win</SelectItem>
                  <SelectItem value="Draw_Win">Draw Win</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1">
              <Label htmlFor="tier">Tier</Label>
              <Select
                value={formData.tier}
                onValueChange={(value) => handleSelectChange('tier', value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select tier" />
                </SelectTrigger>
                <SelectContent className="bg-gray-100 border shadow-md">
                  <SelectItem value="platinum">Platinum</SelectItem>
                  <SelectItem value="gold">Gold</SelectItem>
                  <SelectItem value="silver">Silver</SelectItem>
                  <SelectItem value="bronze">Bronze</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="col-span-2 space-y-1">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                required
                rows={2}
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div className="space-y-1">
              <Label htmlFor="retail_value">Retail Value ($)</Label>
              <Input
                id="retail_value"
                name="retail_value"
                type="number"
                min="0"
                step="0.01"
                value={formData.retail_value}
                onChange={handleNumberChange}
                required
              />
            </div>

            <div className="space-y-1">
              <Label htmlFor="cash_value">Cash Value ($)</Label>
              <Input
                id="cash_value"
                name="cash_value"
                type="number"
                min="0"
                step="0.01"
                value={formData.cash_value}
                onChange={handleNumberChange}
                required
              />
            </div>

            <div className="space-y-1">
              <Label htmlFor="credit_value">Credit Value ($)</Label>
              <Input
                id="credit_value"
                name="credit_value"
                type="number"
                min="0"
                step="0.01"
                value={formData.credit_value}
                onChange={handleNumberChange}
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <Label htmlFor="expiry_days">Expiry Days</Label>
              <Input
                id="expiry_days"
                name="expiry_days"
                type="number"
                min="1"
                value={formData.expiry_days}
                onChange={handleNumberChange}
                required
              />
            </div>

            <div className="space-y-1">
              <Label htmlFor="claim_deadline_hours">Claim Deadline (hours)</Label>
              <Input
                id="claim_deadline_hours"
                name="claim_deadline_hours"
                type="number"
                min="1"
                value={formData.claim_deadline_hours}
                onChange={handleNumberChange}
                required
              />
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <Switch
              id="auto_claim_credit"
              checked={formData.auto_claim_credit}
              onCheckedChange={(checked) =>
                setFormData(prev => ({ ...prev, auto_claim_credit: checked }))
              }
            />
            <Label htmlFor="auto_claim_credit">Auto-claim credit option</Label>
          </div>

          <div className="flex justify-end space-x-2 mt-2 bg-white pt-2">
            <Button variant="outline" onClick={onClose} type="button">
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Creating...' : 'Create Template'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};