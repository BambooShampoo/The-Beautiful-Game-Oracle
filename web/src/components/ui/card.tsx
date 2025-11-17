"use client";

import type { HTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/cn";

type CardProps = HTMLAttributes<HTMLDivElement> & {
  highlight?: ReactNode;
};

export function Card({ className, children, highlight, ...rest }: CardProps) {
  return (
    <div
      className={cn(
        "rounded-3xl border border-white/5 bg-surface/80 p-6 shadow-xl shadow-black/20 backdrop-blur",
        className,
      )}
      {...rest}
    >
      {highlight ? (
        <div className="mb-4 inline-flex items-center gap-2 text-sm text-brand-accent">
          {highlight}
        </div>
      ) : null}
      {children}
    </div>
  );
}

type CardTitleProps = HTMLAttributes<HTMLHeadingElement>;

export function CardTitle({ className, ...rest }: CardTitleProps) {
  return (
    <h3
      className={cn(
        "text-lg font-semibold tracking-tight text-foreground/90",
        className,
      )}
      {...rest}
    />
  );
}

type CardBodyProps = HTMLAttributes<HTMLParagraphElement>;

export function CardBody({ className, ...rest }: CardBodyProps) {
  return (
    <p
      className={cn("text-sm text-muted", className)}
      {...rest}
    />
  );
}
