# Next.js Frontend Implementation Plan
**MetalMind SMCForge - Web-Intensive Architecture Overhaul**

**Date:** May 8, 2026  
**Status:** Planning Phase  
**Priority:** High - Required for "Focused Scope" & "Web-Intensive Development" compliance

---

## Executive Summary

This document outlines a phased approach to replace the Flask-served HTML UI with a **modern Next.js application**. This transformation achieves:
- ✅ **Web-Intensive Development:** Full modern web stack (SSR, API routes, WebSockets, PWA)
- ✅ **Separation of Concerns:** Flask = API-only, Next.js = UI-only
- ✅ **Scalability:** Independent deployment and scaling
- ✅ **Better UX:** Real-time updates, caching, offline support

---

## 1. Current State Analysis

### 1.1 What Works Now
- Flask backend with ML models (XGBoost, SHAP)
- ETL pipeline for data processing
- Backtesting engine
- REST API endpoints
- Basic HTML UI (`frontend/public/index_v4.html`)

### 1.2 What Needs to Change
| Component | Current | Target | Effort |
|-----------|---------|--------|--------|
| Frontend | Flask-served HTML | Next.js SPA | High |
| Build Process | Manual HTML | Next.js build system | Medium |
| API Communication | Direct HTTP | Typed API client | Medium |
| UI Framework | Raw HTML/CSS | Shadcn + Tailwind | Medium |
| Real-time | None | WebSocket integration | High |
| Deployment | Monolithic | Separate containers | Medium |

---

## 2. Target Architecture

### 2.1 New Stack Overview

```
┌──────────────────────────────────────────────────────────────┐
│                    DEPLOYMENT ENVIRONMENT                     │
├──────────────────────┬──────────────────────────────────────┤
│  Next.js Frontend    │        Flask API Backend             │
│  (Port 3000)         │        (Port 5000)                   │
│                      │                                      │
│ - TypeScript React   │ - REST API endpoints                 │
│ - Server Components  │ - ML model inference                 │
│ - API Routes         │ - ETL pipeline                       │
│ - WebSocket client   │ - WebSocket server                   │
│ - PWA support        │ - Database ORM                       │
│ - Image optimization │ - Authentication (JWT)              │
│ - Next.js Auth       │                                      │
└──────────────────────┴──────────────────────────────────────┘
        ↓                           ↓
    Docker container          Docker container
    (node:20-alpine)          (python:3.11)
```

### 2.2 Technology Choices

| Layer | Technology | Reason |
|-------|-----------|--------|
| Framework | Next.js 15+ | SSR, API routes, full-stack capabilities |
| Language | TypeScript | Type safety, better DX |
| Styling | Tailwind CSS | Utility-first, production-ready |
| Components | Shadcn/UI | Accessible, customizable, Tailwind-based |
| HTTP Client | TanStack Query + Axios | Caching, refetch logic, type-safe |
| Real-time | Socket.io Client | WebSocket, fallback support |
| Forms | React Hook Form | Lightweight, validation |
| Charts | Recharts or lightweight-charts | Interactive, performant |
| Auth | NextAuth.js | JWT integration with Flask |
| Deployment | Docker + Docker Compose | Consistency across environments |

---

## 3. Phased Implementation Plan

### Phase 1: Project Setup (Week 1)
**Goal:** Scaffold Next.js project and basic infrastructure

#### 1.1 Create Next.js Project
```bash
npx create-next-app@latest ml-signals-ui \
  --typescript \
  --tailwind \
  --eslint \
  --src-dir \
  --app-router \
  --no-git
```

