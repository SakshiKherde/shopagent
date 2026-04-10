export interface ChatMessage {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
  factsRecalled?: string[]
  graphPaths?: string[]
  cypherQueries?: string[]
  confidence?: number
}

export interface AgentStats {
  elapsedSeconds: number
  questionsAsked: number
  factsRecalled: number
  graphHops: number
  resultRelevance: number
  confidence: "LOW" | "MEDIUM" | "HIGH"
}

export interface GraphNode {
  id: string
  labels: string[]
  properties: Record<string, unknown>
}

export interface GraphEdge {
  id: string
  type: string
  from: string
  to: string
}

export interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

export interface DecisionTrace {
  id: string
  toolName: string
  cypherQuery: string
  reasoning: string
  timestamp: string
  durationMs: number
}

export interface ChatApiResponse {
  type: "chunk" | "meta" | "done" | "error"
  content?: string
  factsRecalled?: string[]
  graphPaths?: string[]
  cypherQueries?: string[]
  confidence?: number
  questionCount?: number
  graphHops?: number
  message?: string
}
