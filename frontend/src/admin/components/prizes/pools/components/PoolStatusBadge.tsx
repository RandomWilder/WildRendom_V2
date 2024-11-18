import { Badge } from "@/admin/components/ui/badge";
import { PrizePoolStatus } from "@/types/prize-pool";
import { cn } from "@/lib/utils";

interface PoolStatusBadgeProps {
  status: PrizePoolStatus;
}

export const PoolStatusBadge = ({ status }: PoolStatusBadgeProps) => {
  const statusConfig = {
    unlocked: {
      variant: "secondary" as const,
      label: "Unlocked",
      className: "bg-blue-100 text-blue-800 hover:bg-blue-100"
    },
    locked: {
      variant: "outline" as const,
      label: "Locked",
      className: "bg-yellow-100 text-yellow-800 hover:bg-yellow-100"
    },
    assigned: {
      variant: "default" as const,
      label: "Assigned",
      className: "bg-green-100 text-green-800 hover:bg-green-100"
    }
  };

  const config = statusConfig[status];

  return (
    <Badge 
      variant={config.variant} 
      className={cn(
        config.className,
        "font-medium"
      )}
    >
      {config.label}
    </Badge>
  );
};