'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { 
  Form, 
  FormControl, 
  FormField, 
  FormItem, 
  FormLabel, 
  FormMessage 
} from '@/components/ui/form';
import { Loader2, Eye, EyeOff } from 'lucide-react';
import { useState } from 'react';

const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
    .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
    .regex(/[0-9]/, 'Password must contain at least one number')
    .regex(/[!@#$%^&*(),.?":{}|<>]/, 'Password must contain at least one special character'),
  totp_code: z.string().optional(),
});

type LoginValues = z.infer<typeof loginSchema>;

interface LoginFormProps {
  onSubmit: (data: LoginValues) => void;
  isLoading?: boolean;
  showOtp?: boolean;
}

export function LoginForm({ onSubmit, isLoading, showOtp = false }: LoginFormProps) {
  const [showPassword, setShowPassword] = useState(false);
  const form = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
    },
  });

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-5">
        <FormField
          control={form.control}
          name="email"
          render={({ field }) => (
            <FormItem>
              <FormLabel className="text-slate-400 text-xs font-medium">
                Email
              </FormLabel>
              <FormControl>
                <Input 
                  placeholder="name@example.com" 
                  {...field}
                  autoComplete="email"
                  className="h-11 bg-input/30 border-border text-foreground placeholder:text-muted-foreground focus:border-ring focus:ring-ring/20 transition-all"
                />
              </FormControl>
              <FormMessage className="text-xs" />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="password"
          render={({ field }) => (
            <FormItem>
              <FormLabel className="text-slate-400 text-xs font-medium">
                Password
              </FormLabel>
              <div className="relative">
                <FormControl>
                  <Input 
                    type={showPassword ? 'text' : 'password'}
                    {...field}
                    autoComplete="current-password"
                    className="h-11 bg-input/30 border-border text-foreground placeholder:text-muted-foreground focus:border-ring focus:ring-ring/20 transition-all pr-10"
                  />
                </FormControl>
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              <FormMessage className="text-xs" />
            </FormItem>
          )}
        />

        {showOtp && (
          <FormField
            control={form.control}
            name="totp_code"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-slate-400 text-xs font-medium">
                  2FA Code
                </FormLabel>
                <FormControl>
                  <Input
                    type="text"
                    {...field}
                    autoComplete="one-time-code"
                    placeholder="Enter 6-digit code"
                    className="h-11 bg-input/30 border-border text-foreground placeholder:text-muted-foreground focus:border-ring focus:ring-ring/20 transition-all"
                  />
                </FormControl>
                <FormMessage className="text-xs" />
              </FormItem>
            )}
          />
        )}

        <Button
          type="submit"
          className="w-full h-11 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-lg transition-all shadow-lg shadow-emerald-600/20"
          disabled={isLoading}
        >
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Signing in...
            </>
          ) : (
            showOtp ? 'Continue with 2FA' : 'Sign in'
          )}
        </Button>
      </form>
    </Form>
  );
}
