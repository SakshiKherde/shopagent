const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"

export async function POST() {
  const res = await fetch(`${BACKEND_URL}/api/seed`, { method: "POST" })
  const data = await res.json()
  return Response.json(data)
}