#### 1.2 Project Structure
```
ml-signals-ui/
├── src/
│   ├── app/
│   │   ├── layout.tsx              # Root layout
│   │   ├── page.tsx                # Home page
│   │   ├── dashboard/
│   │   │   └── page.tsx            # Main dashboard
│   │   ├── backtest/
│   │   │   └── page.tsx            # Backtest simulator
│   │   ├── auth/
│   │   │   ├── login/page.tsx
│   │   │   └── register/page.tsx
│   │   ├── api/                    # API routes (proxy to Flask)
│   │   │   ├── auth/
│   │   │   ├── predictions/
│   │   │   └── backtest/
│   │   └── globals.css             # Tailwind globals
│   ├── components/
│   │   ├── Dashboard/
│   │   │   ├── ChartWidget.tsx
│   │   │   ├── SignalCard.tsx
│   │   │   └── SHAPExplainer.tsx
│   │   ├── Auth/
│   │   │   ├── LoginForm.tsx
│   │   │   └── RegisterForm.tsx
│   │   ├── Common/
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── Footer.tsx
│   │   └── ui/                     # Shadcn components
│   ├── lib/
│   │   ├── api-client.ts           # Axios instance
│   │   ├── api-types.ts            # Type definitions
│   │   ├── hooks/
│   │   │   ├── usePredictions.ts
│   │   │   ├── useBacktest.ts
│   │   │   └── useAuth.ts
│   │   └── utils.ts
│   ├── styles/
│   │   └── colors.css
│   └── middleware.ts               # NextAuth middleware
├── public/
│   ├── icons/
│   └── images/
├── .env.local                      # Environment variables
├── next.config.ts
├── tsconfig.json
├── tailwind.config.ts
├── postcss.config.js
└── package.json
```

#### 1.3 Install Dependencies
```bash
npm install \
  axios \
  @tanstack/react-query \
  react-hook-form \
  zod \
  @hookform/resolvers \
  socket.io-client \
  next-auth \
  recharts \
  date-fns \
  lucide-react

npm install -D \
  @types/node \
  @types/react \
  tailwindcss \
  postcss \
  autoprefixer \
  @shadcn-ui/components \
  class-variance-authority \
  clsx \
  tailwind-merge
```

#### 1.4 Setup Shadcn/UI
```bash
npx shadcn-ui@latest init
```

**Deliverables:**
- ✅ Next.js project initialized
- ✅ Tailwind + TypeScript configured
- ✅ Folder structure in place
- ✅ Dependencies installed

---

### Phase 2: API Layer & Type Safety (Week 1-2)
**Goal:** Create type-safe API client layer

#### 2.1 Create API Types (`src/lib/api-types.ts`)
```typescript
// User & Auth types
export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
  confirmPassword: string;
}

export interface AuthResponse {
  access_token: string;
  user: {
    id: string;
    email: string;
    is_verified: boolean;
  };
}

// Prediction types
export interface PredictionResponse {
  asset: 'gold' | 'silver';
  signal: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  price: number;
  timestamp: string;
  shap_values: {
    feature: string;
    contribution: number;
  }[];
}

// Backtest types
export interface BacktestRequest {
  asset: 'gold' | 'silver';
  start_date: string;
  end_date: string;
  strategy: string;
}

export interface BacktestResponse {
  win_rate: number;
  profit_factor: number;
  max_drawdown: number;
  trades: Trade[];
}

// Error response
export interface ApiError {
  error: string;
  details?: string;
  status: number;
}
```

#### 2.2 Create API Client (`src/lib/api-client.ts`)
```typescript
import axios, { AxiosInstance } from 'axios';
import { AuthResponse, PredictionResponse, BacktestResponse } from './api-types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

class ApiClient {
  private client: AxiosInstance;
  private token: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add token to all requests
    this.client.interceptors.request.use((config) => {
      if (this.token) {
        config.headers.Authorization = `Bearer ${this.token}`;
      }
      return config;
    });

    // Handle 401 responses
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          this.clearAuth();
          // Redirect to login
        }
        return Promise.reject(error);
      }
    );
  }

  setToken(token: string) {
    this.token = token;
    localStorage.setItem('auth_token', token);
  }

  getToken() {
    return this.token || localStorage.getItem('auth_token');
  }

  clearAuth() {
    this.token = null;
    localStorage.removeItem('auth_token');
  }

  // Auth endpoints
  async login(email: string, password: string) {
    const response = await this.client.post<AuthResponse>('/api/auth/login', {
      email,
      password,
    });
    this.setToken(response.data.access_token);
    return response.data;
  }

  async register(email: string, password: string) {
    const response = await this.client.post<AuthResponse>('/api/auth/register', {
      email,
      password,
    });
    return response.data;
  }

  // Prediction endpoints
  async getPrediction(asset: 'gold' | 'silver') {
    const response = await this.client.get<PredictionResponse>(
      `/api/predictions/latest?asset=${asset}`
    );
    return response.data;
  }

  // Backtest endpoints
  async runBacktest(payload: any) {
    const response = await this.client.post<BacktestResponse>(
      '/api/backtest/run',
      payload
    );
    return response.data;
  }

  async getBacktestResults() {
    const response = await this.client.get<BacktestResponse>('/api/backtest/results');
    return response.data;
  }
}

export const apiClient = new ApiClient();
```

