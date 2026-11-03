import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { Droplet, Eye, EyeOff, AlertCircle } from 'lucide-react';
import { useAuth } from '@/state/auth';
import { getErrorMessage } from '@/api/client';
import { cn } from '@utils/cn';

// Import zodResolver dynamically to avoid TypeScript type issues with @hookform/resolvers@3.x
let zodResolver: any = null;
async function getZodResolver() {
  if (!zodResolver) {
    const mod = await import('@hookform/resolvers/zod');
    zodResolver = (mod as any).zodResolver;
  }
  return zodResolver;
}

const schema = z.object({
  username: z.string().min(1, 'Username is required'),
  password: z.string().min(1, 'Password is required'),
});

type FormData = z.infer<typeof schema>;

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: string })?.from || '/dashboard';

  const [showPassword, setShowPassword] = useState(false);
  const [serverError, setServerError] = useState('');
  const [resolver, setResolver] = useState<any>(null);

  // Initialize zodResolver lazily
  useEffect(() => {
    getZodResolver().then(setResolver);
  }, []);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    resolver: resolver ? resolver(schema) : undefined,
    defaultValues: {
      username: 'admin',
      password: 'password123',
    },
  });

  const onSubmit = async (data: FormData) => {
    setServerError('');
    try {
      await login(data);
      navigate(from, { replace: true });
    } catch (err) {
      setServerError(getErrorMessage(err));
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-base p-6">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="mb-8 flex animate-fade-in flex-col items-center">
          <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-info">
            <Droplet className="h-7 w-7 text-white" />
          </div>
          <h1 className="text-text-primary text-h2 font-semibold">Sign in to AquaNexis</h1>
          <p className="mt-1 text-center text-body-sm text-text-secondary">
            Predictive Water Intelligence Platform
          </p>
        </div>

        {/* Card */}
        <div className="border-subtle animate-slide-up rounded-card border bg-surface p-6 shadow-card">
          {serverError && (
            <div
              className="mb-4 flex items-start gap-2 rounded-button border border-critical/20 bg-critical/10 p-3"
              role="alert"
            >
              <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0 text-critical" />
              <p className="text-body-sm text-critical">{serverError}</p>
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
            <div>
              <label className="label" htmlFor="username">
                Username
              </label>
              <input
                id="username"
                type="text"
                autoComplete="username"
                autoFocus
                className={cn('input', errors.username && 'border-critical focus:ring-critical')}
                aria-describedby={errors.username ? 'username-error' : undefined}
                aria-invalid={!!errors.username}
                {...register('username')}
              />
              {errors.username && (
                <p id="username-error" className="mt-1 text-caption text-critical" role="alert">
                  {errors.username.message}
                </p>
              )}
            </div>

            <div>
              <label className="label" htmlFor="password">
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  className={cn(
                    'input pr-10',
                    errors.password && 'border-critical focus:ring-critical'
                  )}
                  aria-describedby={errors.password ? 'password-error' : undefined}
                  aria-invalid={!!errors.password}
                  {...register('password')}
                />
                <button
                  type="button"
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted transition-colors hover:text-text-secondary"
                  onClick={() => setShowPassword(v => !v)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="w-4 w-4" />}
                </button>
              </div>
              {errors.password && (
                <p id="password-error" className="mt-1 text-caption text-critical" role="alert">
                  {errors.password.message}
                </p>
              )}
            </div>

            <button type="submit" disabled={isSubmitting} className="btn btn-primary mt-2 w-full">
              {isSubmitting ? (
                <>
                  <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                    />
                  </svg>
                  Signing in…
                </>
              ) : (
                'Sign In'
              )}
            </button>
          </form>
        </div>

        <p className="mt-6 text-center text-caption text-text-muted">
          AquaNexis — Engineering-grade water monitoring
        </p>
      </div>
    </div>
  );
}
