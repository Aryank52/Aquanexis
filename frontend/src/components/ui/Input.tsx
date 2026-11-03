import { forwardRef, type InputHTMLAttributes } from 'react';
import { cn } from '@utils/cn';

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        'border-subtle bg-background flex h-9 w-full rounded-button border px-3 py-1.5 text-body-sm',
        'placeholder:text-text-muted',
        'focus:border-transparent focus:outline-none focus:ring-2 focus:ring-info',
        'disabled:cursor-not-allowed disabled:bg-surface disabled:opacity-50',
        'transition-colors duration-150',
        className
      )}
      {...props}
    />
  )
);

Input.displayName = 'Input';