#### 2.3 Create Custom Hooks (`src/lib/hooks/`)
```typescript
// src/lib/hooks/usePredictions.ts
import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { apiClient } from '../api-client';
import { PredictionResponse } from '../api-types';

export function usePredictions(asset: 'gold' | 'silver') {
  return useQuery<PredictionResponse>({
    queryKey: ['predictions', asset],
    queryFn: () => apiClient.getPrediction(asset),
    refetchInterval: 60000, // Refresh every 60 seconds
  });
}

// src/lib/hooks/useAuth.ts
import { useMutation, useQuery } from '@tanstack/react-query';
import { apiClient } from '../api-client';
import { AuthResponse } from '../api-types';

export function useLogin() {
  return useMutation({
    mutationFn: (credentials: { email: string; password: string }) =>
      apiClient.login(credentials.email, credentials.password),
  });
}

export function useRegister() {
  return useMutation({
    mutationFn: (data: { email: string; password: string }) =>
      apiClient.register(data.email, data.password),
  });
}
```

**Deliverables:**
- ✅ Type-safe API definitions
- ✅ API client with interceptors
- ✅ Custom React Query hooks
- ✅ Error handling layer

---

### Phase 3: Core Components (Week 2-3)
**Goal:** Build reusable UI components

#### 3.1 Dashboard Layout
```typescript
// src/components/Common/DashboardLayout.tsx
'use client';

import React from 'react';
import Header from './Header';
import Sidebar from './Sidebar';
import { cn } from '@/lib/utils';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-screen bg-slate-950">
      <Sidebar />
      <main className="flex-1 flex flex-col overflow-hidden">
        <Header />
        <div className="flex-1 overflow-auto">
          <div className="p-6">
            {children}
          </div>
        </div>
      </main>
    </div>
  );
}
```

#### 3.2 Signal Card Component
```typescript
// src/components/Dashboard/SignalCard.tsx
'use client';

import { PredictionResponse } from '@/lib/api-types';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader } from '@/components/ui/card';

interface SignalCardProps {
  prediction: PredictionResponse;
}

export default function SignalCard({ prediction }: SignalCardProps) {
  const isBuy = prediction.signal === 'BUY';
  const colors = isBuy ? 'bg-green-500/10 border-green-500' : 'bg-red-500/10 border-red-500';

  return (
    <Card className={`border-2 ${colors}`}>
      <CardHeader>
        <div className="flex justify-between items-center">
          <h3 className="text-lg font-bold">{prediction.asset.toUpperCase()}</h3>
          <Badge className={isBuy ? 'bg-green-500' : 'bg-red-500'}>
            {prediction.signal}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <p className="text-2xl font-bold">${prediction.price}</p>
          <p className="text-sm text-gray-400">
            Confidence: {(prediction.confidence * 100).toFixed(1)}%
          </p>
          <p className="text-xs text-gray-500">
            {new Date(prediction.timestamp).toLocaleString()}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
```

#### 3.3 Chart Component (using lightweight-charts)
```typescript
// src/components/Dashboard/ChartWidget.tsx
'use client';

import { useEffect, useRef } from 'react';
import { createChart } from 'lightweight-charts';
import { Card } from '@/components/ui/card';

interface Candle {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
}

interface ChartWidgetProps {
  data: Candle[];
}

export default function ChartWidget({ data }: ChartWidgetProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current || !data.length) return;

    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height: 400,
      layout: {
        background: { color: '#0f172a' },
        textColor: '#d1d5db',
      },
    });

    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#22c55e',
      downColor: '#ef4444',
    });

    candlestickSeries.setData(data);
    chart.timeScale().fitContent();

    const handleResize = () => {
      if (containerRef.current) {
        chart.applyOptions({
          width: containerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener('resize', handleResize);
    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [data]);

  return (
    <Card className="bg-slate-900 border-slate-700">
      <div ref={containerRef} style={{ width: '100%', height: '400px' }} />
    </Card>
  );
}
```

