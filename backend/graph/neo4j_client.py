import os
from neo4j import GraphDatabase, Driver

_driver: Driver | None = None


def get_driver() -> Driver:
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            os.environ["NEO4J_URI"],
            auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"]),
        )
    return _driver


async def close_driver():
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None


async def run_query(cypher: str, params: dict | None = None) -> list[dict]:
    """Run a Cypher query using the sync driver (works in serverless)."""
    driver = get_driver()
    with driver.session() as session:
        result = session.run(cypher, params or {})
        return result.data()


async def get_user_subgraph(user_id: str) -> dict:
    """Return nodes + edges for graph visualization (2 hops from user)."""
    driver = get_driver()

    nodes_map: dict[str, dict] = {}
    edges: list[dict] = []
    edge_id = 0

    with driver.session() as session:
        # Hop 1: User -> direct neighbors
        result = session.run("""
            MATCH (u:User {id: $userId})
            OPTIONAL MATCH (u)-[r]->(n)
            WITH u, r, n
            RETURN u.id AS userId, labels(u) AS userLabels, properties(u) AS userProps,
                   COALESCE(n.id, elementId(n)) AS nodeId, labels(n) AS nodeLabels,
                   properties(n) AS nodeProps, type(r) AS relType
        """, {"userId": user_id})

        for record in result:
            # Add user
            uid = record["userId"]
            if uid not in nodes_map:
                props = {k: v for k, v in record["userProps"].items() if k != "embedding"}
                nodes_map[uid] = {"id": uid, "labels": record["userLabels"], "properties": props}

            # Add neighbor
            nid = str(record["nodeId"]) if record["nodeId"] else None
            if nid and nid not in nodes_map:
                props = {k: v for k, v in record["nodeProps"].items() if k != "embedding"}
                nodes_map[nid] = {"id": nid, "labels": record["nodeLabels"], "properties": props}

            if nid and record["relType"]:
                edges.append({"id": f"e{edge_id}", "type": record["relType"], "from": uid, "to": nid})
                edge_id += 1

        # Hop 2: neighbors -> their neighbors
        hop1_ids = [nid for nid in nodes_map if nid != user_id]
        if hop1_ids:
            result2 = session.run("""
                UNWIND $nodeIds AS nid
                MATCH (n) WHERE n.id = nid
                OPTIONAL MATCH (n)-[r]->(m)
                RETURN n.id AS sourceId, COALESCE(m.id, elementId(m)) AS targetId,
                       labels(m) AS targetLabels, properties(m) AS targetProps, type(r) AS relType
            """, {"nodeIds": hop1_ids})

            for record in result2:
                tid = str(record["targetId"]) if record["targetId"] else None
                if tid and tid not in nodes_map and record["targetProps"]:
                    props = {k: v for k, v in record["targetProps"].items() if k != "embedding"}
                    nodes_map[tid] = {"id": tid, "labels": record["targetLabels"], "properties": props}
                if tid and record["relType"]:
                    edges.append({"id": f"e{edge_id}", "type": record["relType"], "from": record["sourceId"], "to": tid})
                    edge_id += 1

    return {"nodes": list(nodes_map.values()), "edges": edges}


async def get_conversation_traces(conversation_id: str) -> list[dict]:
    driver = get_driver()
    with driver.session() as session:
        result = session.run("""
            MATCH (dt:DecisionTrace)-[:PART_OF]->(c:Conversation {id: $convId})
            RETURN properties(dt) AS dt ORDER BY dt.timestamp ASC
        """, {"convId": conversation_id})
        return [dict(r["dt"]) for r in result]
