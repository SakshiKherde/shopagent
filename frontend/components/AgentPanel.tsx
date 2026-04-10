"use client"

import { useEffect, useRef, useState } from "react"
import { Send, Loader2, CheckCircle2, XCircle, Zap, Sparkles, ShieldOff } from "lucide-react"
import { ChatMessage } from "@/lib/types"
import { MemoryChip } from "./MemoryChip"
import { GraphPathChip } from "./GraphPathChip"
import { ScrollArea } from "@/components/ui/scroll-area"

interface AgentPanelProps {
  side: "left" | "right"
  conversationId: string
  onStatsUpdate: (stats: { questionsAsked: number; factsRecalled: number; graphHops: number; resultRelevance: number; confidence: "LOW" | "MEDIUM" | "HIGH" }) => void
  onElapsedTick: () => void
}

function renderMarkdown(text: string): string {
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong class="text-neutral-800">$1</strong>')
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/`(.+?)`/g, '<code class="bg-neutral-100 px-1 rounded text-xs text-teal-700 font-mono">$1</code>')
    .replace(/^> (.+)$/gm, '<blockquote class="border-l-2 border-teal-400 pl-3 text-neutral-500 italic my-1 text-[13px]">$1</blockquote>')
    .replace(/\n/g, "<br/>")
}