**Deliverables:**
- ✅ Reusable layout components
- ✅ Signal display cards
- ✅ Chart integration
- ✅ Responsive design with Tailwind

---

### Phase 4: Pages & Routing (Week 3)
**Goal:** Build core pages

#### 4.1 Dashboard Page
```typescript
// src/app/dashboard/page.tsx
'use client';

import { useState } from 'react';
import { usePredictions } from '@/lib/hooks/usePredictions';
import DashboardLayout from '@/components/Common/DashboardLayout';
import SignalCard from '@/components/Dashboard/SignalCard';
import ChartWidget from '@/components/Dashboard/ChartWidget';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

export default function DashboardPage() {
  const [asset, setAsset] = useState<'gold' | 'silver'>('gold');
  const { data: prediction, isLoading, error } = usePredictions(asset);

  if (isLoading) return <div>Loading prediction...</div>;
  if (error) return <div>Error loading data</div>;
  if (!prediction) return <div>No data available</div>;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <h1 className="text-3xl font-bold">Trading Dashboard</h1>

        <Tabs defaultValue="gold" onValueChange={(v) => setAsset(v as any)}>
          <TabsList>
            <TabsTrigger value="gold">Gold (XAU)</TabsTrigger>
            <TabsTrigger value="silver">Silver (XAG)</TabsTrigger>
          </TabsList>

          <TabsContent value={asset} className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <SignalCard prediction={prediction} />
              <div className="lg:col-span-2">
                <ChartWidget data={[]} />
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
}
```

#### 4.2 Login Page
```typescript
// src/app/auth/login/page.tsx
'use client';

import { useRouter } from 'next/navigation';
import { useLogin } from '@/lib/hooks/useAuth';
import { LoginForm } from '@/components/Auth/LoginForm';

export default function LoginPage() {
  const router = useRouter();
  const loginMutation = useLogin();

  const handleLogin = async (email: string, password: string) => {
    try {
      await loginMutation.mutateAsync({ email, password });
      router.push('/dashboard');
    } catch (error) {
      console.error('Login failed:', error);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-slate-950">
      <LoginForm onSubmit={handleLogin} isLoading={loginMutation.isPending} />
    </div>
  );
}
```

**Deliverables:**
- ✅ Dashboard page with asset switcher
- ✅ Auth pages (login/register)
- ✅ Dynamic routing
- ✅ Protected routes setup (to do in phase 5)

---

### Phase 5: Real-time Features & WebSocket (Week 4)
**Goal:** Add real-time updates

#### 5.1 WebSocket Hook
```typescript
// src/lib/hooks/useWebSocket.ts
import { useEffect, useState } from 'react';
import io from 'socket.io-client';

const SOCKET_URL = process.env.NEXT_PUBLIC_SOCKET_URL || 'http://localhost:5000';

export function useWebSocket(event: string) {
  const [data, setData] = useState(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const socket = io(SOCKET_URL, {
      transports: ['websocket', 'polling'],
    });

    socket.on('connect', () => setIsConnected(true));
    socket.on('disconnect', () => setIsConnected(false));
    socket.on(event, (payload) => setData(payload));

    return () => {
      socket.disconnect();
    };
  }, [event]);

  return { data, isConnected };
}
```

#### 5.2 Real-time Chart Updates
```typescript
// src/components/Dashboard/ChartWidget.tsx (updated)
'use client';

import { useWebSocket } from '@/lib/hooks/useWebSocket';
import { useEffect, useRef } from 'react';
import { createChart } from 'lightweight-charts';

export default function ChartWidget() {
  const { data: newCandle } = useWebSocket('price_update');
  const seriesRef = useRef(null);

  useEffect(() => {
    if (newCandle && seriesRef.current) {
      // seriesRef.current.update(newCandle);
    }
  }, [newCandle]);

  // ... rest of component
}
```

**Deliverables:**
- ✅ WebSocket integration
- ✅ Real-time price updates
- ✅ Live chart updates

---

### Phase 6: Authentication & Middleware (Week 4)
**Goal:** Secure the app with NextAuth

