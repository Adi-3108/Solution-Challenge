import { HTMLAttributes, ReactNode } from "react";

import { cn } from "@/utils/cn";

type CardProps = HTMLAttributes<HTMLDivElement> & {
  children: ReactNode;
};

export const Card = ({ children, className, ...props }: CardProps) => (
  <div className={cn("panel p-5", className)} {...props}>
    {children}
  </div>
);

