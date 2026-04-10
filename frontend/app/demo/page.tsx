"use client"

import { useState } from "react"
import { AgentPanel } from "@/components/AgentPanel"
import { MetricsBar } from "@/components/MetricsBar"
import { GraphViewer } from "@/components/GraphViewer"
import { DecisionTracePanel } from "@/components/DecisionTracePanel"
import { WhyGraphPanel } from "@/components/WhyGraphPanel"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { AgentStats } from "@/lib/types"
import { RotateCcw, Network, HelpCircle, GitBranch } from "lucide-react"

const DEFAULT_STATS: AgentStats = {
  elapsedSeconds: 0,
  questionsAsked: 0,
  factsRecalled: 0,
  graphHops: 0,
  resultRelevance: 0,
  confidence: "LOW",
}

export default function DemoPage() {
  const [leftConvId, setLeftConvId] = useState(() => crypto.randomUUID())
  const [rightConvId, setRightConvId] = useState(() => crypto.randomUUID())
  const [leftStats, setLeftStats] = useState<AgentStats>({ ...DEFAULT_STATS })
  const [rightStats, setRightStats] = useState<AgentStats>({ ...DEFAULT_STATS })

  async function handleReset() {
    setLeftStats({ ...DEFAULT_STATS })
    setRightStats({ ...DEFAULT_STATS })
    setLeftConvId(crypto.randomUUID())
    setRightConvId(crypto.randomUUID())
    try { await fetch("/api/agent/reset", { method: "POST" }) } catch { /* best-effort */ }
  }

  return (
    <div className="flex flex-col h-screen bg-[#f8f9fb] mesh-gradient text-neutral-900 overflow-hidden">
      {/* ── Header ── */}
      <header className="flex items-center justify-between px-5 py-2.5 border-b border-neutral-200/80 shrink-0 glass">
        <div className="flex items-center gap-3">
          <span className="text-base font-bold tracking-tight">
            <span className="text-neutral-800">Shop</span>
            <span className="bg-gradient-to-r from-teal-600 to-cyan-500 bg-clip-text text-transparent">Agent</span>
          </span>
        </div>

        <div className="flex items-center gap-4">
          <span className="text-neutral-400 text-[11px] hidden md:inline tracking-wide">
            Same model &middot; Same question &middot; Different data layer
          </span>
          <button
            onClick={handleReset}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg glass border border-neutral-200/80
                       text-neutral-500 hover:text-neutral-700 text-xs transition-all hover:border-neutral-300"
          >
            <RotateCcw className="w-3 h-3" />
            Reset
          </button>
        </div>
      </header>

      {/* ── Metrics Bar ── */}
      <MetricsBar leftStats={leftStats} rightStats={rightStats} />

      {/* ── Two chat panels ── */}
      <div className="flex-1 grid grid-cols-2 gap-3 p-3 min-h-0">
        <AgentPanel side="left" conversationId={leftConvId}
          onStatsUpdate={(s) => setLeftStats((prev) => ({ ...prev, questionsAsked: prev.questionsAsked + s.questionsAsked, factsRecalled: s.factsRecalled, graphHops: s.graphHops, resultRelevance: s.resultRelevance, confidence: s.confidence }))}
          onElapsedTick={() => {}} />
        <AgentPanel side="right" conversationId={rightConvId}
          onStatsUpdate={(s) => setRightStats((prev) => ({ ...prev, questionsAsked: prev.questionsAsked + s.questionsAsked, factsRecalled: s.factsRecalled, graphHops: s.graphHops, resultRelevance: s.resultRelevance, confidence: s.confidence }))}
          onElapsedTick={() => {}} />
      </div>

      {/* ── Bottom Tabs ── */}
      <div className="h-[320px] border-t border-neutral-200/80 shrink-0 bg-white/50">
        <Tabs defaultValue="why" className="h-full flex flex-col">
          <TabsList className="glass border-b border-neutral-200/80 rounded-none h-9 px-4 gap-1 shrink-0 justify-start w-full">
            <TabsTrigger value="graph"
              className="data-[state=active]:bg-teal-50 data-[state=active]:text-teal-700 text-neutral-400 text-xs gap-1.5 rounded-md px-3 py-1">
              <Network className="w-3 h-3" />
              Context Graph
            </TabsTrigger>
            <TabsTrigger value="trace"
              className="data-[state=active]:bg-violet-50 data-[state=active]:text-violet-700 text-neutral-400 text-xs gap-1.5 rounded-md px-3 py-1">
              <GitBranch className="w-3 h-3" />
              Decision Trace
            </TabsTrigger>
            <TabsTrigger value="why"
              className="data-[state=active]:bg-blue-50 data-[state=active]:text-blue-700 text-neutral-400 text-xs gap-1.5 rounded-md px-3 py-1">
              <HelpCircle className="w-3 h-3" />
              Why Graph?
            </TabsTrigger>
          </TabsList>

          <TabsContent value="graph" className="flex-1 m-0 min-h-0">
            <GraphViewer userId="alex" />
          </TabsContent>
          <TabsContent value="trace" className="flex-1 m-0 min-h-0 overflow-hidden">
            <DecisionTracePanel conversationId={rightConvId} />
          </TabsContent>
          <TabsContent value="why" className="flex-1 m-0 min-h-0 overflow-hidden">
            <WhyGraphPanel />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
