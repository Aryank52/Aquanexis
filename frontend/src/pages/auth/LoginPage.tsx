import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Droplet, Eye, EyeOff, AlertCircle } from 'lucide-react';
import { useAuth } from '@/state/auth';
import { getErrorMessage } from '@/api/client';
import { cn } from '@/utils/cn';

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

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data: FormData) => {
    setServerError('');
    try {
      await login(data.username, data.password);
      navigate(from, { replace: true });
    } catch (err) {
      setServerError(getErrorMessage(err));
    }
  };

  return (
    <div className="min-h-screen bg-base flex items-center justify-center p-6">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8 animate-fade-in">
          <div className="w-12 h-12 bg-info rounded-xl flex items-center justify-center mb-4">
            <Droplet className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-h2 font-semibold text-text-primary">Sign in to AquaNexis</h1>
          <p className="text-body-sm text-text-secondary mt-1 text-center">
            Predictive Water Intelligence Platform
          </p>
        </div>

        {/* Card */}
        <div className="bg-surface border border-subtle rounded-card p-6 shadow-card animate-slide-up">
          {serverError && (
            <div className="flex items-start gap-2 p-3 bg-critical/10 border border-critical/20 rounded-button mb-4"
              role="alert">
              <AlertCircle className="w-4 h-4 text-critical flex-shrink-0 mt-0.5" />
              <p className="text-body-sm text-critical">{serverError}</p>
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
            <div>
              <label className="label" htmlFor="username">Username</label>
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
              <label className="label" htmlFor="password">Password</label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  className={cn('input pr-10', errors.password && 'border-critical focus:ring-critical')}
                  aria-describedby={errors.password ? 'password-error' : undefined}
                  aria-invalid={!!errors.password}
                  {...register('password')}
                />
                <button
                  type="button"
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-secondary transition-colors"
                  onClick={() => setShowPassword((v) => !v)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {errors.password && (
                <p id="password-error" className="mt-1 text-caption text-critical" role="alert">
                  {errors.password.message}
                </p>
              )}
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="btn btn-primary w-full mt-2"
            >
              {isSubmitting ? (
                <>
                  <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Signing in…
                </>
              ) : (
                'Sign In'
              )}
            </button>
          </form>
        </div>

        <p className="text-caption text-text-muted text-center mt-6">
          AquaNexis — Engineering-grade water monitoring
        </p>
      </div>
    </div>
  );
}
