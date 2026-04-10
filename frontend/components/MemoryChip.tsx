"use client"

import { Brain } from "lucide-react"

export function MemoryChip({ text, delay = 0 }: { text: string; delay?: number }) {
  return (
    <div
      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium
                 bg-teal-50 border border-teal-200/80 text-teal-700 shadow-sm"
      style={{ animationDelay: `${delay}ms`, animation: "count-up 0.3s ease-out both" }}
    >
      <Brain className="w-3 h-3 shrink-0 text-teal-500" />
      <span>{text}</span>
    </div>
  )
}
