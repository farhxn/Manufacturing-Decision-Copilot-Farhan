'use client';

import React, { useState } from 'react';
import { usePathname } from 'next/navigation';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';
import { PageTransition } from './PageTransition';

export const AppLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-[var(--bg-app)] flex text-[var(--text-primary)] transition-colors duration-200">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Main content — offset by sidebar on desktop */}
      <div className="flex-1 lg:pl-[280px] min-w-0">
        <Topbar onMenuClick={() => setSidebarOpen(true)} />
        <main className="pt-16 px-4 sm:px-6 lg:px-8 pb-12 min-h-[calc(100vh-4rem)]">
          <PageTransition routeKey={pathname ?? '/'}>
            {children}
          </PageTransition>
        </main>
      </div>
    </div>
  );
};
