import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react-swc';
import { VitePWA } from 'vite-plugin-pwa';
import { visualizer } from 'rollup-plugin-visualizer';
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.ico', 'robots.txt'],
      manifest: {
        name: 'ML Trading Signals',
        short_name: 'MLSignals',
        description: 'AI-Powered Trading Signals for Gold & Silver',
        theme_color: '#1976d2',
        background_color: '#121212',
        display: 'standalone',
        icons: [
          {
            src: '/icon-192.png',
            sizes: '192x192',
            type: 'image/png',
          },
          {
            src: '/icon-512.png',
            sizes: '512x512',
            type: 'image/png',
          },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
        runtimeCaching: [
          {
            urlPattern: /^https?:\/\/localhost:5000\/api\/.*$/,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-cache',
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 300, // 5 minutes
              },
              networkTimeoutSeconds: 10,
            },
          },
        ],
      },
    }),
    visualizer({
      open: false,
      gzipSize: true,
      brotliSize: true,
      filename: 'dist/stats.html',
    }),
  ],

  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
      '@store': path.resolve(__dirname, './src/store'),
      '@api': path.resolve(__dirname, './src/api'),
      '@utils': path.resolve(__dirname, './src/utils'),
      '@pages': path.resolve(__dirname, './src/pages'),
      '@types': path.resolve(__dirname, './src/types'),
      '@lib': path.resolve(__dirname, './src/lib'),
      '@features': path.resolve(__dirname, './src/features'),
      '@config': path.resolve(__dirname, './src/config'),
      '@guards': path.resolve(__dirname, './src/guards'),
      '@providers': path.resolve(__dirname, './src/providers'),
      '@styles': path.resolve(__dirname, './src/styles'),
    },
  },

  server: {
    port: 3000,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        secure: false,
      },
      '/ws': {
        target: 'ws://localhost:5000',
        ws: true,
      },
    },
  },

  build: {
    target: 'esnext',
    minify: 'terser',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
          'vendor-ui': ['@mui/material', '@emotion/react', '@emotion/styled'],
          'vendor-charts': ['lightweight-charts', 'recharts'],
          'vendor-query': ['@tanstack/react-query'],
          'vendor-utils': ['date-fns', 'axios', 'zustand', 'zod'],
        },
      },
    },
    chunkSizeWarningLimit: 600,
  },

  define: {
    __APP_VERSION__: JSON.stringify(process.env.npm_package_version || '1.0.0'),
  },

  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      '@mui/material',
      '@emotion/react',
      '@emotion/styled',
      'axios',
      'zustand',
    ],
  },
});
