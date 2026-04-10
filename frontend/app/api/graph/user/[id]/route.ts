import { NextRequest } from "next/server"

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"

export async function GET(
  _req: NextRequest,
  { params }: { params: { id: string } }
) {
  const res = await fetch(`${BACKEND_URL}/api/graph/user/${params.id}`)
  const data = await res.json()
  return Response.json(data)
}
