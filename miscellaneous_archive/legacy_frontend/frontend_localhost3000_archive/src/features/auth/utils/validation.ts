import { z } from 'zod';

/**
 * Validation Schemas for Authentication Forms
 * Using Zod for type-safe validation
 */

// Email validation
export const emailSchema = z
  .string()
  .min(1, 'Email is required')
  .email('Invalid email address')
  .toLowerCase()
  .trim();

// Password validation
export const passwordSchema = z
  .string()
  .min(8, 'Password must be at least 8 characters')
  .max(100, 'Password is too long')
  .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
  .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
  .regex(/[0-9]/, 'Password must contain at least one number')
  .regex(/[^a-zA-Z0-9]/, 'Password must contain at least one special character');

// Username validation
export const usernameSchema = z
  .string()
  .min(3, 'Username must be at least 3 characters')
  .max(20, 'Username must be at most 20 characters')
  .regex(/^[a-zA-Z0-9_-]+$/, 'Username can only contain letters, numbers, underscores, and hyphens')
  .trim();

// OTP validation
export const otpSchema = z
  .string()
  .length(6, 'OTP must be exactly 6 digits')
  .regex(/^[0-9]+$/, 'OTP must contain only numbers');

/**
 * Login Form Schema
 */
export const loginSchema = z.object({
  email: emailSchema,
  password: z.string().min(1, 'Password is required'),
  rememberMe: z.boolean().optional(),
});

export type LoginFormData = z.infer<typeof loginSchema>;

/**
 * Register Form Schema
 */
export const registerSchema = z
  .object({
    email: emailSchema,
    username: usernameSchema,
    password: passwordSchema,
    confirmPassword: z.string().min(1, 'Please confirm your password'),
    acceptTerms: z.boolean().refine((val) => val === true, {
      message: 'You must accept the terms and conditions',
    }),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords don't match",
    path: ['confirmPassword'],
  });

export type RegisterFormData = z.infer<typeof registerSchema>;

/**
 * OTP Verification Schema
 */
export const otpVerificationSchema = z.object({
  email: emailSchema,
  otp: otpSchema,
});

export type OTPVerificationFormData = z.infer<typeof otpVerificationSchema>;

/**
 * Forgot Password Schema
 */
export const forgotPasswordSchema = z.object({
  email: emailSchema,
});

export type ForgotPasswordFormData = z.infer<typeof forgotPasswordSchema>;

/**
 * Reset Password Schema
 */
export const resetPasswordSchema = z
  .object({
    password: passwordSchema,
    confirmPassword: z.string().min(1, 'Please confirm your password'),
    token: z.string().min(1, 'Reset token is required'),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords don't match",
    path: ['confirmPassword'],
  });

export type ResetPasswordFormData = z.infer<typeof resetPasswordSchema>;

/**
 * Change Password Schema
 */
export const changePasswordSchema = z
  .object({
    currentPassword: z.string().min(1, 'Current password is required'),
    newPassword: passwordSchema,
    confirmPassword: z.string().min(1, 'Please confirm your new password'),
  })
  .refine((data) => data.newPassword === data.confirmPassword, {
    message: "Passwords don't match",
    path: ['confirmPassword'],
  })
  .refine((data) => data.currentPassword !== data.newPassword, {
    message: 'New password must be different from current password',
    path: ['newPassword'],
  });

export type ChangePasswordFormData = z.infer<typeof changePasswordSchema>;

/**
 * Password Strength Calculator
 */
export function calculatePasswordStrength(password: string): {
  score: number;
  label: 'Weak' | 'Fair' | 'Good' | 'Strong';
  color: 'error' | 'warning' | 'info' | 'success';
} {
  let score = 0;

  if (password.length >= 8) score += 1;
  if (password.length >= 12) score += 1;
  if (/[a-z]/.test(password)) score += 1;
  if (/[A-Z]/.test(password)) score += 1;
  if (/[0-9]/.test(password)) score += 1;
  if (/[^a-zA-Z0-9]/.test(password)) score += 1;

  if (score <= 2) {
    return { score, label: 'Weak', color: 'error' };
  } else if (score <= 3) {
    return { score, label: 'Fair', color: 'warning' };
  } else if (score <= 4) {
    return { score, label: 'Good', color: 'info' };
  } else {
    return { score, label: 'Strong', color: 'success' };
  }
}
