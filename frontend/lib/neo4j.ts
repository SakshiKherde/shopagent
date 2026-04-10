/**
 * Neo4j driver for frontend API routes.
 * Uses the neo4j-driver package for direct Cypher queries in Next.js API routes.
 */
import neo4j, { Driver } from "neo4j-driver"

let _driver: Driver | null = null

export function getDriver(): Driver {
  if (!_driver) {
    const uri = process.env.NEO4J_URI!
    const user = process.env.NEO4J_USERNAME!
    const password = process.env.NEO4J_PASSWORD!
    _driver = neo4j.driver(uri, neo4j.auth.basic(user, password))
  }
  return _driver
}

export async function runQuery<T = Record<string, unknown>>(
  cypher: string,
  params: Record<string, unknown> = {}
): Promise<T[]> {
  const driver = getDriver()
  const session = driver.session()
  try {
    const result = await session.run(cypher, params)
    return result.records.map((r) => r.toObject() as T)
  } finally {
    await session.close()
  }
}
