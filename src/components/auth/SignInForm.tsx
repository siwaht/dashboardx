import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { LogIn, Mail, Lock, AlertCircle, Loader2 } from 'lucide-react';

export function SignInForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [focusedField, setFocusedField] = useState<string | null>(null);
  const { signIn } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await signIn(email, password);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to sign in');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Email Field */}
      <div className="space-y-2">
        <label htmlFor="email" className="block text-sm font-semibold text-gray-700">
          Email Address
        </label>
        <div className="relative group">
          <div className={`absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none transition-colors duration-300 ${
            focusedField === 'email' ? 'text-purple-600' : 'text-gray-400'
          }`}>
            <Mail size={20} />
          </div>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            onFocus={() => setFocusedField('email')}
            onBlur={() => setFocusedField(null)}
            required
            className="w-full pl-12 pr-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-300 bg-white hover:border-gray-300 hover:shadow-md focus:shadow-lg placeholder-gray-400"
            placeholder="you@example.com"
          />
          {focusedField === 'email' && (
            <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-pink-500/10 pointer-events-none animate-pulse-slow"></div>
          )}
        </div>
      </div>

      {/* Password Field */}
      <div className="space-y-2">
        <label htmlFor="password" className="block text-sm font-semibold text-gray-700">
          Password
        </label>
        <div className="relative group">
          <div className={`absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none transition-colors duration-300 ${
            focusedField === 'password' ? 'text-purple-600' : 'text-gray-400'
          }`}>
            <Lock size={20} />
          </div>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onFocus={() => setFocusedField('password')}
            onBlur={() => setFocusedField(null)}
            required
            className="w-full pl-12 pr-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-300 bg-white hover:border-gray-300 hover:shadow-md focus:shadow-lg placeholder-gray-400"
            placeholder="••••••••"
          />
          {focusedField === 'password' && (
            <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-pink-500/10 pointer-events-none animate-pulse-slow"></div>
          )}
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="relative overflow-hidden rounded-xl bg-gradient-to-r from-red-50 to-rose-50 border-2 border-red-200 p-4 animate-shake">
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-red-500 to-rose-500 rounded-xl flex items-center justify-center shadow-lg">
              <AlertCircle className="text-white" size={20} />
            </div>
            <div className="flex-1">
              <p className="text-sm font-semibold text-red-800">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Submit Button */}
      <button
        type="submit"
        disabled={loading}
        className="w-full relative group overflow-hidden px-6 py-4 bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 text-white rounded-xl font-semibold shadow-lg shadow-purple-500/30 hover:shadow-xl hover:shadow-purple-500/40 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 hover:scale-[1.02] active:scale-[0.98]"
      >
        {/* Shimmer Effect */}
        <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/20 to-white/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700"></div>
        
        {/* Button Content */}
        <span className="relative flex items-center justify-center gap-2">
          {loading ? (
            <>
              <Loader2 size={20} className="animate-spin" />
              <span>Signing in...</span>
            </>
          ) : (
            <>
              <LogIn size={20} />
              <span>Sign In</span>
            </>
          )}
        </span>
      </button>

      {/* Forgot Password Link */}
      <div className="text-center">
        <button
          type="button"
          className="text-sm font-medium text-gray-600 hover:text-purple-600 transition-colors duration-300"
        >
          Forgot your password?
        </button>
      </div>
    </form>
  );
}
