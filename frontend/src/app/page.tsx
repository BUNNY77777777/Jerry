export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8 text-center">
      <div className="max-w-2xl border border-slate-800 bg-slate-900/60 p-10 rounded-2xl backdrop-blur shadow-2xl">
        <div className="inline-flex items-center gap-2 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-emerald-400 bg-emerald-950/50 border border-emerald-800 rounded-full mb-6">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          Jerry Executive System Online
        </div>
        <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl text-white mb-4">
          Jerry AI Executive Agent
        </h1>
        <p className="text-base text-slate-400 mb-8 leading-relaxed">
          High-performance executive orchestration, memory-augmented context threads,
          governance approval queues, and MCP tool automation.
        </p>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-left text-xs text-slate-300">
          <div className="p-3 bg-slate-800/40 rounded-lg border border-slate-800">
            <span className="text-slate-500 block mb-1">Architecture</span>
            Next.js App Router
          </div>
          <div className="p-3 bg-slate-800/40 rounded-lg border border-slate-800">
            <span className="text-slate-500 block mb-1">Backend</span>
            FastAPI & LangGraph
          </div>
          <div className="p-3 bg-slate-800/40 rounded-lg border border-slate-800">
            <span className="text-slate-500 block mb-1">Vector Storage</span>
            Supabase + pgvector
          </div>
        </div>
      </div>
    </main>
  );
}
