import { ButtonHTMLAttributes, ReactNode } from "react";

import { cn } from "@/utils/cn";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode;
  variant?: "primary" | "secondary";
};

export const Button = ({ children, className, variant = "primary", ...props }: ButtonProps) => (
  <button
    className={cn(
      variant === "primary" ? "button-primary" : "button-secondary",
      className,
    )}
    {...props}
  >
    {children}
  </button>
);

