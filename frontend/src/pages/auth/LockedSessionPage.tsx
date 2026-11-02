import { useState } from 'react';
import { Lock, Eye, EyeOff } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/state/auth';
import { getErrorMessage } from '@/api/client';
import { cn } from '@/utils/cn';

export function LockedSessionPage() {
  const { user, login, logout } = useAuth();
  const navigate = useNavigate();
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleUnlock = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) { navigate('/login', { replace: true }); return; }
    setError('');
    setLoading(true);
    try {
      await login(user.username, password);
      navigate('/dashboard', { replace: true });
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-base flex items-center justify-center p-6">
      <div className="w-full max-w-sm animate-fade-in">
        <div className="flex flex-col items-center mb-8">
          <div className="w-14 h-14 bg-info/10 rounded-full flex items-center justify-center mb-4">
            <Lock className="w-7 h-7 text-info" />
          </div>
          <h1 className="text-h2 font-semibold text-text-primary">Session Locked</h1>
          {user && (
            <p className="text-body-sm text-text-secondary mt-1">
              Signed in as <span className="font-medium text-text-primary">{user.display_name}</span>
            </p>
          )}
        </div>

        <div className="bg-surface border border-subtle rounded-card p-6 shadow-card">
          {error && (
            <div className="p-3 bg-critical/10 border border-critical/20 rounded-button mb-4">
              <p className="text-body-sm text-critical">{error}</p>
            </div>
          )}
          <form onSubmit={handleUnlock} className="space-y-4">
            <div>
              <label className="label" htmlFor="lock-password">Password</label>
              <div className="relative">
                <input
                  id="lock-password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  autoFocus
                  className="input pr-10"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
                <button type="button"
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted"
                  onClick={() => setShowPassword(v => !v)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}>
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>
            <button type="submit" disabled={loading || !password} className="btn btn-primary w-full">
              {loading ? 'Unlocking…' : 'Unlock Session'}
            </button>
          </form>
          {/* Extensible MFA surface — rendered when backend supports it */}
          {/* <MFAReauthSection /> */}
        </div>

        <button
          className="btn btn-ghost w-full mt-4 text-text-muted"
          onClick={() => logout()}
        >
          Sign in with a different account
        </button>
      </div>
    </div>
  );
}
