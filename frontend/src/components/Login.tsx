import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

const Login: React.FC<{ onGuest?: () => void }> = ({ onGuest }) => {
  const { login, signUp } = useAuth();
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPass, setConfirmPass] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isLogin && password !== confirmPass) {
      alert("Passwords do not match!");
      return;
    }

    setLoading(true);
    try {
      if (isLogin) {
        await login(email, password);
      } else {
        await signUp(email, password);
      }
    } catch (err) {
      console.error(err);
      alert((isLogin ? 'Login' : 'Sign Up') + ' failed: ' + (err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto bg-slate-900 border border-slate-800 p-6 rounded-lg text-slate-200">
      <h3 className="text-lg font-bold mb-4 text-center">{isLogin ? 'Advocate Login' : 'Create Account'}</h3>
      <form onSubmit={handleSubmit} className="space-y-4">
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none"
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none"
        />
        {!isLogin && (
          <input
            type="password"
            placeholder="Confirm Password"
            value={confirmPass}
            onChange={(e) => setConfirmPass(e.target.value)}
            required
            className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none"
          />
        )}

        <div className="flex flex-col gap-3">
          <button
            type="submit"
            disabled={loading}
            className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded font-semibold disabled:opacity-50 transition-colors"
          >
            {loading ? 'Processing...' : (isLogin ? 'Sign In' : 'Sign Up')}
          </button>

          {onGuest && (
            <button
              type="button"
              onClick={onGuest}
              className="w-full px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded font-medium border border-slate-700 transition-colors"
            >
              Continue as Guest
            </button>
          )}
        </div>
      </form>

      <div className="mt-4 text-center text-sm text-slate-400">
        {isLogin ? (
          <p>
            Don't have an account?{' '}
            <button onClick={() => setIsLogin(false)} className="text-blue-400 hover:underline">
              Sign Up
            </button>
          </p>
        ) : (
          <p>
            Already have an account?{' '}
            <button onClick={() => setIsLogin(true)} className="text-blue-400 hover:underline">
              Log In
            </button>
          </p>
        )}
      </div>
    </div>
  );
};

export default Login;
