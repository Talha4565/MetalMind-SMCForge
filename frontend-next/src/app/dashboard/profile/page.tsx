'use client';

import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import DashboardLayout from '@/components/Common/DashboardLayout';
import TerminalCard, { TerminalButton } from '@/components/Common/TerminalCard';
import { Input } from '@/components/ui/input';
import {
  Form, FormControl, FormField, FormItem, FormLabel, FormMessage
} from '@/components/ui/form';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { cn } from '@/lib/utils';
import { User, Shield, Eye, EyeOff, Save, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { apiClient } from '@/lib/api-client';
import { Profile } from '@/lib/api-types';

const profileSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  email: z.string().email('Invalid email address'),
});

const passwordSchema = z.object({
  currentPassword: z.string().min(8, 'Password must be at least 8 characters'),
  newPassword: z.string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[A-Z]/, 'Must contain an uppercase letter')
    .regex(/[a-z]/, 'Must contain a lowercase letter')
    .regex(/[0-9]/, 'Must contain a number')
    .regex(/[!@#$%^&*(),.?":{}|<>]/, 'Must contain a special character'),
  confirmPassword: z.string(),
}).refine((data) => data.newPassword === data.confirmPassword, { message: "Passwords don't match", path: ["confirmPassword"] });

type ProfileValues = z.infer<typeof profileSchema>;
type PasswordValues = z.infer<typeof passwordSchema>;

export default function ProfilePage() {
  const { status } = useSession();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isEditingPassword, setIsEditingPassword] = useState(false);
  const [showPasswords, setShowPasswords] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (status !== 'authenticated') return;
    const fetchProfile = async () => {
      try { const data = await apiClient.getProfile(); setProfile(data.profile); } catch { toast.error('Failed to load profile'); } finally { setIsLoading(false); }
    };
    fetchProfile();
  }, [status]);

  const profileForm = useForm<ProfileValues>({ resolver: zodResolver(profileSchema), values: { name: profile?.name || '', email: profile?.email || '' } });
  const passwordForm = useForm<PasswordValues>({ resolver: zodResolver(passwordSchema), defaultValues: { currentPassword: '', newPassword: '', confirmPassword: '' } });

  const onProfileSubmit = async (data: ProfileValues) => {
    setIsSaving(true);
    try { const result = await apiClient.updateProfile({ name: data.name, email: data.email }); setProfile(result.profile); toast.success('Profile updated!'); }
    catch (error: unknown) { const err = error as { error?: string; message?: string }; toast.error(err?.error || err?.message || 'An error occurred'); }
    finally { setIsSaving(false); }
  };

  const onPasswordSubmit = async (data: PasswordValues) => {
    setIsSaving(true);
    try { await apiClient.changePassword({ current_password: data.currentPassword, new_password: data.newPassword }); toast.success('Password changed!'); passwordForm.reset(); setIsEditingPassword(false); }
    catch (error: unknown) { const err = error as { error?: string; message?: string }; toast.error(err?.error || err?.message || 'Failed to change password'); }
    finally { setIsSaving(false); }
  };

  if (isLoading) {
    return <DashboardLayout><div className="flex items-center justify-center min-h-96"><Loader2 className="w-8 h-8 animate-spin text-terminal-hold" /></div></DashboardLayout>;
  }

  return (
    <DashboardLayout>
      <div className="space-y-6 p-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-terminal-value font-mono flex items-center gap-3">
            <User className="w-7 h-7 text-terminal-hold" />ACCOUNT SETTINGS
          </h1>
          <p className="text-terminal-label text-xs mt-1 font-mono tracking-wider">Profile · security · preferences</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Profile form */}
          <TerminalCard title="PROFILE INFORMATION" code="PRF" className="lg:col-span-2">
            <Form {...profileForm}>
              <form onSubmit={profileForm.handleSubmit(onProfileSubmit)} className="space-y-5">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  <FormField control={profileForm.control} name="name" render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-[9px] font-mono font-bold uppercase tracking-widest text-terminal-label">Full Name</FormLabel>
                      <FormControl><Input {...field} className="bg-terminal-panel border-terminal-rule text-terminal-value font-mono text-xs rounded-none focus:border-terminal-hold" /></FormControl>
                      <FormMessage className="text-[9px] font-mono text-terminal-sell" />
                    </FormItem>
                  )} />
                  <FormField control={profileForm.control} name="email" render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-[9px] font-mono font-bold uppercase tracking-widest text-terminal-label">Email Address</FormLabel>
                      <FormControl><Input type="email" {...field} className="bg-terminal-panel border-terminal-rule text-terminal-value font-mono text-xs rounded-none focus:border-terminal-hold" /></FormControl>
                      <FormMessage className="text-[9px] font-mono text-terminal-sell" />
                    </FormItem>
                  )} />
                </div>
                <TerminalButton type="submit" disabled={isSaving} isLoading={isSaving}>
                  <Save className="w-3.5 h-3.5" /> SAVE CHANGES
                </TerminalButton>
              </form>
            </Form>
          </TerminalCard>

          {/* Account status */}
          <TerminalCard title="ACCOUNT STATUS" code="STS">
            <div className="space-y-3">
              <div>
                <p className="text-[9px] font-mono font-bold uppercase tracking-widest text-terminal-label mb-1">Status</p>
                <p className="flex items-center gap-2 text-xs font-mono font-bold text-terminal-value">
                  <span className={cn('w-2 h-2 rounded-full', profile?.is_active ? 'bg-terminal-buy animate-pulse' : 'bg-terminal-sell')} />
                  {profile?.is_active ? 'Active' : 'Inactive'}
                  {profile?.is_verified ? ' & Verified' : ' — Unverified'}
                </p>
              </div>
              <div className="pt-3 border-t border-terminal-rule">
                <p className="text-[9px] font-mono font-bold uppercase tracking-widest text-terminal-label mb-1">Member Since</p>
                <p className="text-xs font-mono text-terminal-value">{profile?.created_at ? new Date(profile.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' }) : 'Unknown'}</p>
              </div>
              <div className="pt-3 border-t border-terminal-rule">
                <p className="text-[9px] font-mono font-bold uppercase tracking-widest text-terminal-label mb-1">Plan</p>
                <p className="text-xs font-mono font-bold text-terminal-value">Free Tier</p>
              </div>
            </div>
          </TerminalCard>
        </div>

        {/* Security */}
        <TerminalCard title="SECURITY" code="SEC" right={!isEditingPassword ? (
          <TerminalButton variant="secondary" size="sm" onClick={() => setIsEditingPassword(true)}>CHANGE PASSWORD</TerminalButton>
        ) : undefined}>
          {isEditingPassword ? (
            <Form {...passwordForm}>
              <form onSubmit={passwordForm.handleSubmit(onPasswordSubmit)} className="space-y-5 max-w-xl">
                <FormField control={passwordForm.control} name="currentPassword" render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-[9px] font-mono font-bold uppercase tracking-widest text-terminal-label">Current Password</FormLabel>
                    <FormControl><Input type={showPasswords ? 'text' : 'password'} {...field} className="bg-terminal-panel border-terminal-rule text-terminal-value font-mono text-xs rounded-none focus:border-terminal-hold" /></FormControl>
                    <FormMessage className="text-[9px] font-mono text-terminal-sell" />
                  </FormItem>
                )} />
                <FormField control={passwordForm.control} name="newPassword" render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-[9px] font-mono font-bold uppercase tracking-widest text-terminal-label">New Password</FormLabel>
                    <FormControl><Input type={showPasswords ? 'text' : 'password'} {...field} className="bg-terminal-panel border-terminal-rule text-terminal-value font-mono text-xs rounded-none focus:border-terminal-hold" /></FormControl>
                    <FormMessage className="text-[9px] font-mono text-terminal-sell" />
                  </FormItem>
                )} />
                <FormField control={passwordForm.control} name="confirmPassword" render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-[9px] font-mono font-bold uppercase tracking-widest text-terminal-label">Confirm Password</FormLabel>
                    <FormControl><Input type={showPasswords ? 'text' : 'password'} {...field} className="bg-terminal-panel border-terminal-rule text-terminal-value font-mono text-xs rounded-none focus:border-terminal-hold" /></FormControl>
                    <FormMessage className="text-[9px] font-mono text-terminal-sell" />
                  </FormItem>
                )} />
                <div className="flex items-center gap-4">
                  <TerminalButton type="button" variant="secondary" size="sm" onClick={() => setShowPasswords(!showPasswords)}>
                    {showPasswords ? <><EyeOff className="w-3 h-3" /> HIDE</> : <><Eye className="w-3 h-3" /> SHOW</>}
                  </TerminalButton>
                </div>
                <div className="flex gap-3 pt-4">
                  <TerminalButton type="submit" disabled={isSaving} isLoading={isSaving}><Save className="w-3.5 h-3.5" /> UPDATE PASSWORD</TerminalButton>
                  <TerminalButton type="button" variant="secondary" onClick={() => { setIsEditingPassword(false); passwordForm.reset(); }}>CANCEL</TerminalButton>
                </div>
              </form>
            </Form>
          ) : (
            <p className="font-mono text-xs text-terminal-label">Password management and security settings.</p>
          )}
        </TerminalCard>
      </div>
    </DashboardLayout>
  );
}
