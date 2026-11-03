import { forwardRef, type SelectHTMLAttributes } from 'react';
import { cn } from '@utils/cn';

export const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement>>(
  ({ className, ...props }, ref) => (
    <select
      ref={ref}
      className={cn(
        'border-subtle bg-background flex h-9 w-full rounded-button border px-3 py-1.5 text-body-sm',
        'focus:border-transparent focus:outline-none focus:ring-2 focus:ring-info',
        'disabled:cursor-not-allowed disabled:bg-surface disabled:opacity-50',
        'transition-colors duration-150',
        className
      )}
      {...props}
    />
  )
);

Select.displayName = 'Select';

export const SelectContent = ({ children }: { children: React.ReactNode }) => (
  <div className="relative z-50">{children}</div>
);

export const SelectItem = ({ value, children }: { value: string; children: React.ReactNode }) => (
  <option value={value}>{children}</option>
);

export const SelectTrigger = Select;
export const SelectValue = ({ placeholder }: { placeholder: string }) => (
  <option value="" disabled>
    {placeholder}
  </option>
);
