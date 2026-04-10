import Link from "next/link";
import { ArrowRight, Zap, Network, Brain } from "lucide-react";

export default function Home() {
  return (
    <main className="min-h-screen bg-[#f8f9fb] mesh-gradient flex flex-col items-center justify-center px-6 py-20 relative overflow-hidden">
      {/* Background glow orbs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-teal-400/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-violet-400/8 rounded-full blur-[100px] pointer-events-none" />

      <div className="max-w-2xl text-center space-y-8 relative z-10">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-teal-200 bg-teal-50 text-xs text-teal-700 mb-4">
          <span className="w-1.5 h-1.5 rounded-full bg-teal-500 animate-pulse" />
          Neo4j AI Launch
        </div>

        <h1 className="text-5xl md:text-6xl font-black tracking-tight">
          <span className="text-neutral-800">Shop</span>
          <span className="bg-gradient-to-r from-teal-600 to-cyan-500 bg-clip-text text-transparent">Agent</span>
        </h1>

        <p className="text-neutral-500 text-lg leading-relaxed max-w-lg mx-auto">
          What happens when an AI agent has{" "}
          <span className="text-red-500 font-semibold">no memory</span> versus one backed by a{" "}
          <span className="bg-gradient-to-r from-teal-600 to-cyan-500 bg-clip-text text-transparent font-semibold">
            Neo4j context graph
          </span>
          ?
        </p>

        <p className="text-neutral-400 text-sm tracking-wide uppercase">
          Same model &middot; Same question &middot; Completely different experience
        </p>

        <div className="flex flex-wrap items-center justify-center gap-3">
          {[
            { icon: Brain, label: "Google ADK" },
            { icon: Network, label: "Neo4j Aura" },
            { icon: Zap, label: "MCP Serverless" },
          ].map(({ icon: Icon, label }) => (
            <div
              key={label}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-full glass border border-neutral-200/80 text-neutral-600 text-xs"
            >
              <Icon className="w-3.5 h-3.5 text-teal-600" />
              {label}
            </div>
          ))}
        </div>

        <Link
          href="/demo"
          className="inline-flex items-center gap-2 px-8 py-3.5 rounded-xl
                     bg-gradient-to-r from-teal-600 to-cyan-500 hover:from-teal-500 hover:to-cyan-400
                     text-white font-semibold transition-all text-base shadow-lg shadow-teal-500/20
                     hover:shadow-teal-400/30 hover:scale-[1.02] active:scale-[0.98]"
        >
          Launch Demo
          <ArrowRight className="w-4 h-4" />
        </Link>

        <p className="text-neutral-400 text-xs pt-4">
          Next.js &middot; FastAPI &middot; Google ADK &middot; @neo4j/mcp-server
        </p>
      </div>
    </main>
  );
}
