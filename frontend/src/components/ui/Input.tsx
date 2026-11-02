import { forwardRef, type InputHTMLAttributes } from 'react';
import { cn } from '@utils/cn';

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        'flex h-9 w-full rounded-button border border-subtle bg-background px-3 py-1.5 text-body-sm',
        'placeholder:text-text-muted',
        'focus:outline-none focus:ring-2 focus:ring-info focus:border-transparent',
        'disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-surface',
        'transition-colors duration-150',
        className
      )}
      {...props}
    />
  )
);

Input.displayName = 'Input';