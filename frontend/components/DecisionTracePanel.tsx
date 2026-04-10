"use client"

import { useEffect, useState } from "react"
import { DecisionTrace } from "@/lib/types"
import { ChevronDown, ChevronRight, Database, Loader2 } from "lucide-react"

function TraceRow({ trace }: { trace: DecisionTrace }) {
  const [expanded, setExpanded] = useState(false)
  const ts = new Date(trace.timestamp).toLocaleTimeString()

  return (
    <div className="border border-neutral-200/80 rounded-xl overflow-hidden shadow-sm">
      <button onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-3 px-4 py-2.5 bg-white/60 hover:bg-white text-left transition-all">
        {expanded ? <ChevronDown className="w-3 h-3 text-neutral-400 shrink-0" /> : <ChevronRight className="w-3 h-3 text-neutral-400 shrink-0" />}
        <span className="text-neutral-400 text-[11px] font-mono shrink-0 w-16">{ts}</span>
        <span className="text-violet-600 text-[11px] font-mono shrink-0 bg-violet-50 px-2 py-0.5 rounded-md border border-violet-200/80">
          {trace.toolName}
        </span>
        <span className="text-neutral-500 text-[11px] truncate flex-1 font-mono">{trace.cypherQuery?.substring(0, 50)}...</span>
        <span className="text-neutral-400 text-[11px] shrink-0 font-mono">{trace.durationMs}ms</span>
      </button>
      {expanded && (
        <div className="border-t border-neutral-200/60 p-4 space-y-3 bg-white/80">
          <div>
            <div className="text-[9px] text-neutral-400 uppercase tracking-widest mb-1.5">Cypher Query</div>
            <pre className="bg-[#1e1e2e] rounded-xl p-3 text-[11px] text-green-300 overflow-x-auto whitespace-pre-wrap shadow-sm">{trace.cypherQuery}</pre>
          </div>
          <div>
            <div className="text-[9px] text-neutral-400 uppercase tracking-widest mb-1.5">Reasoning</div>
            <p className="text-xs text-neutral-600">{trace.reasoning}</p>
          </div>
        </div>
      )}
    </div>
  )
}

export function DecisionTracePanel({ conversationId }: { conversationId: string | null }) {
  const [traces, setTraces] = useState<DecisionTrace[]>([])
  const [loading, setLoading] = useState(false)

  async function loadTraces() {
    if (!conversationId) return
    setLoading(true)
    try { const res = await fetch(`/api/graph/trace/${conversationId}`); const data = await res.json(); setTraces(data.traces || []) }
    catch { /* ignore */ } finally { setLoading(false) }
  }

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { loadTraces(); const interval = setInterval(loadTraces, 5000); return () => clearInterval(interval) }, [conversationId])

  return (
    <div className="h-full flex flex-col p-4 gap-3 bg-white/50">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Database className="w-4 h-4 text-violet-500" />
          <span className="text-sm font-semibold text-neutral-700">Decision Trace</span>
          <span className="text-violet-600 text-[11px] font-mono bg-violet-50 px-1.5 py-0.5 rounded border border-violet-200/80">{traces.length}</span>
        </div>
        <button onClick={loadTraces} className="text-[11px] text-teal-600 hover:text-teal-500 transition-colors">Refresh</button>
      </div>

      <div className="flex-1 overflow-y-auto space-y-1.5">
        {loading && traces.length === 0 && (
          <div className="flex items-center gap-2 text-neutral-400 text-xs p-4">
            <Loader2 className="w-3.5 h-3.5 animate-spin" /> Loading traces...
          </div>
        )}
        {!loading && traces.length === 0 && (
          <div className="flex flex-col items-center justify-center gap-3 py-12 text-center">
            <div className="w-12 h-12 rounded-2xl bg-neutral-50 border border-neutral-200 flex items-center justify-center">
              <Database className="w-5 h-5 text-neutral-300" />
            </div>
            <p className="text-neutral-400 text-xs">No traces yet</p>
            <p className="text-neutral-400 text-[11px] max-w-[200px]">Traces appear as the context agent runs Cypher queries.</p>
          </div>
        )}
        {traces.map((trace) => <TraceRow key={trace.id} trace={trace} />)}
      </div>
    </div>
  )
}
