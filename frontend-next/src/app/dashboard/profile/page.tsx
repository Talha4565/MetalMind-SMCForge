'use client';

import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import DashboardLayout from '@/components/Common/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
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
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
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
    .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
    .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
    .regex(/[0-9]/, 'Password must contain at least one number')
    .regex(/[!@#$%^&*(),.?":{}|<>]/, 'Password must contain at least one special character'),
  confirmPassword: z.string(),
}).refine((data) => data.newPassword === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
});

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
      try {
        const data = await apiClient.getProfile();
        setProfile(data.profile);
      } catch {
        toast.error('Failed to load profile. Please refresh.');
      } finally {
        setIsLoading(false);
      }
    };
    fetchProfile();
  }, [status]);

  const profileForm = useForm<ProfileValues>({
    resolver: zodResolver(profileSchema),
    values: {
      name: profile?.name || '',
      email: profile?.email || '',
    },
  });

  const passwordForm = useForm<PasswordValues>({
    resolver: zodResolver(passwordSchema),
    defaultValues: {
      currentPassword: '',
      newPassword: '',
      confirmPassword: '',
    },
  });

  const onProfileSubmit = async (data: ProfileValues) => {
    setIsSaving(true);
    try {
      const result = await apiClient.updateProfile({ name: data.name, email: data.email });
      setProfile(result.profile);
      toast.success('Profile updated successfully!');
    } catch (error: unknown) {
      const err = error as { error?: string; message?: string };
      toast.error(err?.error || err?.message || 'An error occurred');
    } finally {
      setIsSaving(false);
    }
  };

  const onPasswordSubmit = async (data: PasswordValues) => {
    setIsSaving(true);
    try {
      await apiClient.changePassword({
        current_password: data.currentPassword,
        new_password: data.newPassword
      });
      toast.success('Password changed successfully!');
      passwordForm.reset();
      setIsEditingPassword(false);
    } catch (error: unknown) {
      const err = error as { error?: string; message?: string };
      toast.error(err?.error || err?.message || 'Failed to change password');
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-96">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-black tracking-tight text-card-foreground flex items-center gap-3">
            <User className="w-8 h-8 text-blue-500" />
            Account Settings
          </h1>
          <p className="text-slate-500 mt-1">Manage your profile and account preferences.</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <Card className="lg:col-span-2 bg-card border-border">
            <CardHeader>
              <CardTitle className="text-lg font-bold text-card-foreground">Profile Information</CardTitle>
              <CardDescription>Update your account details</CardDescription>
            </CardHeader>
            <CardContent>
              <Form {...profileForm}>
                <form onSubmit={profileForm.handleSubmit(onProfileSubmit)} className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <FormField
                      control={profileForm.control}
                      name="name"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className="text-slate-300 font-bold uppercase tracking-widest text-[10px]">Full Name</FormLabel>
                          <FormControl>
                            <Input {...field} className="bg-input/30 border-border text-foreground focus:border-ring" />
                          </FormControl>
                          <FormMessage className="text-xs text-red-500" />
                        </FormItem>
                      )}
                    />
                    <FormField
                      control={profileForm.control}
                      name="email"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className="text-slate-300 font-bold uppercase tracking-widest text-[10px]">Email Address</FormLabel>
                          <FormControl>
                            <Input type="email" {...field} className="bg-input/30 border-border text-foreground focus:border-ring" />
                          </FormControl>
                          <FormMessage className="text-xs text-red-500" />
                        </FormItem>
                      )}
                    />
                  </div>
                  <Button type="submit" disabled={isSaving} className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-6 rounded-lg">
                    {isSaving ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Saving...</> : <><Save className="w-4 h-4 mr-2" />Save Changes</>}
                  </Button>
                </form>
              </Form>
            </CardContent>
          </Card>

          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="text-lg font-bold text-card-foreground flex items-center gap-2">
                <Shield className="w-5 h-5 text-green-500" /> Account Status
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-1">Status</p>
                <p className="flex items-center gap-2 text-sm font-bold text-card-foreground">
                  <span className={`w-2 h-2 rounded-full ${profile?.is_active ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
                  {profile?.is_active ? 'Active' : 'Inactive'}
                  {profile?.is_verified ? ' & Verified' : ' — Unverified'}
                </p>
              </div>
              <div className="pt-4 border-t border-border">
                <p className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-1">Member Since</p>
                <p className="text-sm text-slate-300">
                  {profile?.created_at
                    ? new Date(profile.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
                    : 'Unknown'}
                </p>
              </div>
              <div className="pt-4 border-t border-border">
                <p className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-1">Plan Type</p>
                <p className="text-sm font-bold text-card-foreground">Free Tier</p>
              </div>
            </CardContent>
          </Card>
        </div>

        <Card className="bg-card border-border">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-lg font-bold text-card-foreground">Security</CardTitle>
              <CardDescription>Change your password and manage security settings</CardDescription>
            </div>
            {!isEditingPassword && (
              <Button variant="outline" className="border-border hover:bg-accent" onClick={() => setIsEditingPassword(true)}>
                Change Password
              </Button>
            )}
          </CardHeader>

          {isEditingPassword && (
            <CardContent>
              <Form {...passwordForm}>
                <form onSubmit={passwordForm.handleSubmit(onPasswordSubmit)} className="space-y-6 max-w-xl">
                  <FormField control={passwordForm.control} name="currentPassword" render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-slate-300 font-bold uppercase tracking-widest text-[10px]">Current Password</FormLabel>
                      <FormControl>
                        <Input type={showPasswords ? 'text' : 'password'} {...field} className="bg-input/30 border-border text-foreground focus:border-ring pr-10" />
                      </FormControl>
                      <FormMessage className="text-xs text-red-500" />
                    </FormItem>
                  )} />
                  <FormField control={passwordForm.control} name="newPassword" render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-slate-300 font-bold uppercase tracking-widest text-[10px]">New Password</FormLabel>
                      <FormControl>
                        <Input type={showPasswords ? 'text' : 'password'} {...field} className="bg-input/30 border-border text-foreground focus:border-ring" />
                      </FormControl>
                      <FormMessage className="text-xs text-red-500" />
                    </FormItem>
                  )} />
                  <FormField control={passwordForm.control} name="confirmPassword" render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-slate-300 font-bold uppercase tracking-widest text-[10px]">Confirm Password</FormLabel>
                      <FormControl>
                        <Input type={showPasswords ? 'text' : 'password'} {...field} className="bg-input/30 border-border text-foreground focus:border-ring" />
                      </FormControl>
                      <FormMessage className="text-xs text-red-500" />
                    </FormItem>
                  )} />
                  <div className="flex items-center gap-4">
                    <Button type="button" variant="outline" className="border-border hover:bg-accent" onClick={() => setShowPasswords(!showPasswords)}>
                      {showPasswords ? <><EyeOff className="w-4 h-4 mr-2" />Hide Passwords</> : <><Eye className="w-4 h-4 mr-2" />Show Passwords</>}
                    </Button>
                  </div>
                  <div className="flex gap-3 pt-4">
                    <Button type="submit" disabled={isSaving} className="bg-blue-600 hover:bg-blue-700 text-white font-bold">
                      {isSaving ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Updating...</> : <><Save className="w-4 h-4 mr-2" />Update Password</>}
                    </Button>
                    <Button type="button" variant="outline" className="border-border hover:bg-accent" onClick={() => { setIsEditingPassword(false); passwordForm.reset(); }}>
                      Cancel
                    </Button>
                  </div>
                </form>
              </Form>
            </CardContent>
          )}
        </Card>
      </div>
    </DashboardLayout>
  );
}
