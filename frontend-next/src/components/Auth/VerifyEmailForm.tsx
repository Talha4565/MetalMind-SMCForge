'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { 
  Form, 
  FormControl, 
  FormField, 
  FormItem, 
  FormLabel, 
  FormMessage 
} from '@/components/ui/form';
import { Mail, Loader2, RotateCw } from 'lucide-react';
import Link from 'next/link';
import { useState } from 'react';

const verifyEmailSchema = z.object({
  email: z.string().email('Invalid email address'),
  otp_code: z.string().min(6, 'OTP code must be 6 digits').max(6, 'OTP code must be 6 digits').regex(/^\d+$/, 'OTP code must contain only numbers'),
});

type VerifyEmailValues = z.infer<typeof verifyEmailSchema>;

interface VerifyEmailFormProps {
  onSubmit: (data: VerifyEmailValues) => void;
  onResendOTP: (email: string) => void;
  email?: string;
  isLoading?: boolean;
}

export function VerifyEmailForm({ onSubmit, onResendOTP, email, isLoading }: VerifyEmailFormProps) {
  const [resendLoading, setResendLoading] = useState(false);
  const form = useForm<VerifyEmailValues>({
    resolver: zodResolver(verifyEmailSchema),
    defaultValues: {
      email: email || '',
      otp_code: '',
    },
  });

  const emailValue = form.watch('email');

  const handleResend = async () => {
    if (!emailValue) {
      return;
    }

    setResendLoading(true);
    try {
      await onResendOTP(emailValue);
    } finally {
      setResendLoading(false);
    }
  };

  return (
    <Card className="w-full max-w-md bg-card border-border shadow-2xl">
      <CardHeader className="space-y-4 flex flex-col items-center text-center">
        <div className="p-3 rounded-2xl bg-emerald-600 shadow-lg shadow-emerald-600/20">
          <Mail className="w-8 h-8 text-white" />
        </div>
        <div className="space-y-1">
          <CardTitle className="text-2xl font-black tracking-tight text-white">Verify Your Email</CardTitle>
          <CardDescription className="text-slate-500">
            Enter the verification code sent to {email || 'your email'}
          </CardDescription>
        </div>
      </CardHeader>
      
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)}>
          <CardContent className="space-y-4">
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem className="space-y-2">
                  <FormLabel className="text-slate-300 font-bold uppercase tracking-widest text-[10px]">
                    Email Address
                  </FormLabel>
                  <FormControl>
                    <Input 
                      placeholder="name@example.com" 
                      {...field}
                      disabled={Boolean(email)}
                      className="bg-input/30 border-border text-foreground focus:border-ring transition-all"
                    />
                  </FormControl>
                  <FormMessage className="text-xs text-red-500 font-medium" />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="otp_code"
              render={({ field }) => (
                <FormItem className="space-y-2">
                  <FormLabel className="text-slate-300 font-bold uppercase tracking-widest text-[10px]">
                    Verification Code
                  </FormLabel>
                  <FormControl>
                    <Input 
                      placeholder="000000" 
                      {...field}
                      maxLength={6}
                      inputMode="numeric"
                      className="bg-input/30 border-border text-foreground focus:border-ring transition-all text-center text-2xl tracking-widest font-bold"
                    />
                  </FormControl>
                  <FormMessage className="text-xs text-red-500 font-medium" />
                  <p className="text-xs text-slate-400 mt-2">Check your email for the 6-digit code (expires in 10 minutes)</p>
                </FormItem>
              )}
            />
          </CardContent>

          <CardFooter className="flex flex-col space-y-3">
            <Button 
              type="submit" 
              className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-6 rounded-xl transition-all shadow-lg shadow-emerald-600/20"
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Verifying...
                </>
              ) : (
                'Verify Email'
              )}
            </Button>

            <Button
              type="button"
              variant="outline"
              className="w-full border-slate-700 text-slate-300 hover:bg-slate-800 font-semibold"
              onClick={handleResend}
              disabled={resendLoading || isLoading}
            >
              {resendLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Sending...
                </>
              ) : (
                <>
                  <RotateCw className="mr-2 h-4 w-4" />
                  Resend Code
                </>
              )}
            </Button>

            <p className="text-xs text-slate-500 text-center">
              Back to{' '}
              <Link href="/auth/login" className="text-emerald-400 hover:text-emerald-300 font-bold underline underline-offset-4">
                Sign In
              </Link>
            </p>
          </CardFooter>
        </form>
      </Form>
    </Card>
  );
}
