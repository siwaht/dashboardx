import { useState } from 'react';
import { useAuth } from '../contexts/SimpleAuthContext';

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
    <div className="flex items-center justify-center min-h-screen bg-gray-50">
      <div className="w-full max-w-md p-8 bg-white rounded-lg shadow-lg">
        <h2 className="text-2xl font-bold mb-6 text-center">
          {isSignUp ? 'Create Account' : 'Sign In'}
        </h2>
        
        {error && (
          <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
          </div>
        )}
        
        <div className="mb-4 flex border-b">
          <button
            type="button"
            className={`flex-1 py-2 ${!isSignUp ? 'border-b-2 border-blue-500 text-blue-500' : 'text-gray-500'}`}
            onClick={() => setIsSignUp(false)}
            data-testid="tab-signin"
          >
            Sign In
          </button>
          <button
            type="button"
            className={`flex-1 py-2 ${isSignUp ? 'border-b-2 border-blue-500 text-blue-500' : 'text-gray-500'}`}
            onClick={() => setIsSignUp(true)}
            data-testid="tab-signup"
          >
            Sign Up
          </button>
        </div>
        
        {!isSignUp ? (
          <form onSubmit={handleSignIn} className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">Email</label>
              <input
                id="email"
                type="email"
                data-testid="input-email"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                value={loginData.email}
                onChange={(e) => setLoginData({ ...loginData, email: e.target.value })}
                required
              />
            </div>
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">Password</label>
              <input
                id="password"
                type="password"
                data-testid="input-password"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                value={loginData.password}
                onChange={(e) => setLoginData({ ...loginData, password: e.target.value })}
                required
              />
            </div>
            <button
              type="submit"
              className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-md disabled:opacity-50"
              disabled={loading}
              data-testid="button-signin"
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleSignUp} className="space-y-4">
            <div>
              <label htmlFor="signup-email" className="block text-sm font-medium text-gray-700">Email</label>
              <input
                id="signup-email"
                type="email"
                data-testid="input-signup-email"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                value={signupData.email}
                onChange={(e) => setSignupData({ ...signupData, email: e.target.value })}
                required
              />
            </div>
            <div>
              <label htmlFor="signup-password" className="block text-sm font-medium text-gray-700">Password</label>
              <input
                id="signup-password"
                type="password"
                data-testid="input-signup-password"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                value={signupData.password}
                onChange={(e) => setSignupData({ ...signupData, password: e.target.value })}
                required
              />
            </div>
            <div>
              <label htmlFor="fullname" className="block text-sm font-medium text-gray-700">Full Name</label>
              <input
                id="fullname"
                data-testid="input-fullname"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                value={signupData.fullName}
                onChange={(e) => setSignupData({ ...signupData, fullName: e.target.value })}
              />
            </div>
            <div>
              <label htmlFor="tenantname" className="block text-sm font-medium text-gray-700">Organization Name</label>
              <input
                id="tenantname"
                data-testid="input-tenantname"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                value={signupData.tenantName}
                onChange={(e) => setSignupData({ ...signupData, tenantName: e.target.value })}
              />
            </div>
            <button
              type="submit"
              className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-md disabled:opacity-50"
              disabled={loading}
              data-testid="button-signup"
            >
              {loading ? 'Creating account...' : 'Sign Up'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
