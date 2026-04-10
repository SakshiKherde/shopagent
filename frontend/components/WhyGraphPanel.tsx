"use client"

import { AlertTriangle, CheckCircle2, Zap } from "lucide-react"

const CYPHER_QUERY = `MATCH (alex:User {id:'alex'})-[:PURCHASED]->(s:Shoe)
      <-[:PURCHASED]-(similar:User {footWidth:'narrow'})
      -[:PURCHASED]->(candidate:Shoe)
      -[:HAS_REVIEW]->(r:Review {authorWidth:'narrow'})
      -[:CONTAINS_INSIGHT]->(i:ReviewInsight {sentiment:'positive'})
WHERE NOT (alex)-[:PURCHASED|REJECTED]->(candidate)
  AND candidate.widthOptions CONTAINS 'narrow'
  AND candidate.inStock = true
RETURN candidate.brand, candidate.model,
       count(i) AS narrowPositiveMentions,
       collect(i.quote)[..3] AS topQuotes
ORDER BY narrowPositiveMentions DESC LIMIT 3`

const WITHOUT_STEPS = [
  { n: 1, title: "Vector search for similar users", desc: "Approximate nearest-neighbor — no guarantee of matching foot width." },
  { n: 2, title: "Separate purchase lookup", desc: "Second round-trip for each similar user's purchases." },
  { n: 3, title: "Separate review lookup", desc: "Third round-trip for each candidate shoe's reviews." },
  { n: 4, title: "Keyword filter for 'narrow'", desc: "String scan or embedding re-rank for narrow-relevant text." },
  { n: 5, title: "Cross-reference reject list", desc: "Another query + programmatic filtering." },
  { n: 6, title: "Manual scoring", desc: "Application-side sort, dedup, and rank." },
]

function SyntaxHighlightedCypher() {
  const lines = CYPHER_QUERY.split("\n")
  return (
    <pre className="text-[11px] leading-relaxed overflow-x-auto p-3 bg-[#1e1e2e] rounded-xl text-neutral-300 border border-neutral-200/10 shadow-sm">
      {lines.map((line, i) => {
        const highlighted = line
          .replace(/\b(MATCH|WHERE|RETURN|ORDER BY|LIMIT|NOT|AND|CONTAINS)\b/g, (m) => `<span class="text-blue-400 font-semibold">${m}</span>`)
          .replace(/\[:([A-Z_]+)\]/g, (_, rel) => `[<span class="text-orange-400">:${rel}</span>]`)
          .replace(/:([A-Z][a-zA-Z]+)/g, (_, lbl) => `:<span class="text-teal-300">${lbl}</span>`)
          .replace(/'([^']+)'/g, (_, s) => `'<span class="text-green-400">${s}</span>'`)
          .replace(/\b(count|collect)\b/g, (m) => `<span class="text-yellow-300">${m}</span>`)
        return <div key={i} dangerouslySetInnerHTML={{ __html: highlighted }} />
      })}
    </pre>
  )
}

export function WhyGraphPanel() {
  return (
    <div className="h-full overflow-y-auto p-5 space-y-5 bg-white/50">
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_auto_1fr] gap-5 items-start">
        {/* Without graph */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-3.5 h-3.5 text-red-500" />
            <h3 className="text-xs font-bold text-red-500 uppercase tracking-wider">Without graph — 6 steps</h3>
          </div>
          <div className="space-y-2">
            {WITHOUT_STEPS.map((step) => (
              <div key={step.n} className="flex gap-2.5 items-start">
                <span className="w-5 h-5 rounded-md bg-red-50 border border-red-200 flex items-center justify-center text-[10px] font-bold text-red-500 shrink-0 mt-0.5">
                  {step.n}
                </span>
                <div>
                  <p className="text-xs font-medium text-neutral-700">{step.title}</p>
                  <p className="text-[11px] text-neutral-400 mt-0.5">{step.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Divider */}
        <div className="hidden lg:flex flex-col items-center pt-8">
          <div className="w-px h-full bg-gradient-to-b from-red-200 via-neutral-200 to-teal-200 min-h-[200px]" />
        </div>

        {/* With graph */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-3.5 h-3.5 text-teal-600" />
            <h3 className="text-xs font-bold text-teal-600 uppercase tracking-wider">With Neo4j — 1 query</h3>
          </div>
          <SyntaxHighlightedCypher />
          <div className="rounded-xl bg-teal-50/80 border border-teal-200/60 p-3 text-[11px] text-teal-700 space-y-0.5">
            <ul className="space-y-0.5 list-none">
              <li className="flex items-center gap-1.5"><span className="text-teal-500 font-bold">+</span> Single traversal across 5 node types</li>
              <li className="flex items-center gap-1.5"><span className="text-teal-500 font-bold">+</span> Exact matches at the graph level</li>
              <li className="flex items-center gap-1.5"><span className="text-teal-500 font-bold">+</span> Full provenance in the query result</li>
              <li className="flex items-center gap-1.5"><span className="text-teal-500 font-bold">+</span> Zero application-side stitching</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Callout */}
      <div className="rounded-xl bg-gradient-to-r from-teal-50 to-cyan-50 border border-teal-200/60 p-4 flex items-start gap-3 shadow-sm">
        <Zap className="w-5 h-5 text-teal-600 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <p className="text-neutral-700 text-xs leading-relaxed">
            <span className="text-red-500 font-semibold">6 round-trips</span> in a vector database →{" "}
            <span className="text-teal-700 font-semibold">1 graph traversal</span> in Neo4j.{" "}
            Connected via{" "}
            <code className="bg-white px-1 rounded text-[10px] text-teal-700 font-mono border border-teal-200/60">@neo4j/mcp-server</code>{" "}
            — 10 lines of Python.
          </p>
          <p className="text-neutral-400 text-[11px] italic">
            &ldquo;Same model on both sides. The difference is the data layer.&rdquo;
          </p>
        </div>
      </div>
    </div>
  )
}
