"use client"

import { AgentStats } from "@/lib/types"
import { MessageCircleQuestion, Brain, Route, Target, Shield } from "lucide-react"

interface MetricsBarProps {
  leftStats: AgentStats
  rightStats: AgentStats
}

function Stat({ icon: Icon, label, left, right }: {
  icon: React.ElementType; label: string; left: string; right: string
}) {
  return (
    <div className="flex flex-col items-center gap-0.5 px-3">
      <div className="flex items-center gap-1 text-[10px] text-neutral-400 uppercase tracking-widest">
        <Icon className="w-3 h-3" />
        {label}
      </div>
      <div className="flex items-center gap-1.5">
        <span className="text-xs font-semibold tabular-nums text-red-500">{left}</span>
        <span className="text-neutral-300 text-[10px]">|</span>
        <span className="text-xs font-semibold tabular-nums text-teal-600">{right}</span>
      </div>
    </div>
  )
}

export function MetricsBar({ leftStats, rightStats }: MetricsBarProps) {
  return (
    <div className="w-full border-b border-neutral-200/80 glass shrink-0">
      <div className="flex items-center justify-center gap-6 px-4 py-2 max-w-screen-2xl mx-auto">
        <div className="flex items-center gap-1.5 text-[9px] uppercase tracking-[0.2em] text-red-400">
          <span className="w-1.5 h-1.5 rounded-full bg-red-400" />
          Standard
        </div>

        <div className="w-px h-6 bg-neutral-200" />

        <Stat icon={MessageCircleQuestion} label="Questions" left={String(leftStats.questionsAsked)} right={String(rightStats.questionsAsked)} />
        <Stat icon={Brain} label="Facts" left={String(leftStats.factsRecalled)} right={String(rightStats.factsRecalled)} />
        <Stat icon={Route} label="Hops" left={String(leftStats.graphHops)} right={String(rightStats.graphHops)} />
        <Stat icon={Target} label="Relevance" left={`${leftStats.resultRelevance}%`} right={`${rightStats.resultRelevance}%`} />

        <div className="flex items-center gap-1.5">
          <Shield className="w-3 h-3 text-neutral-300" />
          <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
            leftStats.confidence === "HIGH" ? "text-teal-700 bg-teal-50"
            : leftStats.confidence === "MEDIUM" ? "text-amber-700 bg-amber-50"
            : "text-red-500 bg-red-50"
          }`}>{leftStats.confidence}</span>
          <span className="text-neutral-300">/</span>
          <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
            rightStats.confidence === "HIGH" ? "text-teal-700 bg-teal-50"
            : rightStats.confidence === "MEDIUM" ? "text-amber-700 bg-amber-50"
            : "text-red-500 bg-red-50"
          }`}>{rightStats.confidence}</span>
        </div>

        <div className="w-px h-6 bg-neutral-200" />

        <div className="flex items-center gap-1.5 text-[9px] uppercase tracking-[0.2em] text-teal-600">
          Neo4j
          <span className="w-1.5 h-1.5 rounded-full bg-teal-500 animate-pulse" />
        </div>
      </div>
    </div>
  )
}
