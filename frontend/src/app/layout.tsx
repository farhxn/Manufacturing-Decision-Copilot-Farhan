import React from 'react';
import type { Metadata } from 'next';
import '../styles/globals.css';
import { AppLayout } from '@/components/layout/AppLayout';
import { QueryProvider } from '@/components/providers/QueryProvider';

export const metadata: Metadata = {
  title: 'Manufacturing Decision Copilot',
  description: 'Evidence-backed manufacturing decision intelligence platform',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <QueryProvider>
          <AppLayout>{children}</AppLayout>
        </QueryProvider>
      </body>
    </html>
  );
}
