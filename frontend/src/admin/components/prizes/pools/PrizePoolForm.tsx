import { useState } from "react";
import { usePrizePoolStore } from "@/admin/stores/prizePools";
import { useToast } from "@/admin/hooks/useToast";
import { PrizePool } from "@/types/prize-pool";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/admin/components/ui/dialog";
import { Button } from "@/admin/components/ui/button";
import { Label } from "@/admin/components/ui/label";
import { Input } from "@/admin/components/ui/input";

interface PrizePoolFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  poolToEdit?: PrizePool;
}

interface FormState {
  name: string;
  description: string;
}

const defaultFormState: FormState = {
  name: "",
  description: "",
};

export const PrizePoolForm = ({ 
  isOpen, 
  onClose, 
  onSuccess, 
  poolToEdit 
}: PrizePoolFormProps) => {
  const { createPool } = usePrizePoolStore();
  const { toast } = useToast();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formState, setFormState] = useState<FormState>(
    poolToEdit 
      ? { 
          name: poolToEdit.name, 
          description: poolToEdit.description || "" 
        }
      : defaultFormState
  );
  const [errors, setErrors] = useState<Partial<FormState>>({});

  const validateForm = (): boolean => {
    const newErrors: Partial<FormState> = {};

    if (!formState.name.trim()) {
      newErrors.name = "Name is required";
    } else if (formState.name.length < 3) {
      newErrors.name = "Name must be at least 3 characters";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      await createPool({
        name: formState.name.trim(),
        description: formState.description.trim(),
        // status is enforced as 'unlocked' in the store's createPool method
      });

      toast({
        title: "Success",
        description: "Prize pool created successfully",
      });

      onSuccess();
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to create prize pool",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setFormState(prev => ({ ...prev, [name]: value }));
    // Clear error when user starts typing
    if (errors[name as keyof FormState]) {
      setErrors(prev => ({ ...prev, [name]: undefined }));
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px] bg-white border-2 shadow-lg">
        <DialogHeader className="border-b pb-4">
          <DialogTitle className="text-xl font-semibold text-gray-900">
            {poolToEdit ? "Edit Prize Pool" : "Create New Prize Pool"}
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6 py-4">
          <div className="space-y-4">
            <div className="space-y-2">
              <Label 
                htmlFor="name" 
                className="text-sm font-medium text-gray-700 required"
              >
                Pool Name
              </Label>
              <Input
                id="name"
                name="name"
                value={formState.name}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md 
                  focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                  placeholder:text-gray-400"
                placeholder="Enter pool name"
              />
              {errors.name && (
                <p className="text-sm text-red-500 mt-1">{errors.name}</p>
              )}
            </div>            
            <div className="space-y-2">
                <Label 
                htmlFor="description" 
                className="text-sm font-medium text-gray-700"
                >
                Description
                </Label>
                <textarea
                id="description"
                name="description"
                value={formState.description}
                onChange={handleChange}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md 
                    focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter pool description"
                />
                {errors.description && (
                <p className="text-sm text-red-500 mt-1">{errors.description}</p>
                )}
            </div>
        </div>
          <DialogFooter className="border-t pt-4 mt-6">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              className="mr-2 border-gray-300 text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </Button>
            <Button 
              type="submit"
              className="bg-blue-600 text-white hover:bg-blue-700"
            disabled={isSubmitting}
            >
              {isSubmitting ? "Submitting..." : poolToEdit ? "Update" : "Create"} Pool
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};