"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import {
  Activity,
  ArrowRight,
  Bot,
  Calendar,
  CheckCircle2,
  Clock,
  Cpu,
  Inbox,
  Loader2,
  Mail,
  Network,
  Radio,
  Send,
  ShieldCheck,
  Sparkles,
  Terminal,
  User,
  Zap,
} from "lucide-react";

interface AuthStatus {
  authenticated: boolean;
  email?: string;
  token_expired?: boolean;
  has_refresh_token?: boolean;
}

interface Message {
  id: string;
  sender: "user" | "jerry";
  text: string;
  timestamp: string;
}

export default function HomePage() {
  const [authStatus, setAuthStatus] = useState<AuthStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [command, setCommand] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "init-1",
      sender: "jerry",
      text: "Executive Cockpit initialized. Neural telemetry online and standing by for voice or text directives.",
      timestamp: "10:14 AM",
    },
  ]);

  const feedEndRef = useRef<HTMLDivElement | null>(null);

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

  useEffect(() => {
    feedEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isProcessing]);

  const loginUrl = `${apiBase}/api/auth/login`;
  const connectedEmail = authStatus?.email || "bunny777bsbn@gmail.com";
  const userInitial = connectedEmail ? connectedEmail[0].toUpperCase() : "E";

  const handleCommandSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const prompt = command.trim();
    if (!prompt || isProcessing) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      sender: "user",
      text: prompt,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMessage]);
    setCommand("");
    setIsProcessing(true);

    try {
      const res = await fetch(`${apiBase}/api/command`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ prompt }),
      });

      if (!res.ok) {
        throw new Error(`Server returned error: ${res.status}`);
      }

      const data = await res.json();
      const replyText = data.reply || "Directive dispatched successfully.";

      const agentMessage: Message = {
        id: (Date.now() + 1).toString(),
        sender: "jerry",
        text: replyText,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, agentMessage]);
    } catch (err: any) {
      console.error("Command execution error:", err);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        sender: "jerry",
        text: `Execution notice: ${err.message || "Unable to route command to backend instance."}`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="h-screen overflow-hidden text-brand-white bg-brand-navy flex flex-col font-sans selection:bg-white/20">
      {/* Sleek Top Navigation Bar */}
      <header className="w-full h-16 border-b border-white/10 bg-brand-navy/90 backdrop-blur-lg px-6 flex items-center justify-between z-40 shrink-0">
        <div className="flex items-center space-x-3">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_rgba(52,211,153,0.8)]"></span>
            <h1 className="text-2xl font-serif tracking-normal text-white font-normal drop-shadow-sm">
              Jerry Executive Cockpit
            </h1>
          </div>
          <span className="text-[10px] uppercase font-mono tracking-widest px-2 py-0.5 rounded bg-white/10 text-white/60 border border-white/10 hidden sm:inline-block">
            Autonomous OS v2.4
          </span>
        </div>

        {/* Header Right Profile & System Status */}
        <div className="flex items-center space-x-4">
          <div className="hidden md:flex items-center space-x-3 text-xs font-mono text-white/50 border-r border-white/10 pr-4">
            <div className="flex items-center gap-1.5">
              <Radio className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
              <span>GATEWAY: CONNECTED</span>
            </div>
          </div>

          {loading ? (
            <div className="w-9 h-9 rounded-full bg-white/10 animate-pulse" />
          ) : authStatus?.authenticated ? (
            <div
              className="relative group cursor-pointer flex items-center gap-3"
              title={`Authenticated as ${connectedEmail}`}
            >
              <div className="text-right hidden sm:block">
                <p className="text-xs font-medium text-white/90 truncate max-w-[150px]">
                  {connectedEmail}
                </p>
                <p className="text-[10px] font-mono text-emerald-400">EXECUTIVE ACCESS</p>
              </div>
              <div className="relative">
                <div className="w-9 h-9 rounded-full bg-white/10 border border-white/20 flex items-center justify-center font-serif text-base font-medium text-white shadow-sm transition-all duration-200 group-hover:border-white/50">
                  {userInitial}
                </div>
                <span className="absolute bottom-0 right-0 flex h-2.5 w-2.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-60"></span>
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500 ring-2 ring-brand-navy"></span>
                </span>
              </div>
            </div>
          ) : (
            <Link
              href={loginUrl}
              className="inline-flex items-center gap-2 px-3.5 py-1.5 text-xs uppercase tracking-wider font-medium text-brand-navy bg-white rounded-full hover:bg-slate-100 transition-all duration-200 shadow-sm"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
              Connect OAuth
            </Link>
          )}
        </div>
      </header>

      {/* Main 12-Column Grid Layout */}
      <div className="flex-1 grid grid-cols-12 gap-5 p-5 overflow-hidden">
        {/* =========================================
            LEFT PANE: System Diagnostics & Context (col-span-3)
            ========================================= */}
        <aside className="col-span-3 h-full flex flex-col gap-4 overflow-hidden">
          <div className="flex-1 bg-white/5 border border-white/10 backdrop-blur-md rounded-2xl p-5 flex flex-col justify-between overflow-y-auto no-scrollbar shadow-xl">
            <div className="space-y-6">
              {/* Header */}
              <div className="flex items-center justify-between pb-3 border-b border-white/10">
                <div className="flex items-center gap-2 text-white/80">
                  <Cpu className="w-4 h-4 text-emerald-400" />
                  <h2 className="text-xs uppercase font-mono tracking-wider font-semibold text-white/90">
                    System Telemetry
                  </h2>
                </div>
                <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/60 border border-emerald-800/60 px-2 py-0.5 rounded">
                  HEALTHY
                </span>
              </div>

              {/* Core Metrics */}
              <div className="space-y-3">
                <div className="text-[11px] uppercase tracking-wider text-white/40 font-mono">
                  Core Metrics
                </div>
                <div className="grid grid-cols-1 gap-2.5">
                  <div className="bg-white/[0.03] border border-white/10 rounded-xl p-3 flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <Activity className="w-4 h-4 text-sky-400" />
                      <span className="text-xs text-white/70">Gateway Latency</span>
                    </div>
                    <span className="font-mono text-xs font-semibold text-sky-400">12ms</span>
                  </div>

                  <div className="bg-white/[0.03] border border-white/10 rounded-xl p-3 flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <Network className="w-4 h-4 text-emerald-400" />
                      <span className="text-xs text-white/70">Neural Router</span>
                    </div>
                    <span className="font-mono text-xs font-semibold text-emerald-400">ONLINE</span>
                  </div>

                  <div className="bg-white/[0.03] border border-white/10 rounded-xl p-3 flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <Zap className="w-4 h-4 text-amber-400" />
                      <span className="text-xs text-white/70">Token Pool Limit</span>
                    </div>
                    <span className="font-mono text-xs font-semibold text-amber-300">
                      94.2k / 1M
                    </span>
                  </div>
                </div>
              </div>

              {/* Active MCP Nodes */}
              <div className="space-y-3">
                <div className="text-[11px] uppercase tracking-wider text-white/40 font-mono">
                  Active Nodes
                </div>
                <div className="space-y-2">
                  <div className="bg-white/[0.03] border border-white/10 rounded-xl p-3 flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <Mail className="w-4 h-4 text-rose-400" />
                      <div>
                        <div className="text-xs font-medium text-white/90">Gmail MCP Toolset</div>
                        <div className="text-[10px] text-white/40 font-mono">
                          Read, Draft, Send, Threads
                        </div>
                      </div>
                    </div>
                    <span className="relative flex h-2.5 w-2.5">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-60"></span>
                      <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
                    </span>
                  </div>

                  <div className="bg-white/[0.03] border border-white/10 rounded-xl p-3 flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <Calendar className="w-4 h-4 text-indigo-400" />
                      <div>
                        <div className="text-xs font-medium text-white/90">Calendar MCP Node</div>
                        <div className="text-[10px] text-white/40 font-mono">
                          Schedule, Conflicts, Events
                        </div>
                      </div>
                    </div>
                    <span className="relative flex h-2.5 w-2.5">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-60"></span>
                      <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
                    </span>
                  </div>

                  <div className="bg-white/[0.03] border border-white/10 rounded-xl p-3 flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <ShieldCheck className="w-4 h-4 text-purple-400" />
                      <div>
                        <div className="text-xs font-medium text-white/90">Governance Engine</div>
                        <div className="text-[10px] text-white/40 font-mono">
                          Human-in-the-Loop Safe
                        </div>
                      </div>
                    </div>
                    <span className="w-2 h-2 rounded-full bg-purple-400"></span>
                  </div>
                </div>
              </div>
            </div>

            {/* Bottom Context Info */}
            <div className="pt-4 border-t border-white/10 text-[10px] font-mono text-white/40 space-y-1">
              <div className="flex justify-between">
                <span>Model Orchestrator:</span>
                <span className="text-white/70">LangGraph v0.2</span>
              </div>
              <div className="flex justify-between">
                <span>Context Vectors:</span>
                <span className="text-white/70">Supabase pgvector</span>
              </div>
            </div>
          </div>
        </aside>

        {/* =========================================
            CENTER PANE: Execution Feed & Command Bar (col-span-6)
            ========================================= */}
        <main className="col-span-6 h-full flex flex-col gap-4 overflow-hidden relative">
          <div className="flex-1 bg-white/5 border border-white/10 backdrop-blur-md rounded-2xl p-5 flex flex-col overflow-hidden shadow-2xl relative">
            {/* Center Header */}
            <div className="flex items-center justify-between pb-3 border-b border-white/10 shrink-0">
              <div className="flex items-center gap-2">
                <Terminal className="w-4 h-4 text-white/70" />
                <h2 className="text-xs uppercase font-mono tracking-wider font-semibold text-white/90">
                  Autonomous Execution Thread
                </h2>
              </div>
              <span className="text-[10px] font-mono text-white/40">
                {messages.length} DISPATCH{messages.length === 1 ? "" : "ES"}
              </span>
            </div>

            {/* Execution Messages Feed */}
            <div className="flex-1 overflow-y-auto no-scrollbar py-4 space-y-4 pr-1">
              <AnimatePresence initial={false}>
                {messages.map((msg) => (
                  <motion.div
                    key={msg.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.25, ease: "easeOut" }}
                    className={`flex flex-col space-y-1.5 p-4 rounded-xl transition-colors ${
                      msg.sender === "user"
                        ? "bg-white/[0.08] border border-white/15 ml-10 shadow-lg"
                        : "bg-white/[0.02] border border-white/10 mr-10 shadow-md backdrop-blur-sm"
                    }`}
                  >
                    <div className="flex items-center justify-between text-xs text-white/40">
                      <div className="flex items-center gap-1.5 font-medium">
                        {msg.sender === "user" ? (
                          <>
                            <User className="w-3.5 h-3.5 text-white/70" />
                            <span className="text-white/90 font-sans">Executive Directive</span>
                          </>
                        ) : (
                          <>
                            <Bot className="w-3.5 h-3.5 text-emerald-400" />
                            <span className="text-emerald-300 font-sans">Jerry Response</span>
                          </>
                        )}
                      </div>
                      <span className="font-mono text-[10px] text-white/40 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {msg.timestamp}
                      </span>
                    </div>

                    <p
                      className={`text-sm leading-relaxed ${
                        msg.sender === "user"
                          ? "text-white font-sans font-normal"
                          : "text-white/90 font-mono text-xs sm:text-sm bg-black/30 p-3 rounded-lg border border-white/5 whitespace-pre-wrap"
                      }`}
                    >
                      {msg.text}
                    </p>
                  </motion.div>
                ))}
              </AnimatePresence>

              {isProcessing && (
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex items-center gap-3 p-3.5 bg-white/[0.02] border border-white/10 rounded-xl mr-10 text-xs text-white/70 font-mono"
                >
                  <Loader2 className="w-4 h-4 animate-spin text-emerald-400" />
                  <span>Synthesizing intent & routing to MCP execution pipeline...</span>
                </motion.div>
              )}
              <div ref={feedEndRef} />
            </div>

            {/* Quick Suggestions Chips */}
            <div className="shrink-0 pt-2 pb-1 flex flex-wrap gap-2">
              {[
                "Brief priority inbox",
                "Scan schedule for conflicts",
                "Generate executive digest",
              ].map((chip) => (
                <button
                  key={chip}
                  onClick={() => setCommand(chip)}
                  disabled={isProcessing}
                  className="px-2.5 py-1 rounded-md bg-white/[0.03] hover:bg-white/[0.08] border border-white/10 text-[11px] text-white/60 hover:text-white font-sans transition-all disabled:opacity-40 cursor-pointer"
                >
                  {chip}
                </button>
              ))}
            </div>

            {/* Floating Glassmorphic Command Bar */}
            <form onSubmit={handleCommandSubmit} className="shrink-0 pt-2 w-full">
              <div className="relative flex items-center w-full rounded-xl bg-white/10 backdrop-blur-xl border border-white/20 shadow-2xl transition-all duration-300 focus-within:border-white/40 focus-within:ring-2 focus-within:ring-white/30 focus-within:bg-white/[0.14] hover:border-white/30">
                <div className="pl-4 pr-2 text-white/50">
                  <Terminal className="w-4 h-4" />
                </div>
                <input
                  type="text"
                  value={command}
                  onChange={(e) => setCommand(e.target.value)}
                  placeholder="Awaiting your command..."
                  disabled={isProcessing}
                  className="w-full py-4 pr-14 pl-2 bg-transparent text-white placeholder-white/40 font-sans text-sm sm:text-base focus:outline-none tracking-normal disabled:opacity-50"
                />
                <button
                  type="submit"
                  aria-label="Send Directive"
                  className="absolute right-2.5 p-2 rounded-lg bg-white/10 hover:bg-white/20 text-white/70 hover:text-white transition-all duration-200 focus:outline-none disabled:opacity-30 disabled:pointer-events-none cursor-pointer"
                  disabled={!command.trim() || isProcessing}
                >
                  {isProcessing ? (
                    <Loader2 className="w-4 h-4 animate-spin text-white" />
                  ) : (
                    <Send className="w-4 h-4" />
                  )}
                </button>
              </div>
            </form>
          </div>
        </main>

        {/* =========================================
            RIGHT PANE: Executive Briefing (col-span-3)
            ========================================= */}
        <aside className="col-span-3 h-full flex flex-col gap-4 overflow-hidden">
          <div className="flex-1 bg-white/5 border border-white/10 backdrop-blur-md rounded-2xl p-5 flex flex-col justify-between overflow-y-auto no-scrollbar shadow-xl">
            <div className="space-y-6">
              {/* Section 1: Priority Communications */}
              <div className="space-y-3">
                <div className="flex items-center justify-between pb-2 border-b border-white/10">
                  <div className="flex items-center gap-2">
                    <Inbox className="w-4 h-4 text-sky-400" />
                    <h2 className="text-xl font-serif text-white font-normal">
                      Priority Communications
                    </h2>
                  </div>
                  <span className="text-[10px] font-mono text-sky-400 bg-sky-950/60 border border-sky-800/60 px-1.5 py-0.5 rounded">
                    3 UNREAD
                  </span>
                </div>

                <div className="space-y-2">
                  {[
                    {
                      sender: "Sarah Lin (Chief of Staff)",
                      subject: "Q3 Board Strategy Deck Review",
                      time: "10:02 AM",
                      urgent: true,
                    },
                    {
                      sender: "David Marcus (Founders Fund)",
                      subject: "Follow-up: Series B Allocation Terms",
                      time: "09:41 AM",
                      urgent: false,
                    },
                    {
                      sender: "Engineering Ops",
                      subject: "Incident Report: EU CDN Latency Spike",
                      time: "08:15 AM",
                      urgent: false,
                    },
                  ].map((email, idx) => (
                    <div
                      key={idx}
                      className="p-2.5 rounded-xl bg-white/[0.03] hover:bg-white/10 border border-white/5 hover:border-white/15 transition-all duration-150 cursor-pointer group"
                    >
                      <div className="flex items-center justify-between text-[11px] text-white/50 mb-1">
                        <span className="font-medium text-white/80 group-hover:text-white truncate max-w-[150px]">
                          {email.sender}
                        </span>
                        <span className="font-mono text-[10px]">{email.time}</span>
                      </div>
                      <p className="text-xs text-white/70 group-hover:text-white/90 line-clamp-1">
                        {email.subject}
                      </p>
                      {email.urgent && (
                        <span className="inline-block mt-1.5 text-[9px] font-mono font-semibold text-rose-400 bg-rose-950/40 border border-rose-800/40 px-1.5 py-0.2 rounded">
                          ACTION REQUIRED
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Section 2: Agenda */}
              <div className="space-y-3">
                <div className="flex items-center justify-between pb-2 border-b border-white/10">
                  <div className="flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-emerald-400" />
                    <h2 className="text-xl font-serif text-white font-normal">Agenda</h2>
                  </div>
                  <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/60 border border-emerald-800/60 px-1.5 py-0.5 rounded">
                    TODAY
                  </span>
                </div>

                <div className="space-y-2">
                  {[
                    {
                      title: "Product Roadmap Sync",
                      time: "11:00 AM - 11:45 AM",
                      type: "Internal",
                      status: "Upcoming",
                    },
                    {
                      title: "Partnership Call w/ Stripe",
                      time: "02:00 PM - 02:30 PM",
                      type: "External",
                      status: "Pending prep",
                    },
                    {
                      title: "Executive Committee Check-in",
                      time: "04:30 PM - 05:00 PM",
                      type: "Governance",
                      status: "Scheduled",
                    },
                  ].map((event, idx) => (
                    <div
                      key={idx}
                      className="p-2.5 rounded-xl bg-white/[0.03] hover:bg-white/10 border border-white/5 hover:border-white/15 transition-all duration-150 cursor-pointer group"
                    >
                      <div className="flex items-center justify-between text-[11px] text-white/50 mb-1">
                        <span className="font-mono text-[10px] text-emerald-400">
                          {event.time}
                        </span>
                        <span className="text-[9px] uppercase tracking-wider font-mono text-white/40">
                          {event.type}
                        </span>
                      </div>
                      <p className="text-xs font-medium text-white/80 group-hover:text-white">
                        {event.title}
                      </p>
                      <div className="flex items-center gap-1 mt-1 text-[10px] text-white/50 font-mono">
                        <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                        <span>{event.status}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Quick Sync Notice */}
            <div className="pt-4 border-t border-white/10 flex items-center justify-between text-[10px] font-mono text-white/40">
              <span>Synced with Google Workspace</span>
              <span className="text-emerald-400">LIVE</span>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
