import { withAuth } from 'next-auth/middleware';
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

/**
 * NextAuth middleware — protects backtest and other sensitive routes.
 * Dashboard auth-gating is handled at the page level via getServerSession.
 */
const authMiddleware = withAuth({
  callbacks: {
    authorized: ({ token }) => !!token,
  },
});

export default function middleware(req: NextRequest) {
  // Bypass auth middleware in dev when no secret is configured (preview mode)
  if (!process.env.NEXTAUTH_SECRET) {
    return NextResponse.next();
  }
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return (authMiddleware as any)(req);
}

export const config = {
  matcher: [
    '/backtest/:path*',
  ],
};
