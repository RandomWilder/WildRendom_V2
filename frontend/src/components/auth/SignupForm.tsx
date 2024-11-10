// src/components/auth/SignUpForm.tsx

import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { API_ENDPOINTS } from '../../lib/config/api';
import { validatePassword } from '../../lib/auth/auth-utils';
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

interface SignUpFormProps {}

const SignupForm: React.FC<SignUpFormProps> = () => {
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [password, setPassword] = useState('');

  useEffect(() => {
    if (password) {
      const errors = validatePassword(password);
      setValidationErrors(errors);
    } else {
      setValidationErrors([]);
    }
  }, [password]);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    
    if (validationErrors.length > 0) {
      setError('Please fix password validation errors');
      return;
    }

    setIsLoading(true);
    const formData = new FormData(e.currentTarget);
    const data = {
      username: formData.get('username'),
      email: formData.get('email'),
      password: formData.get('password'),
    };

    try {
      const response = await fetch(API_ENDPOINTS.AUTH.REGISTER, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || 'Registration failed');
      }

      // Redirect to login with success message
      navigate('/login', { 
        state: { message: 'Registration successful! Please log in.' }
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex justify-center items-center min-h-screen bg-gray-50">
      <Card className="w-full max-w-md mx-4 shadow-lg">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl text-center">Create an account</CardTitle>
          <CardDescription className="text-center">
            Enter your details to sign up
          </CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium" htmlFor="username">
                Username
              </label>
              <Input
                id="username"
                name="username"
                type="text"
                required
                placeholder="Choose a username"
                className="w-full"
                disabled={isLoading}
                minLength={3}
                maxLength={64}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium" htmlFor="email">
                Email
              </label>
              <Input
                id="email"
                name="email"
                type="email"
                required
                placeholder="Enter your email"
                className="w-full"
                disabled={isLoading}
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
                placeholder="Create a password"
                className="w-full"
                disabled={isLoading}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                minLength={8}
              />
              {validationErrors.length > 0 && (
                <ul className="text-sm text-red-500 space-y-1 mt-2">
                  {validationErrors.map((error, index) => (
                    <li key={index}>{error}</li>
                  ))}
                </ul>
              )}
            </div>
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
          </CardContent>
          <CardFooter className="flex flex-col space-y-4">
            <Button 
              type="submit" 
              className="w-full"
              disabled={isLoading || validationErrors.length > 0}
            >
              {isLoading ? (
                <span className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Creating account...
                </span>
              ) : (
                'Sign up'
              )}
            </Button>
            <p className="text-sm text-center text-gray-600">
              Already have an account?{' '}
              <Link 
                to="/login" 
                className="text-primary hover:underline font-medium"
                tabIndex={0}
              >
                Sign in
              </Link>
            </p>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
};
export default SignupForm;