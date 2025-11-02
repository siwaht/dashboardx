import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { UserPlus, Mail, Lock, User, Building2, AlertCircle, Loader2, CheckCircle2, XCircle } from 'lucide-react';

export function SignUpForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [tenantName, setTenantName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [focusedField, setFocusedField] = useState<string | null>(null);
  const { signUp } = useAuth();

  // Password strength indicator
  const getPasswordStrength = (pwd: string) => {
    if (pwd.length === 0) return { strength: 0, label: '', color: '' };
    if (pwd.length < 6) return { strength: 1, label: 'Weak', color: 'text-red-600' };
    if (pwd.length < 10) return { strength: 2, label: 'Fair', color: 'text-yellow-600' };
    if (pwd.length < 14) return { strength: 3, label: 'Good', color: 'text-blue-600' };
    return { strength: 4, label: 'Strong', color: 'text-green-600' };
  };

  const passwordStrength = getPasswordStrength(password);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await signUp(email, password, fullName, tenantName);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to sign up');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* Full Name Field */}
      <div className="space-y-2">
        <label htmlFor="fullName" className="block text-sm font-semibold text-gray-700">
          Full Name
        </label>
        <div className="relative group">
          <div className={`absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none transition-colors duration-300 ${
            focusedField === 'fullName' ? 'text-purple-600' : 'text-gray-400'
          }`}>
            <User size={20} />
          </div>
          <input
            id="fullName"
            type="text"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            onFocus={() => setFocusedField('fullName')}
            onBlur={() => setFocusedField(null)}
            required
            className="w-full pl-12 pr-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-300 bg-white hover:border-gray-300 hover:shadow-md focus:shadow-lg placeholder-gray-400"
            placeholder="John Doe"
          />
          {focusedField === 'fullName' && (
            <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-pink-500/10 pointer-events-none animate-pulse-slow"></div>
          )}
        </div>
      </div>

      {/* Organization Name Field */}
      <div className="space-y-2">
        <label htmlFor="tenantName" className="block text-sm font-semibold text-gray-700">
          Organization Name
        </label>
        <div className="relative group">
          <div className={`absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none transition-colors duration-300 ${
            focusedField === 'tenantName' ? 'text-purple-600' : 'text-gray-400'
          }`}>
            <Building2 size={20} />
          </div>
          <input
            id="tenantName"
            type="text"
            value={tenantName}
            onChange={(e) => setTenantName(e.target.value)}
            onFocus={() => setFocusedField('tenantName')}
            onBlur={() => setFocusedField(null)}
            required
            className="w-full pl-12 pr-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-300 bg-white hover:border-gray-300 hover:shadow-md focus:shadow-lg placeholder-gray-400"
            placeholder="Acme Corp"
          />
          {focusedField === 'tenantName' && (
            <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-pink-500/10 pointer-events-none animate-pulse-slow"></div>
          )}
        </div>
      </div>

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
            minLength={6}
            className="w-full pl-12 pr-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-300 bg-white hover:border-gray-300 hover:shadow-md focus:shadow-lg placeholder-gray-400"
            placeholder="••••••••"
          />
          {focusedField === 'password' && (
            <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-pink-500/10 pointer-events-none animate-pulse-slow"></div>
          )}
        </div>
        
        {/* Password Strength Indicator */}
        {password.length > 0 && (
          <div className="space-y-2 animate-fade-in">
            <div className="flex items-center gap-2">
              <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all duration-300 ${
                    passwordStrength.strength === 1 ? 'bg-red-500 w-1/4' :
                    passwordStrength.strength === 2 ? 'bg-yellow-500 w-2/4' :
                    passwordStrength.strength === 3 ? 'bg-blue-500 w-3/4' :
                    'bg-green-500 w-full'
                  }`}
                ></div>
              </div>
              <span className={`text-xs font-semibold ${passwordStrength.color}`}>
                {passwordStrength.label}
              </span>
            </div>
            <div className="flex items-start gap-2 text-xs text-gray-600">
              {password.length >= 6 ? (
                <CheckCircle2 size={14} className="text-green-600 mt-0.5 flex-shrink-0" />
              ) : (
                <XCircle size={14} className="text-gray-400 mt-0.5 flex-shrink-0" />
              )}
              <span>Minimum 6 characters</span>
            </div>
          </div>
        )}
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
              <span>Creating account...</span>
            </>
          ) : (
            <>
              <UserPlus size={20} />
              <span>Create Account</span>
            </>
          )}
        </span>
      </button>

      {/* Terms Notice */}
      <p className="text-xs text-center text-gray-600">
        By signing up, you agree to our{' '}
        <button type="button" className="text-purple-600 hover:text-purple-700 font-medium transition-colors">
          Terms of Service
        </button>{' '}
        and{' '}
        <button type="button" className="text-purple-600 hover:text-purple-700 font-medium transition-colors">
          Privacy Policy
        </button>
      </p>
    </form>
  );
}
