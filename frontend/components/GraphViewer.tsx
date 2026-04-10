"use client"

/**
 * GraphViewer — D3 force-directed graph visualization.
 *
 * NOTE: This component uses D3 for rendering. In production, you can swap
 * the canvas renderer for Neo4j NVL (@neo4j/nvl) by loading the library
 * from the Neo4j CDN and replacing the D3 simulation with:
 *
 *   const nvl = new NVL(containerRef.current, nodes, edges, {
 *     renderer: 'canvas',
 *     layout: 'force',
 *   })
 *
 * NVL is a licensed library available at:
 *   https://neo4j.com/product/graph-data-science/graph-visualization/
 */

import { useEffect, useRef, useState } from "react"
import * as d3 from "d3"
import { GraphData, GraphNode } from "@/lib/types"
import { Loader2, RefreshCw, Network } from "lucide-react"

const NODE_COLORS: Record<string, string> = {
  User: "#00BCD4",
  Shoe: "#2196F3",
  Review: "#FF9800",
  ReviewInsight: "#FFC107",
  DecisionTrace: "#9C27B0",
  Recommendation: "#4CAF50",
  Conversation: "#E91E63",
  Message: "#607D8B",
}

function getNodeColor(labels: string[]): string {
  for (const label of labels) {
    if (NODE_COLORS[label]) return NODE_COLORS[label]
  }
  return "#9E9E9E"
}

function getNodeRadius(labels: string[]): number {
  if (labels.includes("User")) return 20
  if (labels.includes("Shoe")) return 14
  if (labels.includes("Review")) return 10
  return 8
}

interface NodeDatum extends d3.SimulationNodeDatum {
  id: string
  labels: string[]
  properties: Record<string, unknown>
}

interface LinkDatum extends d3.SimulationLinkDatum<NodeDatum> {
  type: string
}

interface GraphViewerProps {
  userId?: string
  highlightPath?: string[]
}

