"use client"

import { GitBranch } from "lucide-react"

export function GraphPathChip({ path, delay = 0 }: { path: string; delay?: number }) {
  const parts = path.split(/\s*→\s*/)
  return (
    <div
      className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px]
                 bg-violet-50 border border-violet-200/80 text-violet-700 flex-wrap shadow-sm"
      style={{ animationDelay: `${delay}ms`, animation: "count-up 0.3s ease-out both" }}
    >
      <GitBranch className="w-3 h-3 shrink-0 text-violet-500" />
      {parts.map((part, i) => (
        <span key={i} className="flex items-center gap-1">
          <span className="font-medium">{part}</span>
          {i < parts.length - 1 && <span className="text-violet-400">→</span>}
        </span>
      ))}
    </div>
  )
}
