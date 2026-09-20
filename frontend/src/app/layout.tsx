// C:/Users/jasmi/OneDrive/Desktop/THERMOSENTRY-AI/frontend/src/app/layout.tsx
import '@/styles/globals.css';
import type { ReactNode } from 'react';
import Sidebar from '@/components/Sidebar';
import TopBar from '@/components/TopBar';

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className="bg-bg-base text-text-primary">
      <body className="font-body antialiased">
        <div className="flex min-h-screen">
          <Sidebar />
          <div className="flex flex-col flex-1">
            <TopBar />
            <main className="p-4 flex-1 overflow-auto">{children}</main>
          </div>
        </div>
      </body>
    </html>
  );
}
