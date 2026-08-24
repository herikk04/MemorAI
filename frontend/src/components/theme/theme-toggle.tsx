import { Moon, Sun } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useTheme } from "@/components/theme/theme-provider";

/**
 * ThemeToggle — Design System MemorAI §9
 * Transição rotate 200ms ease-in-out ao trocar de tema.
 */
export function ThemeToggle() {
  const { resolvedTheme, toggle } = useTheme();
  const isDark = resolvedTheme === "dark";

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          onClick={toggle}
          aria-label={isDark ? "Mudar para tema claro" : "Mudar para tema escuro"}
        >
          <Sun
            className="size-5 stroke-2 transition-transform duration-200 ease-in-out rotate-0 scale-100 dark:-rotate-90 dark:scale-0"
            aria-hidden
          />
          <Moon
            className="absolute size-5 stroke-2 transition-transform duration-200 ease-in-out rotate-90 scale-0 dark:rotate-0 dark:scale-100"
            aria-hidden
          />
        </Button>
      </TooltipTrigger>
      <TooltipContent>{isDark ? "Tema claro" : "Tema escuro"}</TooltipContent>
    </Tooltip>
  );
}