export function GraphViewer({ userId = "alex" }: GraphViewerProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const [graphData, setGraphData] = useState<GraphData | null>(null)
  const [loading, setLoading] = useState(false)
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function loadGraph() {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`/api/graph/user/${userId}`)
      if (!res.ok) throw new Error("Failed to load graph")
      const data = await res.json()
      if (!data || !Array.isArray(data.nodes)) throw new Error("Invalid graph data")
      setGraphData(data as GraphData)
    } catch {
      setError("Could not load graph. Is the backend running?")
    } finally {
      setLoading(false)
    }
  }

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { loadGraph() }, [userId])

  useEffect(() => {
    if (!graphData || !svgRef.current) return

    const svg = d3.select(svgRef.current)
    svg.selectAll("*").remove()

    const width = svgRef.current.clientWidth || 600
    const height = svgRef.current.clientHeight || 400

    const nodes: NodeDatum[] = graphData.nodes.map((n) => ({
      id: n.id,
      labels: n.labels,
      properties: n.properties,
    }))

    const nodeMap = new Map(nodes.map((n) => [n.id, n]))

    const links: LinkDatum[] = graphData.edges
      .filter((e) => nodeMap.has(e.from) && nodeMap.has(e.to))
      .map((e) => ({
        source: e.from,
        target: e.to,
        type: e.type,
      }))

    const simulation = d3
      .forceSimulation<NodeDatum>(nodes)
      .force("link", d3.forceLink<NodeDatum, LinkDatum>(links).id((d) => d.id).distance(80))
      .force("charge", d3.forceManyBody().strength(-200))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(30))

    const g = svg.append("g")

    // Zoom
    svg.call(
      d3.zoom<SVGSVGElement, unknown>().on("zoom", (event) => {
        g.attr("transform", event.transform)
      })
    )

    // Arrow marker
    svg.append("defs").append("marker")
      .attr("id", "arrow")
      .attr("viewBox", "0 -5 10 10")
      .attr("refX", 20)
      .attr("markerWidth", 6)
      .attr("markerHeight", 6)
      .attr("orient", "auto")
      .append("path")
      .attr("d", "M0,-5L10,0L0,5")
      .attr("fill", "#bbb")

    // Links
    const link = g
      .append("g")
      .selectAll("line")
      .data(links)
      .join("line")
      .attr("stroke", "#ddd")
      .attr("stroke-width", 1.5)
      .attr("marker-end", "url(#arrow)")

    // Link labels
    const linkLabel = g
      .append("g")
      .selectAll("text")
      .data(links)
      .join("text")
      .attr("text-anchor", "middle")
      .attr("font-size", 9)
      .attr("fill", "#999")
      .text((d) => d.type)

    // Node groups
    const node = g
      .append("g")
      .selectAll<SVGGElement, NodeDatum>("g")
      .data(nodes)
      .join("g")
      .attr("cursor", "pointer")
      .call(
        d3
          .drag<SVGGElement, NodeDatum>()
          .on("start", (event, d) => {
            if (!event.active) simulation.alphaTarget(0.3).restart()
            d.fx = d.x
            d.fy = d.y
          })
          .on("drag", (event, d) => {
            d.fx = event.x
            d.fy = event.y
          })
          .on("end", (event, d) => {
            if (!event.active) simulation.alphaTarget(0)
            d.fx = null
            d.fy = null
          })
      )
      .on("mouseenter", (_, d) => {
        setHoveredNode({ id: d.id, labels: d.labels, properties: d.properties })
      })
      .on("mouseleave", () => setHoveredNode(null))

    node
      .append("circle")
      .attr("r", (d) => getNodeRadius(d.labels))
      .attr("fill", (d) => getNodeColor(d.labels))
      .attr("stroke", "#fff")
      .attr("stroke-width", 2)

    node
      .append("text")
      .attr("text-anchor", "middle")
      .attr("dy", (d) => getNodeRadius(d.labels) + 12)
      .attr("font-size", 10)
      .attr("fill", "#555")
      .text((d) => {
        const p = d.properties
        return (p.name as string) || (p.model as string) || (p.id as string) || d.labels[0]
      })

    simulation.on("tick", () => {
      link
        .attr("x1", (d) => (d.source as NodeDatum).x ?? 0)
        .attr("y1", (d) => (d.source as NodeDatum).y ?? 0)
        .attr("x2", (d) => (d.target as NodeDatum).x ?? 0)
        .attr("y2", (d) => (d.target as NodeDatum).y ?? 0)

      linkLabel
        .attr("x", (d) => (((d.source as NodeDatum).x ?? 0) + ((d.target as NodeDatum).x ?? 0)) / 2)
        .attr("y", (d) => (((d.source as NodeDatum).y ?? 0) + ((d.target as NodeDatum).y ?? 0)) / 2)

      node.attr("transform", (d) => `translate(${d.x ?? 0},${d.y ?? 0})`)
    })

    return () => {
      simulation.stop()
    }
  }, [graphData])

  return (
    <div className="relative w-full h-full bg-white/60 rounded-lg overflow-hidden border border-neutral-200/80">
      {/* Legend */}
      <div className="absolute top-3 left-3 z-10 flex flex-wrap gap-2 max-w-xs">
        {Object.entries(NODE_COLORS).map(([label, color]) => (
          <div key={label} className="flex items-center gap-1">
            <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
            <span className="text-[10px] text-neutral-400">{label}</span>
          </div>
        ))}
      </div>

      {/* Refresh */}
      <button
        onClick={loadGraph}
        className="absolute top-3 right-3 z-10 p-1.5 rounded-md glass border border-neutral-200/80 shadow-lg text-neutral-400 hover:text-white/60 transition-colors"
      >
        <RefreshCw className="w-3.5 h-3.5" />
      </button>

      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-white/90">
          <Loader2 className="w-5 h-5 animate-spin text-teal-600" />
          <span className="ml-2 text-xs text-neutral-400">Loading graph...</span>
        </div>
      )}

      {error && (
        <div className="absolute inset-0 flex items-center justify-center text-center px-8 bg-white/90">
          <div className="space-y-2">
            <Network className="w-8 h-8 text-neutral-300 mx-auto" />
            <p className="text-neutral-400 text-xs">Backend not connected</p>
            <p className="text-neutral-400 text-[11px] max-w-[200px]">
              Start the FastAPI backend and seed the database to visualize Alex&apos;s context graph.
            </p>
            <button
              onClick={loadGraph}
              className="text-[11px] text-teal-400 hover:text-teal-400 transition-colors"
            >
              Retry
            </button>
          </div>
        </div>
      )}

      {!loading && !error && graphData && (
        <svg ref={svgRef} className="w-full h-full" />
      )}

      {/* Hovered node properties */}
      {hoveredNode && (
        <div className="absolute bottom-3 right-3 glass border border-neutral-200/80 shadow-lg rounded-xl p-3 max-w-xs text-xs z-20 shadow-2xl">
          <div className="flex items-center gap-1.5 mb-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: getNodeColor(hoveredNode.labels) }}
            />
            <span className="font-semibold text-neutral-800">
              {hoveredNode.labels.join(" · ")}
            </span>
          </div>
          <div className="space-y-1 text-neutral-500 max-h-36 overflow-y-auto">
            {Object.entries(hoveredNode.properties)
              .filter(([, v]) => v !== null && v !== undefined)
              .map(([k, v]) => (
                <div key={k} className="flex gap-2">
                  <span className="text-neutral-400 shrink-0">{k}:</span>
                  <span className="truncate">{String(v)}</span>
                </div>
              ))}
          </div>
        </div>
      )}

      {!loading && !error && (!graphData || !graphData.nodes || graphData.nodes.length === 0) && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 text-center px-8 bg-white/90">
          <Network className="w-8 h-8 text-neutral-300" />
          <p className="text-neutral-400 text-xs">No graph data yet</p>
          <p className="text-neutral-400 text-[11px] max-w-[220px]">
            Seed the database to populate Alex&apos;s context graph with shoes, reviews, and insights.
          </p>
          <button
            onClick={async () => {
              await fetch("/api/seed", { method: "POST" })
              loadGraph()
            }}
            className="px-3 py-1.5 bg-teal-700 hover:bg-teal-600 text-white text-[11px] rounded-lg transition-colors"
          >
            Seed &amp; Load
          </button>
        </div>
      )}
    </div>
  )
}
