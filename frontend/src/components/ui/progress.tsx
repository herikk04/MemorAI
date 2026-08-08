import * as React from "react";

import { cn } from "@/lib/utils";

/**
 * Progress — Design System MemorAI §6.5
 * Container h-1.5 sobre bg-muted, fill bg-primary.
 * §11: esconder barra de 0% (passar 0 mostra apenas o trilho).
 */
const Progress = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & { value?: number; max?: number }
>(({ className, value = 0, max = 100, ...props }, ref) => {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));
  return (
    <div
      ref={ref}
      role="progressbar"
      aria-valuenow={value}
      aria-valuemin={0}
      aria-valuemax={max}
      className={cn(
        "h-1.5 w-full overflow-hidden rounded-full bg-muted",
        className
      )}
      {...props}
    >
      {pct > 0 ? (
        <div
          className="h-full rounded-full bg-primary transition-all duration-300 ease-in-out"
          style={{ width: `${pct}%` }}
        />
      ) : null}
    </div>
  );
});
Progress.displayName = "Progress";

export { Progress };
