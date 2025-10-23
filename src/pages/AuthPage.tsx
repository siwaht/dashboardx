import React, { useState } from 'react';
import { SignInForm } from '../components/auth/SignInForm';
import { SignUpForm } from '../components/auth/SignUpForm';
import { Brain, Sparkles, Shield, Zap } from 'lucide-react';

export function AuthPage() {
  const [mode, setMode] = useState<'signin' | 'signup'>('signin');

  return (
    <div className="min-h-screen relative overflow-hidden flex items-center justify-center p-4">
      {/* Animated Gradient Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
        <div className="absolute inset-0 bg-gradient-to-tr from-blue-500/10 via-purple-500/10 to-pink-500/10 animate-gradient-shift"></div>
      </div>

      {/* Floating Particles */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-blue-400/20 rounded-full blur-3xl animate-float"></div>
        <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-purple-400/20 rounded-full blur-3xl animate-float-delayed"></div>
        <div className="absolute bottom-1/4 left-1/3 w-80 h-80 bg-pink-400/20 rounded-full blur-3xl animate-float-slow"></div>
      </div>

      {/* Decorative Elements */}
      <div className="absolute top-10 left-10 opacity-20 animate-pulse-slow">
        <Sparkles size={24} className="text-blue-500" />
      </div>
      <div className="absolute top-20 right-20 opacity-20 animate-pulse-slow" style={{ animationDelay: '1s' }}>
        <Shield size={28} className="text-purple-500" />
      </div>
      <div className="absolute bottom-20 left-20 opacity-20 animate-pulse-slow" style={{ animationDelay: '2s' }}>
        <Zap size={26} className="text-pink-500" />
      </div>

      {/* Main Content */}
      <div className="relative w-full max-w-md z-10 animate-fade-in">
        {/* Header */}
        <div className="text-center mb-8 animate-slide-in-down">
          <div className="relative inline-block mb-6">
            {/* Glow Effect */}
            <div className="absolute inset-0 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-3xl blur-2xl opacity-40 animate-pulse-slow"></div>
            
            {/* Icon Container */}
            <div className="relative w-20 h-20 bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 rounded-3xl flex items-center justify-center shadow-2xl shadow-purple-500/50 transform hover:scale-110 transition-transform duration-300">
              <Brain size={40} className="text-white animate-pulse-slow" />
            </div>
          </div>

          <h1 className="text-4xl font-bold mb-3 bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent animate-gradient-text">
            Agentic RAG Platform
          </h1>
          <p className="text-gray-600 font-medium text-lg">
            Secure, multi-tenant AI-powered document intelligence
          </p>
        </div>

        {/* Glass Morphism Card */}
        <div className="relative backdrop-blur-xl bg-white/80 rounded-3xl shadow-2xl border border-white/20 p-8 animate-scale-in">
          {/* Top Gradient Border */}
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-t-3xl"></div>

          {/* Tab Buttons */}
          <div className="flex gap-3 mb-8">
            <button
              onClick={() => setMode('signin')}
              className={`flex-1 py-3 px-6 rounded-xl font-semibold transition-all duration-300 relative overflow-hidden group ${
                mode === 'signin'
                  ? 'bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 text-white shadow-lg shadow-purple-500/30'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200 hover:shadow-md'
              }`}
            >
              {mode === 'signin' && (
                <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/20 to-white/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700"></div>
              )}
              <span className="relative">Sign In</span>
            </button>
            <button
              onClick={() => setMode('signup')}
              className={`flex-1 py-3 px-6 rounded-xl font-semibold transition-all duration-300 relative overflow-hidden group ${
                mode === 'signup'
                  ? 'bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 text-white shadow-lg shadow-purple-500/30'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200 hover:shadow-md'
              }`}
            >
              {mode === 'signup' && (
                <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/20 to-white/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700"></div>
              )}
              <span className="relative">Sign Up</span>
            </button>
          </div>

          {/* Form Content with Transition */}
          <div className="relative">
            <div
              key={mode}
              className="animate-fade-in"
            >
              {mode === 'signin' ? <SignInForm /> : <SignUpForm />}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center animate-fade-in" style={{ animationDelay: '300ms' }}>
          <div className="inline-flex items-center gap-2 px-6 py-3 bg-white/60 backdrop-blur-sm rounded-full border border-white/20 shadow-lg">
            <Shield size={16} className="text-purple-600" />
            <p className="text-sm font-medium text-gray-700">
              Enterprise-grade security with tenant isolation
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
