import { withAuth } from 'next-auth/middleware';
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

/**
 * NextAuth middleware to protect routes and redirect unauthorized users to login.
 * In development (no NEXTAUTH_SECRET), bypass auth so the preview renders.
 */
const authMiddleware = withAuth({
  callbacks: {
    authorized: ({ token }) => !!token,
  },
});

export default function middleware(req: NextRequest) {
  if (process.env.NODE_ENV === 'development' && !process.env.NEXTAUTH_SECRET) {
    return NextResponse.next();
  }
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return (authMiddleware as any)(req);
}

export const config = {
  matcher: [
    '/dashboard/:path*',
    '/backtest/:path*',
  ],
};