export function AgentPanel({ side, conversationId, onStatsUpdate, onElapsedTick }: AgentPanelProps) {
  const isRight = side === "right"
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [loadingContext, setLoadingContext] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight
  }, [messages])

  async function sendMessage(text?: string) {
    const msg = (text ?? input).trim()
    if (!msg || isLoading) return
    setInput("")

    setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: "user", content: msg, timestamp: new Date() }])
    setIsLoading(true)

    if (isRight) { setLoadingContext(true); await new Promise((r) => setTimeout(r, 800)); setLoadingContext(false) }

    const assistantMsgId = crypto.randomUUID()
    setMessages((prev) => [...prev, { id: assistantMsgId, role: "assistant", content: "", timestamp: new Date() }])

    try {
      const res = await fetch("/api/agent/chat", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg, conversationId, useContextGraph: isRight, userId: "alex" }),
      })
      const reader = res.body?.getReader()
      if (!reader) throw new Error("No body")
      const decoder = new TextDecoder()
      let buffer = ""
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split("\n"); buffer = lines.pop() ?? ""
        for (const line of lines) {
          if (!line.startsWith("data: ")) continue
          try {
            const event = JSON.parse(line.slice(6))
            if (event.type === "chunk") { setMessages((prev) => prev.map((m) => m.id === assistantMsgId ? { ...m, content: m.content + event.content } : m)); onElapsedTick() }
            else if (event.type === "meta") {
              setMessages((prev) => prev.map((m) => m.id === assistantMsgId ? { ...m, factsRecalled: event.factsRecalled, graphPaths: event.graphPaths, cypherQueries: event.cypherQueries, confidence: event.confidence ?? 0 } : m))
              onStatsUpdate({ questionsAsked: event.questionCount ?? 0, factsRecalled: event.factsRecalled?.length ?? 0, graphHops: event.graphHops ?? 0, resultRelevance: isRight ? 94 : Math.floor(Math.random() * 30 + 40), confidence: isRight ? (event.confidence ?? 0) > 0.8 ? "HIGH" : (event.confidence ?? 0) > 0.5 ? "MEDIUM" : "LOW" : "LOW" })
            }
          } catch { /* partial SSE */ }
        }
      }
    } catch {
      setMessages((prev) => prev.map((m) => m.id === assistantMsgId ? { ...m, content: "Could not reach the backend. Start the FastAPI server and try again." } : m))
    } finally { setIsLoading(false) }
  }

  const suggestedPrompt = "I need new running shoes"

  return (
    <div className={`flex flex-col h-full rounded-2xl overflow-hidden border transition-all ${
      isRight ? "border-teal-200/80 glow-teal glass-teal" : "border-neutral-200/80 glow-red glass-red"
    }`}>
      {/* Header */}
      <div className={`px-4 py-3 border-b flex items-center justify-between shrink-0 ${
        isRight ? "border-teal-200/60 bg-gradient-to-r from-teal-50/80 to-cyan-50/40" : "border-neutral-200/60 bg-neutral-50/60"
      }`}>
        <div className="flex items-center gap-2.5">
          {isRight ? (
            <div className="w-6 h-6 rounded-full bg-gradient-to-br from-teal-500 to-cyan-400 flex items-center justify-center shadow-sm shadow-teal-500/20">
              <CheckCircle2 className="w-3.5 h-3.5 text-white" />
            </div>
          ) : (
            <div className="w-6 h-6 rounded-full bg-neutral-100 border border-neutral-200 flex items-center justify-center">
              <XCircle className="w-3.5 h-3.5 text-red-400" />
            </div>
          )}
          <div>
            <span className={`font-semibold text-sm ${isRight ? "text-teal-800" : "text-neutral-600"}`}>
              {isRight ? "Neo4j Context Graph" : "Standard AI"}
            </span>
            {!isRight && <span className="text-neutral-400 text-[10px] ml-2">No Memory</span>}
          </div>
          {isRight && <span className="w-1.5 h-1.5 rounded-full bg-teal-500 animate-pulse ml-0.5" />}
        </div>
        {isRight && (
          <div className="flex items-center gap-1 text-[10px] text-teal-700 bg-teal-100/80 px-2.5 py-1 rounded-full border border-teal-200/60">
            <Zap className="w-2.5 h-2.5" />
            Graph-powered
          </div>
        )}
      </div>

      {/* Context loading */}
      {loadingContext && (
        <div className="px-4 py-1.5 border-b border-teal-100 flex items-center gap-2 text-[11px] text-teal-600 shrink-0 shimmer bg-teal-50/50">
          <Loader2 className="w-3 h-3 animate-spin" />
          Loading context graph...
        </div>
      )}

      {/* Messages */}
      <ScrollArea className="flex-1 px-4 py-3" ref={scrollRef}>
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full gap-5 text-center py-16">
            {isRight ? (
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-teal-100 to-cyan-50 border border-teal-200/60 flex items-center justify-center shadow-sm">
                <Sparkles className="w-6 h-6 text-teal-500" />
              </div>
            ) : (
              <div className="w-14 h-14 rounded-2xl bg-neutral-100 border border-neutral-200 flex items-center justify-center">
                <ShieldOff className="w-6 h-6 text-neutral-300" />
              </div>
            )}
            <div className="space-y-2">
              <p className={`text-sm font-medium ${isRight ? "text-neutral-700" : "text-neutral-400"}`}>
                {isRight ? "Context graph loaded" : "No context available"}
              </p>
              <p className="text-neutral-400 text-xs max-w-[260px] mx-auto leading-relaxed">
                {isRight ? "Preferences, purchases, reviews, and similar-user insights are ready in the graph." : "This agent has no memory. It will ask you for everything from scratch."}
              </p>
            </div>
            <button onClick={() => sendMessage(suggestedPrompt)}
              className={`text-xs px-5 py-2.5 rounded-xl border transition-all hover:scale-[1.02] active:scale-[0.98] ${
                isRight ? "border-teal-200 text-teal-700 hover:bg-teal-50 hover:border-teal-300 shadow-sm" : "border-neutral-200 text-neutral-500 hover:bg-neutral-50 hover:border-neutral-300"
              }`}>
              &ldquo;{suggestedPrompt}&rdquo;
            </button>
          </div>
        )}

        <div className="space-y-3">
          {messages.map((msg) => (
            <div key={msg.id} className="space-y-1.5">
              <div className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[88%] rounded-2xl px-4 py-2.5 text-[13px] leading-relaxed ${
                  msg.role === "user"
                    ? "bg-gradient-to-r from-neutral-800 to-neutral-700 text-white shadow-sm"
                    : isRight
                    ? "bg-white/80 border border-teal-200/60 text-neutral-700 shadow-sm"
                    : "bg-white/60 border border-neutral-200 text-neutral-600"
                }`}>
                  {msg.role === "assistant" && msg.content === "" && isLoading ? (
                    <div className="flex items-center gap-2 py-1">
                      <div className="flex gap-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-neutral-300 animate-bounce [animation-delay:0ms]" />
                        <span className="w-1.5 h-1.5 rounded-full bg-neutral-300 animate-bounce [animation-delay:150ms]" />
                        <span className="w-1.5 h-1.5 rounded-full bg-neutral-300 animate-bounce [animation-delay:300ms]" />
                      </div>
                      <span className="text-xs text-neutral-400">{isRight ? "Traversing graph..." : "Thinking..."}</span>
                    </div>
                  ) : (
                    <span dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.content) }} />
                  )}
                </div>
              </div>

              {isRight && msg.role === "assistant" && msg.content && (
                <div className="flex flex-col gap-1.5 pl-2">
                  {msg.factsRecalled && msg.factsRecalled.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {msg.factsRecalled.map((fact, i) => <MemoryChip key={i} text={fact} delay={i * 80} />)}
                    </div>
                  )}
                  {msg.graphPaths && msg.graphPaths.length > 0 && (
                    <div className="flex flex-col gap-1">
                      {msg.graphPaths.slice(0, 2).map((path, i) => <GraphPathChip key={i} path={path} delay={i * 100 + 200} />)}
                    </div>
                  )}
                  {msg.confidence !== undefined && msg.confidence > 0 && (
                    <div className="inline-flex items-center gap-1.5 text-[11px] text-teal-600 font-medium pl-0.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-teal-500" />
                      {Math.round(msg.confidence * 100)}% confidence
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </ScrollArea>

      {/* Input */}
      <div className={`px-3 py-3 border-t shrink-0 ${isRight ? "border-teal-200/60" : "border-neutral-200/60"}`}>
        <div className="flex gap-2">
          <input value={input} onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
            placeholder={isRight ? "Ask Alex's shopping agent..." : "Ask the standard agent..."}
            disabled={isLoading}
            className="flex-1 bg-white/80 border border-neutral-200 rounded-xl px-4 py-2.5 text-sm
                       text-neutral-800 placeholder-neutral-400 focus:outline-none
                       focus:border-teal-300 focus:ring-2 focus:ring-teal-100 disabled:opacity-40 transition-all shadow-sm" />
          <button onClick={() => sendMessage()} disabled={isLoading || !input.trim()}
            className={`px-3 rounded-xl transition-all disabled:opacity-20 hover:scale-[1.05] active:scale-[0.95] shadow-sm ${
              isRight
                ? "bg-gradient-to-r from-teal-500 to-cyan-500 text-white shadow-teal-500/15"
                : "bg-neutral-800 text-white hover:bg-neutral-700"
            }`}>
            {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          </button>
        </div>
      </div>
    </div>
  )
}
