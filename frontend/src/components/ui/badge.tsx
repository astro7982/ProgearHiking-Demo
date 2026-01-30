"use client";

import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default: "bg-forest-100 text-forest-800 dark:bg-forest-900 dark:text-forest-100",
        secondary: "bg-stone-100 text-stone-800 dark:bg-stone-800 dark:text-stone-100",
        destructive: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100",
        outline: "border border-current",
        salesforce: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-100",
        inventory: "bg-forest-100 text-forest-800 dark:bg-forest-900 dark:text-forest-100",
        success: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100",
        warning: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-100",
        info: "bg-summit-100 text-summit-800 dark:bg-summit-900 dark:text-summit-100",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {
  icon?: React.ReactNode;
}

function Badge({ className, variant, icon, children, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props}>
      {icon && <span className="mr-1">{icon}</span>}
      {children}
    </div>
  );
}

export { Badge, badgeVariants };
