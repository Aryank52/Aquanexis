import { forwardRef, ButtonHTMLAttributes } from 'react';
import { cn } from '@utils/cn';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'success';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  iconLeft?: React.ReactNode;
  iconRight?: React.ReactNode;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', loading, iconLeft, iconRight, disabled, children, ...props }, ref) => {
    const baseStyles = 'inline-flex items-center justify-center gap-2 font-medium rounded-button transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-info focus-visible:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed';

    const variantStyles = {
      primary: 'bg-info text-white hover:bg-info/90 active:bg-info active:scale-[0.98]',
      secondary: 'bg-surface text-text-primary border border-subtle hover:bg-hover active:bg-active active:scale-[0.98]',
      ghost: 'bg-transparent text-text-primary hover:bg-hover active:bg-active active:scale-[0.98]',
      danger: 'bg-critical text-white hover:bg-critical/90 active:bg-critical active:scale-[0.98]',
      success: 'bg-success text-white hover:bg-success/90 active:bg-success active:scale-[0.98]',
    };

    const sizeStyles = {
      sm: 'px-3 py-1.5 text-caption gap-1.5',
      md: 'px-4 py-2 text-body-sm gap-2',
      lg: 'px-6 py-3 text-body-lg gap-2',
    };

    return (
      <button
        ref={ref}
        className={cn(baseStyles, variantStyles[variant], sizeStyles[size], className)}
        disabled={disabled || loading}
        {...props}
      >
        {loading && (
          <svg className="animate-spin w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
        )}
        {!loading && iconLeft && <span className="flex-shrink-0">{iconLeft}</span>}
        {children}
        {!loading && iconRight && <span className="flex-shrink-0">{iconRight}</span>}
      </button>
    );
  }
);

Button.displayName = 'Button';