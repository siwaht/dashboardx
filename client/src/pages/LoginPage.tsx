import { useState } from 'react';
import { useAuth } from '../contexts/SimpleAuthContext';
import { Brain, Sparkles, Shield, Zap, Lock, Mail, User, Building2 } from 'lucide-react';

export function LoginPage() {
  const { signIn, signUp } = useAuth();

  const [isSignUp, setIsSignUp] = useState(false);
  const [loginData, setLoginData] = useState({ email: '', password: '' });
  const [signupData, setSignupData] = useState({
    email: '',
    password: '',
    fullName: '',
    tenantName: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await signIn(loginData.email, loginData.password);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Sign in failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await signUp(
        signupData.email,
        signupData.password,
        signupData.fullName,
        signupData.tenantName
      );
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Sign up failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Animated Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-500 animate-gradient-shift"></div>

      {/* Floating Particles */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-1/4 left-1/4 w-72 h-72 bg-white/10 rounded-full blur-3xl animate-float"></div>
        <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-blue-400/10 rounded-full blur-3xl animate-float-delayed"></div>
        <div className="absolute bottom-1/4 left-1/3 w-80 h-80 bg-purple-400/10 rounded-full blur-3xl animate-float-slow"></div>
      </div>

      {/* Content */}
      <div className="relative z-10 flex min-h-screen">
        {/* Left Side - Branding */}
        <div className="hidden lg:flex lg:w-1/2 flex-col justify-center items-center p-12 text-white">
          <div className="max-w-lg animate-fade-in-up">
            <div className="flex items-center gap-3 mb-8">
              <div className="p-3 bg-white/20 backdrop-blur-lg rounded-2xl">
                <Brain className="w-12 h-12" />
              </div>
              <h1 className="text-5xl font-bold">DashboardX</h1>
            </div>

            <h2 className="text-4xl font-bold mb-6 leading-tight">
              Advanced Agentic RAG Platform
            </h2>

            <p className="text-xl text-white/90 mb-12 leading-relaxed">
              Unlock the power of AI-driven insights with our cutting-edge
              Retrieval-Augmented Generation platform. Experience real-time
              intelligence at your fingertips.
            </p>

            <div className="space-y-6">
              <div className="flex items-center gap-4 group">
                <div className="p-3 bg-white/20 backdrop-blur-lg rounded-xl group-hover:bg-white/30 transition-all">
                  <Sparkles className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="font-semibold text-lg">AI-Powered Insights</h3>
                  <p className="text-white/80">Advanced language models for intelligent responses</p>
                </div>
              </div>

              <div className="flex items-center gap-4 group">
                <div className="p-3 bg-white/20 backdrop-blur-lg rounded-xl group-hover:bg-white/30 transition-all">
                  <Shield className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="font-semibold text-lg">Enterprise Security</h3>
                  <p className="text-white/80">Multi-tenant architecture with fine-grained access control</p>
                </div>
              </div>

              <div className="flex items-center gap-4 group">
                <div className="p-3 bg-white/20 backdrop-blur-lg rounded-xl group-hover:bg-white/30 transition-all">
                  <Zap className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="font-semibold text-lg">Real-time Processing</h3>
                  <p className="text-white/80">Instant responses with streaming capabilities</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Side - Auth Form */}
        <div className="w-full lg:w-1/2 flex items-center justify-center p-8">
          <div className="w-full max-w-md">
            <div className="bg-white/95 backdrop-blur-xl rounded-3xl shadow-2xl p-8 animate-scale-in">
              {/* Logo for Mobile */}
              <div className="lg:hidden flex items-center justify-center gap-2 mb-6">
                <Brain className="w-8 h-8 text-indigo-600" />
                <h1 className="text-2xl font-bold gradient-text">DashboardX</h1>
              </div>

              <div className="text-center mb-8">
                <h2 className="text-3xl font-bold text-gray-900 mb-2">
                  {isSignUp ? 'Create Account' : 'Welcome Back'}
                </h2>
                <p className="text-gray-600">
                  {isSignUp ? 'Join us and start your journey' : 'Sign in to continue to your dashboard'}
                </p>
              </div>

              {error && (
                <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-500 rounded-lg animate-shake">
                  <p className="text-red-700 text-sm font-medium">{error}</p>
                </div>
              )}

              <div className="mb-6 flex bg-gray-100 rounded-xl p-1">
                <button
                  type="button"
                  className={`flex-1 py-2.5 rounded-lg font-medium transition-all duration-300 ${
                    !isSignUp
                      ? 'bg-white text-indigo-600 shadow-md'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                  onClick={() => {
                    setIsSignUp(false);
                    setError('');
                  }}
                  data-testid="tab-signin"
                >
                  Sign In
                </button>
                <button
                  type="button"
                  className={`flex-1 py-2.5 rounded-lg font-medium transition-all duration-300 ${
                    isSignUp
                      ? 'bg-white text-indigo-600 shadow-md'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                  onClick={() => {
                    setIsSignUp(true);
                    setError('');
                  }}
                  data-testid="tab-signup"
                >
                  Sign Up
                </button>
              </div>

              {!isSignUp ? (
                <form onSubmit={handleSignIn} className="space-y-5">
                  <div>
                    <label htmlFor="email" className="block text-sm font-semibold text-gray-700 mb-2">
                      Email Address
                    </label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                      <input
                        id="email"
                        type="email"
                        data-testid="input-email"
                        className="w-full pl-11 pr-4 py-3 border-2 border-gray-200 rounded-xl focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 transition-all outline-none"
                        placeholder="Enter your email"
                        value={loginData.email}
                        onChange={(e) => setLoginData({ ...loginData, email: e.target.value })}
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <label htmlFor="password" className="block text-sm font-semibold text-gray-700 mb-2">
                      Password
                    </label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                      <input
                        id="password"
                        type="password"
                        data-testid="input-password"
                        className="w-full pl-11 pr-4 py-3 border-2 border-gray-200 rounded-xl focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 transition-all outline-none"
                        placeholder="Enter your password"
                        value={loginData.password}
                        onChange={(e) => setLoginData({ ...loginData, password: e.target.value })}
                        required
                      />
                    </div>
                  </div>

                  <button
                    type="submit"
                    className="w-full py-3.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-semibold rounded-xl shadow-lg shadow-indigo-500/50 hover:shadow-xl hover:shadow-indigo-500/60 transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed"
                    disabled={loading}
                    data-testid="button-signin"
                  >
                    {loading ? (
                      <span className="flex items-center justify-center gap-2">
                        <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                        Signing in...
                      </span>
                    ) : (
                      'Sign In'
                    )}
                  </button>
                </form>
              ) : (
                <form onSubmit={handleSignUp} className="space-y-5">
                  <div>
                    <label htmlFor="signup-email" className="block text-sm font-semibold text-gray-700 mb-2">
                      Email Address
                    </label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                      <input
                        id="signup-email"
                        type="email"
                        data-testid="input-signup-email"
                        className="w-full pl-11 pr-4 py-3 border-2 border-gray-200 rounded-xl focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 transition-all outline-none"
                        placeholder="Enter your email"
                        value={signupData.email}
                        onChange={(e) => setSignupData({ ...signupData, email: e.target.value })}
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <label htmlFor="signup-password" className="block text-sm font-semibold text-gray-700 mb-2">
                      Password
                    </label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                      <input
                        id="signup-password"
                        type="password"
                        data-testid="input-signup-password"
                        className="w-full pl-11 pr-4 py-3 border-2 border-gray-200 rounded-xl focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 transition-all outline-none"
                        placeholder="Create a password"
                        value={signupData.password}
                        onChange={(e) => setSignupData({ ...signupData, password: e.target.value })}
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <label htmlFor="fullname" className="block text-sm font-semibold text-gray-700 mb-2">
                      Full Name
                    </label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                      <input
                        id="fullname"
                        data-testid="input-fullname"
                        className="w-full pl-11 pr-4 py-3 border-2 border-gray-200 rounded-xl focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 transition-all outline-none"
                        placeholder="Enter your full name"
                        value={signupData.fullName}
                        onChange={(e) => setSignupData({ ...signupData, fullName: e.target.value })}
                      />
                    </div>
                  </div>

                  <div>
                    <label htmlFor="tenantname" className="block text-sm font-semibold text-gray-700 mb-2">
                      Organization Name
                    </label>
                    <div className="relative">
                      <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                      <input
                        id="tenantname"
                        data-testid="input-tenantname"
                        className="w-full pl-11 pr-4 py-3 border-2 border-gray-200 rounded-xl focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 transition-all outline-none"
                        placeholder="Enter organization name"
                        value={signupData.tenantName}
                        onChange={(e) => setSignupData({ ...signupData, tenantName: e.target.value })}
                      />
                    </div>
                  </div>

                  <button
                    type="submit"
                    className="w-full py-3.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-semibold rounded-xl shadow-lg shadow-indigo-500/50 hover:shadow-xl hover:shadow-indigo-500/60 transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed"
                    disabled={loading}
                    data-testid="button-signup"
                  >
                    {loading ? (
                      <span className="flex items-center justify-center gap-2">
                        <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                        Creating account...
                      </span>
                    ) : (
                      'Create Account'
                    )}
                  </button>
                </form>
              )}
            </div>

            {/* Footer */}
            <p className="text-center mt-6 text-white/80 text-sm">
              By continuing, you agree to our Terms of Service and Privacy Policy
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
