import * as React from "react"
import { cn } from "@/lib/utils"

const Input = React.forwardRef<HTMLInputElement, React.ComponentProps<"input">>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        ref={ref}
        data-slot="input"
        className={cn(
          "h-10 w-full min-w-0 rounded-lg border border-border bg-input/30 px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground transition-colors outline-none focus:border-ring focus:ring-1 focus:ring-ring/20 disabled:cursor-not-allowed disabled:opacity-50",
          className
        )}
        {...props}
      />
    )
  }
)
Input.displayName = "Input"

export { Input }
