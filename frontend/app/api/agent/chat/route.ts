import { NextRequest } from "next/server"

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"

export async function POST(req: NextRequest) {
  const body = await req.json()

  const upstream = await fetch(`${BACKEND_URL}/api/agent/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })

  if (!upstream.ok) {
    return new Response(JSON.stringify({ error: "Backend error" }), {
      status: upstream.status,
      headers: { "Content-Type": "application/json" },
    })
  }

  // Proxy the SSE stream
  return new Response(upstream.body, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
      "X-Accel-Buffering": "no",
    },
  })
}
