import NextAuth, { NextAuthOptions, User as NextAuthUser } from 'next-auth';
import CredentialsProvider from 'next-auth/providers/credentials';
import { AuthResponse } from '@/lib/api-types';

interface ExtendedUser extends NextAuthUser {
  accessToken?: string;
  refreshToken?: string;
  id: string;
}

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      name: 'SMCForge Credentials',
      credentials: {
        email: { label: 'Email', type: 'email' },
        password: { label: 'Password', type: 'password' },
        totp_code: { label: '2FA Code', type: 'text' },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          return null;
        }

        const defaultApiUrl = process.env.NODE_ENV === 'production' ? 'http://api:5000' : 'http://localhost:5000';
        const API_BASE_URL = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || defaultApiUrl;

        const loginUrl = `${API_BASE_URL}/api/auth/login`;

        const callLogin = async (payload: Record<string, any>) => {
          const res = await fetch(loginUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
          });
          const raw = await res.text();
          let parsed: AuthResponse & { requires_2fa?: boolean } | null = null;
          try {
            parsed = JSON.parse(raw);
          } catch {
            // Response was not valid JSON
          }
          return { res, raw, parsed } as const;
        };

        try {
          const attempt1 = await callLogin({ email: credentials.email, password: credentials.password, totp_code: credentials.totp_code || undefined });

          if (attempt1.res.ok && attempt1.parsed) {
            const data = attempt1.parsed;
            if (data.requires_2fa) throw new Error('requires_2fa');
            if (data.success && data.token) {
              return {
                id: data.data.user.id.toString(),
                email: data.data.user.email,
                name: data.data.user.username,
                accessToken: data.token,
                refreshToken: data.refresh_token,
              } as ExtendedUser;
            }
          }

          // If 401 or no usable JSON, try username fallback once
          if (attempt1.res.status === 401) {
            const attempt2 = await callLogin({ username: credentials.email, password: credentials.password, totp_code: credentials.totp_code || undefined });

            if (attempt2.res.ok && attempt2.parsed) {
              const data = attempt2.parsed;
              if (data.requires_2fa) throw new Error('requires_2fa');
              if (data.success && data.token) {
                return {
                  id: data.data.user.id.toString(),
                  email: data.data.user.email,
                  name: data.data.user.username,
                  accessToken: data.token,
                  refreshToken: data.refresh_token,
                } as ExtendedUser;
              }
            }
          }

          throw new Error('Login failed');
        } catch (error) {
          throw error;
        }
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        const u = user as ExtendedUser;
        token.id = u.id;
        token.accessToken = u.accessToken;
        token.refreshToken = u.refreshToken;
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        session.user.id = token.id as string;
        session.user.accessToken = token.accessToken as string;
        session.user.refreshToken = token.refreshToken as string;
      }
      return session;
    },
  },
  pages: {
    signIn: '/auth/login',
  },
  session: {
    strategy: 'jwt',
    maxAge: 30 * 24 * 60 * 60, // 30 days
  },
  secret: process.env.NEXTAUTH_SECRET,
};
