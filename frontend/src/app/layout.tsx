'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import './globals.css';

const queryClient = new QueryClient();

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="antialiased">
        <QueryClientProvider client={queryClient}>
          <div className="min-h-screen flex">
            {/* Sidebar */}
            <Sidebar />

            {/* Main Content */}
            <main className="flex-1 flex flex-col">
              <AnimatePresence mode="wait">
                <motion.div
                  key="content"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.3, ease: 'easeOut' }}
                  className="flex-1"
                >
                  {children}
                </motion.div>
              </AnimatePresence>
            </main>
          </div>
        </QueryClientProvider>
      </body>
    </html>
  );
}

// Sidebar Component
function Sidebar() {
  const pathname = usePathname();

  return (
    <motion.aside
      initial={{ x: -100, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
      className="w-64 bg-slate-900/60 backdrop-blur-xl border-r border-white/10 p-4 flex flex-col"
    >
      {/* Logo */}
      <div className="flex items-center gap-3 mb-8 px-2">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-sky-400 to-violet-500 flex items-center justify-center">
          <span className="text-xl">🕷️</span>
        </div>
        <div>
          <h1 className="font-bold text-lg bg-gradient-to-r from-sky-400 to-violet-400 bg-clip-text text-transparent">
            Code Crawler
          </h1>
          <p className="text-xs text-slate-500">v2.0</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-2">
        <NavItem href="/" icon="📁" label="Upload" active={pathname === '/'} />
        <NavItem href="/chat" icon="💬" label="Chat" active={pathname === '/chat'} />
        <NavItem href="/search" icon="🔍" label="Search" active={pathname === '/search'} />
        <NavItem href="/refactor" icon="🔧" label="Refactor" active={pathname === '/refactor'} />
        <NavItem href="/generate" icon="✨" label="Generate" active={pathname === '/generate'} />
      </nav>

      {/* Footer */}
      <div className="pt-4 border-t border-white/10">
        <div className="px-4 py-2 text-xs text-slate-500">
          Powered by Gemini AI
        </div>
      </div>
    </motion.aside>
  );
}

function NavItem({ href, icon, label, active }: { href: string; icon: string; label: string; active: boolean }) {
  return (
    <Link href={href}>
      <motion.div
        whileHover={{ scale: 1.02, x: 4 }}
        whileTap={{ scale: 0.98 }}
        className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all cursor-pointer ${active
            ? 'bg-gradient-to-r from-sky-500/20 to-violet-500/20 border border-sky-500/30'
            : 'hover:bg-white/5'
          }`}
      >
        <span className="text-lg">{icon}</span>
        <span className={`font-medium ${active ? 'text-sky-400' : 'text-slate-300'}`}>
          {label}
        </span>
      </motion.div>
    </Link>
  );
}
