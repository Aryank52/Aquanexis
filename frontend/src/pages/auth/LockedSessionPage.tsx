import { useState } from 'react';
import { Lock, Eye, EyeOff } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/state/auth';
import { getErrorMessage } from '@/api/client';
import { cn } from '@utils/cn';

export function LockedSessionPage() {
  const { user, login, logout } = useAuth();
  const navigate = useNavigate();
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleUnlock = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) {
      navigate('/login', { replace: true });
      return;
    }
    setError('');
    setLoading(true);
    try {
      await login({ username: user.username!, password });
      navigate('/dashboard', { replace: true });
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-base p-6">
      <div className="w-full max-w-sm animate-fade-in">
        <div className="mb-8 flex flex-col items-center">
          <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-info/10">
            <Lock className="h-7 w-7 text-info" />
          </div>
          <h1 className="text-text-primary text-h2 font-semibold">Session Locked</h1>
          {user && (
            <p className="mt-1 text-body-sm text-text-secondary">
              Signed in as{' '}
              <span className="text-text-primary font-medium">{user.display_name}</span>
            </p>
          )}
        </div>

        <div className="border-subtle rounded-card border bg-surface p-6 shadow-card">
          {error && (
            <div className="mb-4 rounded-button border border-critical/20 bg-critical/10 p-3">
              <p className="text-body-sm text-critical">{error}</p>
            </div>
          )}
          <form onSubmit={handleUnlock} className="space-y-4">
            <div>
              <label className="label" htmlFor="lock-password">
                Password
              </label>
              <div className="relative">
                <input
                  id="lock-password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  autoFocus
                  className="input pr-10"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                />
                <button
                  type="button"
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted"
                  onClick={() => setShowPassword(v => !v)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>
            <button
              type="submit"
              disabled={loading || !password}
              className="btn btn-primary w-full"
            >
              {loading ? 'Unlocking…' : 'Unlock Session'}
            </button>
          </form>
          {/* Extensible MFA surface — rendered when backend supports it */}
          {/* <MFAReauthSection /> */}
        </div>

        <button className="btn btn-ghost mt-4 w-full text-text-muted" onClick={() => logout()}>
          Sign in with a different account
        </button>
      </div>
    </div>
  );
}