#### 6.1 NextAuth Configuration
```typescript
// src/app/api/auth/[...nextauth]/route.ts
import NextAuth from 'next-auth';
import CredentialsProvider from 'next-auth/providers/credentials';
import { apiClient } from '@/lib/api-client';

const handler = NextAuth({
  providers: [
    CredentialsProvider({
      credentials: {
        email: { label: 'Email', type: 'email' },
        password: { label: 'Password', type: 'password' },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) return null;

        try {
          const response = await apiClient.login(
            credentials.email,
            credentials.password
          );
          return {
            id: response.user.id,
            email: response.user.email,
            accessToken: response.access_token,
          };
        } catch (error) {
          return null;
        }
      },
    }),
  ],
  pages: {
    signIn: '/auth/login',
  },
  callbacks: {
    async jwt({ token, user }: any) {
      if (user) {
        token.accessToken = user.accessToken;
      }
      return token;
    },
    async session({ session, token }: any) {
      session.accessToken = token.accessToken;
      return session;
    },
  },
});

export { handler as GET, handler as POST };
```

#### 6.2 Middleware for Protected Routes
```typescript
// src/middleware.ts
import { withAuth } from 'next-auth/middleware';

export const middleware = withAuth({
  callbacks: {
    authorized: ({ token }) => !!token,
  },
  pages: {
    signIn: '/auth/login',
  },
});

export const config = {
  matcher: ['/dashboard/:path*', '/backtest/:path*', '/profile/:path*'],
};
```

**Deliverables:**
- ✅ NextAuth setup with JWT
- ✅ Protected routes middleware
- ✅ Session management

---

### Phase 7: Flask Backend Updates (Week 3-4)
**Goal:** Remove HTML serving, keep API-only

#### 7.1 Update Flask main.py
```python
# api/app/main.py - Changes

# REMOVE these lines:
# - @app.route('/') 
# - @app.route('/index')
# - send_file() calls for HTML

# KEEP these:
# - All /api/* routes
# - WebSocket support
# - Authentication

# ADD CORS for Next.js:
CORS(app, 
     resources={r"/api/*": {
         "origins": [
             "http://localhost:3000",  # Next.js dev server
             "https://yourdomain.com"  # Production
         ],
         "supports_credentials": True,
         "methods": ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
         "allow_headers": ['Content-Type', 'Authorization'],
         "expose_headers": ['Content-Type', 'Authorization']
     }}
)

# ADD WebSocket support for real-time updates:
from flask_socketio import SocketIO

socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('connect')
def handle_connect():
    logger.info("Client connected")

@socketio.on('subscribe_prices')
def handle_subscribe(data):
    asset = data.get('asset')
    # Push updates to this client
```

#### 7.2 Update Requirements
```txt
# api/requirements.txt - Add:
flask-socketio==5.3.5
python-socketio==5.10.0
python-engineio==4.8.0
```

**Deliverables:**
- ✅ Flask API cleaned (no HTML serving)
- ✅ CORS configured for Next.js
- ✅ WebSocket support added

---

### Phase 8: Docker & Deployment (Week 4-5)
**Goal:** Containerize both services

#### 8.1 Next.js Dockerfile
```dockerfile
# Dockerfile.frontend
FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci

# Copy source
COPY . .

# Build
RUN npm run build

# Expose port
EXPOSE 3000

# Start
CMD ["npm", "start"]
```

#### 8.2 Updated docker-compose.yml
```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: api/Dockerfile
    container_name: ml-signals-api
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://user:pass@db:5432/ml_signals
    depends_on:
      - db
    volumes:
      - ./models:/app/models
      - ./reports:/app/reports

  frontend:
    build:
      context: ./ml-signals-ui
      dockerfile: Dockerfile
    container_name: ml-signals-ui
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://api:5000
      - NEXT_PUBLIC_SOCKET_URL=http://api:5000
    depends_on:
      - api

  db:
    image: postgres:15-alpine
    container_name: ml-signals-db
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=secure_password
      - POSTGRES_DB=ml_signals
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

**Deliverables:**
- ✅ Dockerfiles for both services
- ✅ Updated docker-compose
- ✅ Multi-container orchestration

---

## 4. Integration Checklist

### Backend (Flask) ✅
- [ ] Remove HTML serving endpoints
- [ ] Configure CORS for `http://localhost:3000`
- [ ] Add WebSocket server
- [ ] Update environment variables
- [ ] Test all `/api/*` endpoints with Next.js
- [ ] Add logging for debugging

