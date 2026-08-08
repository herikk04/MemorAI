import { Moon, Sun } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { useTheme } from "@/components/theme/theme-provider";

export function ThemeToggle() {
  const { resolvedTheme, toggle } = useTheme();

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          onClick={toggle}
          aria-label="Alternar tema"
        >
          {resolvedTheme === "dark" ? (
            <Sun className="size-5" />
          ) : (
            <Moon className="size-5" />
          )}
        </Button>
      </TooltipTrigger>
      <TooltipContent>
        {resolvedTheme === "dark" ? "Tema claro" : "Tema escuro"}
      </TooltipContent>
    </Tooltip>
  );
}
