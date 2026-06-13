import { createBrowserRouter, Navigate } from 'react-router-dom';
import { AuthGuard, GuestGuard } from '@/guards/AuthGuard';
import { Dashboard } from '@/pages/Dashboard';
import { Login } from '@/pages/Login';
import { Register } from '@/pages/Register';
import { ForgotPassword } from '@/pages/ForgotPassword';
import { ResetPassword } from '@/pages/ResetPassword';
import { Profile } from '@/pages/Profile';
import { NotFound } from '@/pages/NotFound';

/**
 * Application Router
 * Defines all routes with protection
 */
export const router = createBrowserRouter([
  {
    path: '/',
    element: <Navigate to="/dashboard" replace />,
  },
  
  // Protected Routes (require authentication)
  {
    path: '/dashboard',
    element: (
      <AuthGuard>
        <Dashboard />
      </AuthGuard>
    ),
  },
  {
    path: '/profile',
    element: (
      <AuthGuard>
        <Profile />
      </AuthGuard>
    ),
  },
  
  // Guest Routes (only accessible when NOT authenticated)
  {
    path: '/login',
    element: (
      <GuestGuard>
        <Login />
      </GuestGuard>
    ),
  },
  {
    path: '/register',
    element: (
      <GuestGuard>
        <Register />
      </GuestGuard>
    ),
  },
  {
    path: '/forgot-password',
    element: (
      <GuestGuard>
        <ForgotPassword />
      </GuestGuard>
    ),
  },
  {
    path: '/reset-password',
    element: (
      <GuestGuard>
        <ResetPassword />
      </GuestGuard>
    ),
  },
  
  // 404 - Not Found
  {
    path: '*',
    element: <NotFound />,
  },
]);
