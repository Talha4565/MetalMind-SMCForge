import { withAuth } from 'next-auth/middleware';

/**
 * NextAuth middleware to protect routes and redirect unauthorized users to login.
 */
export default withAuth({
  callbacks: {
    authorized: ({ token }) => !!token,
  },
});

export const config = {
  matcher: [
    '/dashboard/:path*',
    '/backtest/:path*',
  ],
};