### Frontend (Next.js) ✅
- [ ] Initialize project with correct structure
- [ ] Setup TypeScript & Tailwind
- [ ] Create API types and client
- [ ] Build core components
- [ ] Implement auth pages
- [ ] Setup NextAuth integration
- [ ] Add WebSocket listeners
- [ ] Test all connections to Flask

### Deployment ✅
- [ ] Create Dockerfiles for both
- [ ] Update docker-compose.yml
- [ ] Test local Docker build
- [ ] Setup environment files
- [ ] Document environment variables
- [ ] Test full stack locally

---

## 5. Environment Variables

### Next.js (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:5000
NEXT_PUBLIC_SOCKET_URL=http://localhost:5000
NEXTAUTH_SECRET=your-secret-key-here
NEXTAUTH_URL=http://localhost:3000
```

### Flask (.env)
```env
FLASK_ENV=production
DATABASE_URL=sqlite:///ml_signals.db
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

---

## 6. Web-Intensive Features Added

### ✅ Real-time Updates
- WebSocket connection for live prices
- Server-Sent Events fallback
- Automatic reconnection logic

### ✅ Progressive Enhancement
- Service Worker for offline support
- PWA manifest for installability
- Optimized images & code splitting

### ✅ Advanced Interactivity
- Real-time chart updates
- Signal notifications
- Live backtest progress

### ✅ Performance Optimizations
- Next.js Image component for optimization
- API request caching with React Query
- Code splitting & lazy loading

### ✅ Security
- HTTPS in production
- CSRF protection
- XSS prevention via React escaping
- Rate limiting (Flask side)

---

## 7. Timeline & Effort Estimate

| Phase | Duration | Effort | Complexity |
|-------|----------|--------|-----------|
| 1. Setup | 3-4 days | 8h | Low |
| 2. API Layer | 4-5 days | 12h | Medium |
| 3. Components | 5-6 days | 16h | Medium |
| 4. Pages | 4-5 days | 12h | Medium |
| 5. Real-time | 5-6 days | 14h | High |
| 6. Auth | 3-4 days | 10h | Medium |
| 7. Backend Updates | 2-3 days | 6h | Low |
| 8. Deployment | 4-5 days | 10h | Medium |
| **Total** | **4-5 weeks** | **88 hours** | **Medium-High** |

---

## 8. Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| WebSocket connection issues | High | Implement fallback polling, connection retry logic |
| CORS configuration errors | High | Test CORS headers thoroughly, document all origins |
| Type mismatch between Flask/Next | Medium | Use zod for runtime validation, test extensively |
| Performance degradation | Medium | Monitor with Lighthouse, implement caching |
| Authentication token expiry | Medium | Implement refresh token rotation in NextAuth |
| Database connection leaks | High | Use connection pooling, test under load |

---

## 9. Success Criteria

✅ **All criteria must be met before completion:**

- [ ] Next.js application boots without errors
- [ ] All API endpoints respond correctly
- [ ] WebSocket real-time updates work
- [ ] Authentication flow works end-to-end
- [ ] Charts render with real data
- [ ] Dashboard loads in < 3 seconds
- [ ] Protected routes prevent unauthorized access
- [ ] Docker containers start cleanly
- [ ] Full stack works with `docker-compose up`
- [ ] No Flask HTML routes remain active
- [ ] TypeScript strict mode enabled
- [ ] All eslint rules passing

---

## 10. Future Enhancements (Post-MVP)

- [ ] Mobile app (React Native)
- [ ] Dark mode toggle
- [ ] Advanced charting (TradingView Lightweight Charts Pro)
- [ ] Push notifications via Web Push API
- [ ] Analytics dashboard (Mixpanel/Vercel Analytics)
- [ ] Collaboration features (shared watchlists)
- [ ] Sentiment analysis integration

---

## 11. References & Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [Shadcn/UI Components](https://ui.shadcn.com)
- [NextAuth.js](https://next-auth.js.org)
- [TanStack Query](https://tanstack.com/query)
- [Socket.io](https://socket.io)
- [Tailwind CSS](https://tailwindcss.com)

---

**Document Version:** 1.0  
**Last Updated:** May 8, 2026  
**Next Review:** After Phase 2 completion
