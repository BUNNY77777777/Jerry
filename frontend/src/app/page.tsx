"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, Sparkles } from "lucide-react";

interface AuthStatus {
  authenticated: boolean;
  email?: string;
  token_expired?: boolean;
  has_refresh_token?: boolean;
}

export default function HomePage() {
  const [authStatus, setAuthStatus] = useState<AuthStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [command, setCommand] = useState("");

  const apiBase =
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    "https://jerry-t5rd.onrender.com";

  useEffect(() => {
    let isMounted = true;

    async function checkAuth() {
      try {
        const res = await fetch(`${apiBase}/api/auth/status`, {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
        });
        if (res.ok) {
          const data = await res.json();
          if (isMounted) {
            setAuthStatus(data);
          }
        } else {
          if (isMounted) {
            setAuthStatus({ authenticated: false });
          }
        }
      } catch (err) {
        console.error("Failed to check auth status:", err);
        if (isMounted) {
          setAuthStatus({ authenticated: false });
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    checkAuth();

    return () => {
      isMounted = false;
    };
  }, [apiBase]);

  const loginUrl = `${apiBase}/api/auth/login`;
  const connectedEmail = authStatus?.email || "bunny777bsbn@gmail.com";
  const userInitial = connectedEmail ? connectedEmail[0].toUpperCase() : "E";

  const handleCommandSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!command.trim()) return;
    // Reserved for future agent workflow dispatch
  };

  return (
    <div className="min-h-screen bg-[#001F3F] text-white flex flex-col selection:bg-white/20">
      {/* 1. Professional Header */}
      <header className="w-full border-b border-white/10 bg-[#001F3F]/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <h1 className="text-2xl sm:text-3xl font-serif tracking-normal text-white font-normal drop-shadow-sm">
              Jerry Executive Cockpit
            </h1>
          </div>

          {/* Profile & Status on Right */}
          <div className="flex items-center space-x-4">
            {loading ? (
              <div className="w-10 h-10 rounded-full bg-white/10 animate-pulse" />
            ) : authStatus?.authenticated ? (
              <div
                className="relative group cursor-pointer"
                title={`Connected as ${connectedEmail}`}
              >
                <div className="w-10 h-10 rounded-full bg-white/10 border border-white/20 flex items-center justify-center font-serif text-lg font-medium text-white shadow-sm transition-all duration-200 group-hover:border-white/40">
                  {userInitial}
                </div>
                {/* Subtle glowing status dot */}
                <span className="absolute bottom-0 right-0 flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-60"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500 ring-2 ring-[#001F3F]"></span>
                </span>
              </div>
            ) : (
              <Link
                href={loginUrl}
                className="inline-flex items-center gap-2 px-4 py-2 text-xs uppercase tracking-wider font-sans font-medium text-[#001F3F] bg-white rounded-full hover:bg-slate-100 transition-all duration-200 shadow-sm"
              >
                <span className="w-2 h-2 rounded-full bg-amber-500"></span>
                Connect
              </Link>
            )}
          </div>
        </div>
      </header>

      {/* 2. Center Command Interface */}
      <main className="flex-1 flex flex-col items-center justify-center px-6 py-12 relative">
        <div className="w-full max-w-3xl flex flex-col items-center text-center space-y-8">
          <div className="space-y-3">
            <p className="text-xs uppercase tracking-[0.25em] text-white/50 font-sans font-medium">
              Autonomous Chief of Staff
            </p>
            <h2 className="text-4xl sm:text-5xl md:text-6xl font-serif tracking-tight text-white font-normal drop-shadow">
              How may I assist you today?
            </h2>
          </div>

          {/* Command Bar Form */}
          <form
            onSubmit={handleCommandSubmit}
            className="w-full relative group"
          >
            <div className="relative flex items-center w-full rounded-2xl bg-white/[0.04] backdrop-blur-xl border border-white/15 shadow-2xl transition-all duration-300 focus-within:border-white/40 focus-within:ring-2 focus-within:ring-white/20 focus-within:bg-white/[0.07] hover:border-white/25">
              <div className="pl-6 pr-2 text-white/40 group-focus-within:text-white/80 transition-colors">
                <Sparkles className="w-5 h-5" />
              </div>
              <input
                type="text"
                value={command}
                onChange={(e) => setCommand(e.target.value)}
                placeholder="Awaiting your command..."
                className="w-full py-5 pr-14 pl-2 bg-transparent text-white placeholder-white/40 font-sans text-base sm:text-lg focus:outline-none tracking-normal"
              />
              <button
                type="submit"
                aria-label="Send Command"
                className="absolute right-3.5 p-2.5 rounded-xl bg-white/10 hover:bg-white/20 text-white/70 hover:text-white transition-all duration-200 focus:outline-none disabled:opacity-30 disabled:pointer-events-none cursor-pointer"
                disabled={!command.trim()}
              >
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </form>

          {/* Subtle Suggested Directives */}
          <div className="flex flex-wrap items-center justify-center gap-2.5 pt-2">
            {[
              "Brief me on priority unread emails",
              "Review upcoming schedule & conflicts",
              "Draft weekly executive digest",
            ].map((suggestion) => (
              <button
                key={suggestion}
                onClick={() => setCommand(suggestion)}
                className="px-3.5 py-1.5 rounded-lg bg-white/[0.03] hover:bg-white/[0.08] border border-white/10 text-xs text-white/70 hover:text-white font-sans transition-all duration-150 backdrop-blur-sm"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}


