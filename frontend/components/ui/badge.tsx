import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none",
  {
    variants: {
      variant: {
        default: "border-[#262626] bg-[#f5f5f5] text-[#0a0a0a]",
        secondary: "border-[#262626] bg-[#171717] text-[#f5f5f5]",
        destructive:
          "border-[#ef4444] bg-[#ef4444] text-[#f5f5f5]",
        outline: "border-[#262626] text-[#f5f5f5]",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { Badge, badgeVariants };
