import { HTMLAttributes, forwardRef } from 'react';
import { cn } from '@utils/cn';

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'success' | 'warning' | 'critical' | 'info' | 'outline';
}

export const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = 'default', children, ...props }, ref) => {
    const variantStyles = {
      default: 'bg-info/10 text-info',
      success: 'bg-success/10 text-success',
      warning: 'bg-warning/10 text-warning',
      critical: 'bg-critical/10 text-critical',
      info: 'bg-info/10 text-info',
      outline: 'border border-subtle bg-transparent text-text-secondary',
    };

    return (
      <span
        ref={ref}
        className={cn(
          'inline-flex items-center px-2 py-0.5 rounded-full text-caption font-medium',
          variantStyles[variant],
          className
        )}
        {...props}
      >
        {children}
      </span>
    );
  }
);

Badge.displayName = 'Badge';