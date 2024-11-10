// src/components/auth/LoginForm.tsx

import React, { useState } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../lib/auth/auth-context';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Alert,
  AlertDescription
} from '@/components/ui/alert';
import { Loader2 } from 'lucide-react';

interface LocationState {
  from?: Location;
  message?: string;
}

export const LoginForm: React.FC = () => {
  const { login, error: authError, clearError } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [isLoading, setIsLoading] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const state = location.state as LocationState;
  const from = state?.from?.pathname || '/';
  const message = state?.message;

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    clearError();
    setFormError(null);
    setIsLoading(true);
    
    const formData = new FormData(e.currentTarget);
    const username = formData.get('username') as string;
    const password = formData.get('password') as string;

    if (!username || !password) {
      setFormError('Username and password are required');
      setIsLoading(false);
      return;
    }

    try {
      await login(username, password);
      // Navigate to the page they were trying to visit or home
      navigate(from, { replace: true });
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex justify-center items-center min-h-screen bg-gray-50">
      <Card className="w-full max-w-md mx-4 shadow-lg">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl text-center">Sign in</CardTitle>
          <CardDescription className="text-center">
            Enter your credentials to access your account
          </CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            {message && (
              <Alert className="bg-green-50 text-green-700 border-green-200">
                <AlertDescription>{message}</AlertDescription>
              </Alert>
            )}
            <div className="space-y-2">
              <label className="text-sm font-medium" htmlFor="username">
                Username
              </label>
              <Input
                id="username"
                name="username"
                type="text"
                required
                placeholder="Enter your username"
                disabled={isLoading}
                className="w-full"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium" htmlFor="password">
                Password
              </label>
              <Input
                id="password"
                name="password"
                type="password"
                required
                placeholder="Enter your password"
                disabled={isLoading}
                className="w-full"
              />
            </div>
            {(authError || formError) && (
              <Alert variant="destructive">
                <AlertDescription>
                  {authError || formError}
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
          <CardFooter className="flex flex-col space-y-4">
            <Button 
              type="submit" 
              className="w-full"
              disabled={isLoading}
            >
              {isLoading ? (
                <span className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Signing in...
                </span>
              ) : (
                'Sign in'
              )}
            </Button>
            <p className="text-sm text-center text-gray-600">
              Don't have an account?{' '}
              <Link 
                to="/signup" 
                className="text-primary hover:underline font-medium"
                tabIndex={0}
              >
                Sign up
              </Link>
            </p>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
};