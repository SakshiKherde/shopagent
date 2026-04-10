# Demo Cypher Queries

Run these in the Neo4j Aura Browser ([console.neo4j.io](https://console.neo4j.io))
alongside the ShopAgent demo. All queries return graph visualizations.

---

## Scenario 1: Long-Term Memory — "I need new running shoes"

### Alex's full shopping profile (purchases, rejections, views)
```cypher
MATCH path = (alex:User {id: 'alex'})-[r:PURCHASED|REJECTED|VIEWED]->(s:Shoe)
RETURN path
```

### The cross-user recommendation engine
```cypher
MATCH path = (alex:User {id:'alex'})-[:PURCHASED]->(s:Shoe)
             <-[:PURCHASED]-(similar:User {footWidth:'narrow'})
             -[:PURCHASED]->(candidate:Shoe)
             -[:HAS_REVIEW]->(r:Review {authorWidth:'narrow'})
             -[:CONTAINS_INSIGHT]->(i:ReviewInsight {sentiment:'positive'})
WHERE NOT (alex)-[:PURCHASED|REJECTED]->(candidate)
  AND candidate.inStock = true
RETURN path
LIMIT 40
```

### Similar narrow-footed customers
```cypher
MATCH path = (alex:User {id: 'alex'})-[:SIMILAR_TO]->(similar:User)
             -[:PURCHASED]->(s:Shoe)
RETURN path
```

---

## Scenario 2: Short-Term + Reasoning Memory — "Tell me about heel fit"

### Heel-specific review insights from narrow-footed runners
```cypher
MATCH path = (s:Shoe {id: 'saucony_kinvara_14_n'})
             -[:HAS_REVIEW]->(r:Review {authorWidth: 'narrow'})
             -[:CONTAINS_INSIGHT]->(i:ReviewInsight)
WHERE i.aspect = 'heel'
RETURN path
```

### All review insights for the Kinvara 14N
```cypher
MATCH path = (s:Shoe {id: 'saucony_kinvara_14_n'})
             -[:HAS_REVIEW]->(r:Review)
             -[:CONTAINS_INSIGHT]->(i:ReviewInsight)
RETURN path
```

### Conversation history with recommendations
```cypher
MATCH path = (alex:User {id: 'alex'})-[:HAD_CONVERSATION]->(c:Conversation)
             -[:PRODUCED]->(rec:Recommendation)-[:RECOMMENDS]->(s:Shoe)
RETURN path
```

### Cross-session learning (INFORMED_BY)
```cypher
MATCH path = (c1:Conversation)-[:INFORMED_BY]->(c2:Conversation)
RETURN path
```

---

## Scenario 3: Audit Trail — "I just bought the 1080v13N"

### Decision traces with labeled memory types
```cypher
MATCH path = (dt:DecisionTrace)-[:PART_OF]->(c:Conversation)
WHERE dt.memoryType IS NOT NULL
RETURN path
```

### Message → triggered → decision trace chain
```cypher
MATCH path = (m:Message)-[:TRIGGERED]->(dt:DecisionTrace)
             -[:PART_OF]->(c:Conversation)
RETURN path
```

### Decision trace → led to → recommendation → shoe
```cypher
MATCH path = (dt:DecisionTrace)-[:LED_TO]->(rec:Recommendation)
             -[:RECOMMENDS]->(s:Shoe)
RETURN path
```

### Full conversation thread (message chain)
```cypher
MATCH (c:Conversation {id: 'conv_session_2'})-[:FIRST_MESSAGE]->(first:Message)
MATCH path = (first)-[:NEXT_MESSAGE*]->(subsequent:Message)
RETURN path
```

---

## Big Picture

### Alex's complete context graph (2 hops)
```cypher
MATCH path = (alex:User {id: 'alex'})-[r]->(n)
RETURN path
```

### All 8 node types connected
```cypher
MATCH path = (n)-[r]->(m)
WHERE any(label IN labels(n) WHERE label IN
      ['User', 'Shoe', 'Review', 'ReviewInsight',
       'Conversation', 'Recommendation', 'DecisionTrace'])
RETURN path
LIMIT 200
```

### Database schema
```cypher
CALL db.schema.visualization
```

### Node counts
```cypher
MATCH (n)
RETURN labels(n)[0] AS type, count(n) AS count
ORDER BY count DESC
```

### Relationship counts
```cypher
MATCH ()-[r]->()
RETURN type(r) AS relationship, count(r) AS count
ORDER BY count DESC
```

---

## Memory-Specific Queries

### All three memory types in one view
```cypher
// Long-term: profile + purchases
MATCH ltPath = (u:User {id: 'alex'})-[:PURCHASED|REJECTED]->(s:Shoe)
// Short-term: conversation messages
MATCH stPath = (u)-[:HAD_CONVERSATION]->(c:Conversation)-[:FIRST_MESSAGE]->(m:Message)
// Reasoning: decision traces
MATCH rPath = (dt:DecisionTrace)-[:PART_OF]->(c)
WHERE dt.memoryType IS NOT NULL
RETURN ltPath, stPath, rPath
```

### Reasoning memory reuse pattern
```cypher
MATCH (c3:Conversation {id: 'conv_session_3'})-[:INFORMED_BY]->(c2:Conversation)
MATCH (c2)-[:PRODUCED]->(rec:Recommendation)-[:RECOMMENDS]->(s:Shoe)
MATCH (dt:DecisionTrace)-[:PART_OF]->(c3)
WHERE dt.memoryType = 'reasoning'
RETURN c3, c2, rec, s, dt
```
