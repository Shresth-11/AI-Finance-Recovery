import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 tabular-nums select-none",
  {
    variants: {
      variant: {
        default: "border-transparent bg-primary text-primary-foreground",
        secondary: "border-transparent bg-secondary text-secondary-foreground",
        outline: "text-foreground border-border",
        critical: "border-red-300 bg-red-100/90 text-red-900 font-bold dark:border-red-800 dark:bg-red-950 dark:text-red-200",
        high: "border-amber-300 bg-amber-100/90 text-amber-900 font-bold dark:border-amber-800 dark:bg-amber-950 dark:text-amber-200",
        medium: "border-blue-300 bg-blue-100/90 text-blue-900 font-bold dark:border-blue-800 dark:bg-blue-950 dark:text-blue-200",
        low: "border-slate-300 bg-slate-200/90 text-slate-900 font-bold dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200",
        resolved: "border-emerald-300 bg-emerald-100/90 text-emerald-900 font-bold dark:border-emerald-800 dark:bg-emerald-950 dark:text-emerald-200",
        ai: "border-violet-300 bg-violet-100/90 text-violet-900 font-bold dark:border-violet-800 dark:bg-violet-950 dark:text-violet-200",
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
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
