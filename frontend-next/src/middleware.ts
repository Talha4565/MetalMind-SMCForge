import { withAuth } from 'next-auth/middleware';
import type { NextRequest } from 'next/server';

export default withAuth(
  function middleware(req: NextRequest) {
    // The withAuth wrapper handles redirecting unauthenticated users.
    // This function runs only for authenticated requests on matched routes.
  },
  {
    callbacks: {
      authorized: ({ token }) => !!token,
    },
    pages: {
      signIn: '/auth/login',
    },
  }
);

export const config = {
  matcher: ['/dashboard/:path*', '/backtest/:path*'],
};
