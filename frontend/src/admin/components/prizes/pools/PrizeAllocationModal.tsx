import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/admin/components/ui/label";
import { Select } from "@/admin/components/ui/select";
import { useToast } from "@/admin/hooks/useToast";
import { usePrizePoolStore } from "@/admin/stores/prizePools";
import { PrizeTemplate } from "@/types/prize";
import { PrizePool } from "@/types/prize-pool";
import { AlertCircle } from "lucide-react";

interface PrizeAllocationModalProps {
  isOpen: boolean;
  onClose: () => void;
  pool: PrizePool;
  prizeTemplates: PrizeTemplate[];
  currentTotalOdds: number;
}

interface FormState {
  prizeTemplateId: number | null;
  instanceCount: number;
  collectiveOdds: number;
}

const defaultFormState: FormState = {
  prizeTemplateId: null,
  instanceCount: 1,
  collectiveOdds: 0
};

export const PrizeAllocationModal = ({
  isOpen,
  onClose,
  pool,
  prizeTemplates,
  currentTotalOdds
}: PrizeAllocationModalProps) => {
  const [formState, setFormState] = useState<FormState>(defaultFormState);
  interface FormErrors {
    prizeTemplateId?: string;
    instanceCount?: string;
    collectiveOdds?: string;
  }
  
  const [errors, setErrors] = useState<FormErrors>({});
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validation
    if (!formState.prizeTemplateId) {
      setErrors({ prizeTemplateId: "Please select a prize template" });
      return;
    }

    try {
      const response = await fetch(`/api/admin/prizes/pools/${pool.id}/allocate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prize_template_id: formState.prizeTemplateId,
          instance_count: formState.instanceCount,
          collective_odds: formState.collectiveOdds
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Failed to allocate prizes');
      }

      toast({
        title: "Success",
        description: "Prizes allocated successfully",
      });
      onClose();
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to allocate prizes",
        variant: "destructive",
      });
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Allocate Prizes to Pool: {pool.name}</DialogTitle>
        </DialogHeader>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="prizeTemplateId">Prize Template</Label>
            <Select
              value={formState.prizeTemplateId?.toString()}
              onValueChange={(value) => 
                setFormState(prev => ({ ...prev, prizeTemplateId: parseInt(value) }))
              }
            >
              {prizeTemplates.map((template) => (
                <option key={template.id} value={template.id}>
                  {template.name}
                </option>
              ))}
            </Select>
            {errors.prizeTemplateId && (
              <p className="text-sm text-red-500">{errors.prizeTemplateId}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="instanceCount">Number of Instances</Label>
            <Input
              type="number"
              min="1"
              value={formState.instanceCount}
              onChange={(e) => 
                setFormState(prev => ({ ...prev, instanceCount: parseInt(e.target.value) }))
              }
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="collectiveOdds">
              Collective Odds (%) - Current Total: {currentTotalOdds}%
            </Label>
            <Input
              type="number"
              min="0"
              max={100 - currentTotalOdds}
              step="0.1"
              value={formState.collectiveOdds}
              onChange={(e) => 
                setFormState(prev => ({ ...prev, collectiveOdds: parseFloat(e.target.value) }))
              }
            />
          </div>

          <div className="flex justify-end space-x-2">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit">
              Allocate Prizes
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};