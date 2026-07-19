'use client';

import { useState, useEffect, useRef } from 'react';
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
import { User, Shield, Eye, EyeOff, Save, Loader2, Trash2, Upload, QrCode, Key, Settings2, AlertTriangle } from 'lucide-react';
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

const deleteSchema = z.object({
  password: z.string().min(1, 'Password is required to confirm'),
});

type ProfileValues = z.infer<typeof profileSchema>;
type PasswordValues = z.infer<typeof passwordSchema>;
type DeleteValues = z.infer<typeof deleteSchema>;

interface UserSettings {
  theme?: string;
  notifications_enabled?: boolean;
  email_notifications?: boolean;
  default_timeframe?: string;
  default_asset?: string;
}

export default function ProfilePage() {
  const { status } = useSession();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isEditingPassword, setIsEditingPassword] = useState(false);
  const [isEditingDelete, setIsEditingDelete] = useState(false);
  const [showPasswords, setShowPasswords] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // 2FA state
  const [twoFaSetup, setTwoFaSetup] = useState<{ secret: string; provisioning_uri: string; qr: string } | null>(null);
  const [twoFaOtp, setTwoFaOtp] = useState('');
  const [twoFaLoading, setTwoFaLoading] = useState(false);

  // Avatar state
  const [avatarUploading, setAvatarUploading] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  // Settings state
  const [settingsDirty, setSettingsDirty] = useState(false);
  const [settingsSaving, setSettingsSaving] = useState(false);

  useEffect(() => {
    if (status !== 'authenticated') return;
    const fetchAll = async () => {
      try {
        const [profileData, settingsData] = await Promise.all([
          apiClient.getProfile(),
          apiClient.getSettings().catch(() => ({ settings: {} as UserSettings })),
        ]);
        setProfile(profileData.profile);
        setSettings(settingsData.settings);
      } catch {
        toast.error('Failed to load profile');
      } finally {
        setIsLoading(false);
      }
    };
    fetchAll();
  }, [status]);

  const profileForm = useForm<ProfileValues>({ resolver: zodResolver(profileSchema), values: { name: profile?.name || '', email: profile?.email || '' } });
  const passwordForm = useForm<PasswordValues>({ resolver: zodResolver(passwordSchema), defaultValues: { currentPassword: '', newPassword: '', confirmPassword: '' } });
  const deleteForm = useForm<DeleteValues>({ resolver: zodResolver(deleteSchema), defaultValues: { password: '' } });

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

  // ── 2FA handlers ──
  const handleSetup2fa = async () => {
    setTwoFaLoading(true);
    try { const data = await apiClient.get2faSetup(); setTwoFaSetup(data); }
    catch { toast.error('Failed to load 2FA setup'); }
    finally { setTwoFaLoading(false); }
  };

  const handleEnable2fa = async () => {
    if (!twoFaOtp) { toast.error('Enter the 6-digit code'); return; }
    setTwoFaLoading(true);
    try { await apiClient.enable2fa(twoFaOtp); setProfile(prev => prev ? { ...prev, totp_enabled: true } : null); setTwoFaSetup(null); setTwoFaOtp(''); toast.success('2FA enabled!'); }
    catch (error: unknown) { const err = error as { error?: string }; toast.error(err?.error || 'Invalid code'); }
    finally { setTwoFaLoading(false); }
  };

  const handleDisable2fa = async () => {
    if (!twoFaOtp) { toast.error('Enter the 6-digit code'); return; }
    setTwoFaLoading(true);
    try { await apiClient.disable2fa(twoFaOtp); setProfile(prev => prev ? { ...prev, totp_enabled: false } : null); setTwoFaOtp(''); toast.success('2FA disabled'); }
    catch (error: unknown) { const err = error as { error?: string }; toast.error(err?.error || 'Invalid code'); }
    finally { setTwoFaLoading(false); }
  };

  // ── Avatar handler ──
  const handleAvatarUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setAvatarUploading(true);
    try { const result = await apiClient.uploadAvatar(file); setProfile(result.profile); toast.success('Avatar uploaded!'); }
    catch { toast.error('Failed to upload avatar'); }
    finally { setAvatarUploading(false); }
  };

  // ── Settings handlers ──
  const handleSettingsChange = (key: string, value: unknown) => {
    setSettings(prev => prev ? { ...prev, [key]: value } : null);
    setSettingsDirty(true);
  };

  const handleSaveSettings = async () => {
    if (!settings) return;
    setSettingsSaving(true);
    try { const result = await apiClient.updateSettings(settings as Record<string, unknown>); setSettings(result.settings as UserSettings); setSettingsDirty(false); toast.success('Settings saved!'); }
    catch { toast.error('Failed to save settings'); }
    finally { setSettingsSaving(false); }
  };

  // ── Delete account handler ──
  const onDeleteSubmit = async (data: DeleteValues) => {
    setIsSaving(true);
    try { await apiClient.deleteAccount(data.password); toast.success('Account deleted'); window.location.href = '/auth/login'; }
    catch (error: unknown) { const err = error as { error?: string }; toast.error(err?.error || 'Failed to delete account'); }
    finally { setIsSaving(false); setIsEditingDelete(false); }
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
          <p className="text-terminal-label text-xs mt-1 font-mono tracking-wider">Profile · security · preferences · 2FA</p>
        </div>

        {/* Row 1: Profile + Status */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
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
                <p className="text-[9px] font-mono font-bold uppercase tracking-widest text-terminal-label mb-1">2FA</p>
                <p className={cn('text-xs font-mono font-bold', profile?.totp_enabled ? 'text-terminal-buy' : 'text-terminal-label')}>
                  {profile?.totp_enabled ? 'Enabled' : 'Not enabled'}
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
              {profile?.settings?.avatar_url && (
                <div className="pt-3 border-t border-terminal-rule">
                  <p className="text-[9px] font-mono font-bold uppercase tracking-widest text-terminal-label mb-2">Avatar</p>
                  <img src={profile.settings.avatar_url} alt="Avatar" className="w-16 h-16 rounded border border-terminal-rule object-cover" />
                </div>
              )}
            </div>
          </TerminalCard>
        </div>

        {/* Row 2: Settings */}
        <TerminalCard title="PREFERENCES" code="SET" right={
          <TerminalButton variant="primary" size="sm" onClick={handleSaveSettings} disabled={!settingsDirty} isLoading={settingsSaving}>
            <Save className="w-3 h-3" /> SAVE
          </TerminalButton>
        }>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
            <div className="space-y-1.5">
              <p className="text-[9px] font-mono font-bold uppercase tracking-widest text-terminal-label">Theme</p>
              <select
                value={settings?.theme || 'dark'}
                onChange={e => handleSettingsChange('theme', e.target.value)}
                className="w-full bg-terminal-panel border border-terminal-rule text-terminal-value font-mono text-xs rounded-none px-3 py-2 focus:border-terminal-hold"
              >
                <option value="dark">Dark</option>
                <option value="light">Light</option>
              </select>
            </div>
            <div className="space-y-1.5">
              <p className="text-[9px] font-mono font-bold uppercase tracking-widest text-terminal-label">Default Asset</p>
              <select
                value={settings?.default_asset || 'gold'}
                onChange={e => handleSettingsChange('default_asset', e.target.value)}
                className="w-full bg-terminal-panel border border-terminal-rule text-terminal-value font-mono text-xs rounded-none px-3 py-2 focus:border-terminal-hold"
              >
                <option value="gold">XAU/USD (Gold)</option>
                <option value="silver">XAG/USD (Silver)</option>
              </select>
            </div>
            <div className="space-y-1.5">
              <p className="text-[9px] font-mono font-bold uppercase tracking-widest text-terminal-label">Default Timeframe</p>
              <select
                value={settings?.default_timeframe || '15m'}
                onChange={e => handleSettingsChange('default_timeframe', e.target.value)}
                className="w-full bg-terminal-panel border border-terminal-rule text-terminal-value font-mono text-xs rounded-none px-3 py-2 focus:border-terminal-hold"
              >
                <option value="5m">5m</option>
                <option value="15m">15m</option>
                <option value="30m">30m</option>
                <option value="1h">1h</option>
              </select>
            </div>
            <div className="space-y-2">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={!!settings?.notifications_enabled}
                  onChange={e => handleSettingsChange('notifications_enabled', e.target.checked)}
                  className="accent-terminal-hold"
                />
                <span className="text-[10px] font-mono font-bold text-terminal-value">Push Notifications</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={!!settings?.email_notifications}
                  onChange={e => handleSettingsChange('email_notifications', e.target.checked)}
                  className="accent-terminal-hold"
                />
                <span className="text-[10px] font-mono font-bold text-terminal-value">Email Notifications</span>
              </label>
            </div>
          </div>
        </TerminalCard>

        {/* Row 3: 2FA + Avatar */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 2FA */}
          <TerminalCard title="TWO-FACTOR AUTH" code="2FA" right={
            profile?.totp_enabled ? (
              <span className="text-[9px] font-mono font-bold text-terminal-buy tracking-widest">ACTIVE</span>
            ) : (
              <span className="text-[9px] font-mono font-bold text-terminal-label tracking-widest">INACTIVE</span>
            )
          }>
            <div className="space-y-4">
              {!twoFaSetup && !profile?.totp_enabled && (
                <div>
                  <p className="text-xs font-mono text-terminal-label mb-3">Add an extra layer of security with TOTP-based two-factor authentication.</p>
                  <TerminalButton variant="secondary" size="sm" onClick={handleSetup2fa} isLoading={twoFaLoading}>
                    <QrCode className="w-3.5 h-3.5" /> SETUP 2FA
                  </TerminalButton>
                </div>
              )}

              {twoFaSetup && !profile?.totp_enabled && (
                <div className="space-y-4">
                  <p className="text-[10px] font-mono text-terminal-label">Scan this QR code with Google Authenticator or any TOTP app:</p>
                  <div className="flex justify-center">
                    <img src={twoFaSetup.qr} alt="2FA QR Code" className="w-40 h-40 border border-terminal-rule bg-white p-2" />
                  </div>
                  <p className="text-[8px] font-mono text-terminal-label break-all">Secret: {twoFaSetup.secret}</p>
                  <div className="flex items-center gap-3">
                    <Input
                      type="text"
                      maxLength={6}
                      placeholder="000000"
                      value={twoFaOtp}
                      onChange={e => setTwoFaOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                      className="bg-terminal-panel border-terminal-rule text-terminal-value font-mono text-sm rounded-none focus:border-terminal-hold w-24 text-center tracking-[0.5em]"
                    />
                    <TerminalButton variant="primary" size="sm" onClick={handleEnable2fa} isLoading={twoFaLoading} disabled={twoFaOtp.length !== 6}>
                      <Shield className="w-3.5 h-3.5" /> ENABLE
                    </TerminalButton>
                    <TerminalButton variant="secondary" size="sm" onClick={() => { setTwoFaSetup(null); setTwoFaOtp(''); }}>
                      CANCEL
                    </TerminalButton>
                  </div>
                </div>
              )}

              {profile?.totp_enabled && (
                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-terminal-buy">
                    <Shield className="w-4 h-4" />
                    <span className="text-xs font-mono font-bold">2FA is active on your account</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <Input
                      type="text"
                      maxLength={6}
                      placeholder="000000"
                      value={twoFaOtp}
                      onChange={e => setTwoFaOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                      className="bg-terminal-panel border-terminal-rule text-terminal-value font-mono text-sm rounded-none focus:border-terminal-hold w-24 text-center tracking-[0.5em]"
                    />
                    <TerminalButton variant="danger" size="sm" onClick={handleDisable2fa} isLoading={twoFaLoading} disabled={twoFaOtp.length !== 6}>
                      DISABLE 2FA
                    </TerminalButton>
                  </div>
                </div>
              )}
            </div>
          </TerminalCard>

          {/* Avatar */}
          <TerminalCard title="AVATAR" code="AVT">
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                {profile?.settings?.avatar_url ? (
                  <img src={profile.settings.avatar_url} alt="Avatar" className="w-20 h-20 rounded border border-terminal-rule object-cover" />
                ) : (
                  <div className="w-20 h-20 rounded border border-terminal-rule bg-terminal-panel flex items-center justify-center">
                    <User className="w-8 h-8 text-terminal-label" />
                  </div>
                )}
                <div>
                  <p className="text-xs font-mono text-terminal-label mb-2">Upload a profile picture. PNG, JPG, GIF, or WebP. Max 2MB.</p>
                  <input ref={fileRef} type="file" accept="image/png,image/jpeg,image/gif,image/webp" onChange={handleAvatarUpload} className="hidden" />
                  <TerminalButton variant="secondary" size="sm" onClick={() => fileRef.current?.click()} isLoading={avatarUploading}>
                    <Upload className="w-3.5 h-3.5" /> UPLOAD
                  </TerminalButton>
                </div>
              </div>
            </div>
          </TerminalCard>
        </div>

        {/* Row 4: Security */}
        <TerminalCard title="SECURITY" code="SEC" right={!isEditingPassword ? (
          <TerminalButton variant="secondary" size="sm" onClick={() => setIsEditingPassword(true)}><Key className="w-3 h-3" /> CHANGE PASSWORD</TerminalButton>
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

        {/* Row 5: Danger Zone */}
        <TerminalCard title="DANGER ZONE" code="DNG">
          {isEditingDelete ? (
            <Form {...deleteForm}>
              <form onSubmit={deleteForm.handleSubmit(onDeleteSubmit)} className="space-y-4 max-w-xl">
                <div className="flex items-center gap-2 px-3 py-2 border border-terminal-sell/30 bg-terminal-sell/5">
                  <AlertTriangle className="w-4 h-4 text-terminal-sell shrink-0" />
                  <p className="text-[10px] font-mono text-terminal-sell">This action cannot be undone. Your account will be deactivated and all personal data retained for 30 days.</p>
                </div>
                <FormField control={deleteForm.control} name="password" render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-[9px] font-mono font-bold uppercase tracking-widest text-terminal-label">Enter your password to confirm</FormLabel>
                    <FormControl><Input type="password" {...field} className="bg-terminal-panel border-terminal-rule text-terminal-value font-mono text-xs rounded-none focus:border-terminal-sell" /></FormControl>
                    <FormMessage className="text-[9px] font-mono text-terminal-sell" />
                  </FormItem>
                )} />
                <div className="flex gap-3">
                  <TerminalButton type="submit" variant="danger" disabled={isSaving} isLoading={isSaving}>
                    <Trash2 className="w-3.5 h-3.5" /> DELETE MY ACCOUNT
                  </TerminalButton>
                  <TerminalButton type="button" variant="secondary" onClick={() => { setIsEditingDelete(false); deleteForm.reset(); }}>CANCEL</TerminalButton>
                </div>
              </form>
            </Form>
          ) : (
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-mono font-bold text-terminal-value">Delete Account</p>
                <p className="text-[10px] font-mono text-terminal-label">Permanently deactivate your account and remove access.</p>
              </div>
              <TerminalButton variant="danger" size="sm" onClick={() => setIsEditingDelete(true)}>
                <Trash2 className="w-3.5 h-3.5" /> DELETE ACCOUNT
              </TerminalButton>
            </div>
          )}
        </TerminalCard>
      </div>
    </DashboardLayout>
  );
}
