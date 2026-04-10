"""
Seed the neo4j-agent-memory library with Alex's profile data.

This populates the library's own schema (Entity / Fact / Preference /
Message / ReasoningTrace) so that when shopagent_adk.py runs, the
agent finds rich context to recall — not an empty profile.

Run once after the main seed:
    python -m agent.seed_agent_memory
"""

import asyncio
import os

from dotenv import load_dotenv

load_dotenv()

from neo4j_agent_memory import (
    EmbeddingConfig,
    EmbeddingProvider,
    EntityType,
    MemoryClient,
    MemorySettings,
    Neo4jConfig,
)


async def seed():
    settings = MemorySettings(
        neo4j=Neo4jConfig(
            uri=os.environ["NEO4J_URI"],
            username=os.environ["NEO4J_USERNAME"],
            password=os.environ["NEO4J_PASSWORD"],
        ),
        embedding=EmbeddingConfig(
            provider=EmbeddingProvider.SENTENCE_TRANSFORMERS,
            model="all-MiniLM-L6-v2",
            dimensions=384,
        ),
    )

    async with MemoryClient(settings=settings) as client:
        # ─── Long-term memory: Alex as an entity ───
        alex, _ = await client.long_term.add_entity(
            name="Alex Chen",
            entity_type=EntityType.PERSON,
            description="Narrow-footed road runner, size 9.5",
            attributes={
                "user_id": "alex",
                "foot_width": "narrow",
                "primary_size": 9.5,
                "fit_notes": "high arch, prefers snug heel with roomy toe box",
            },
        )
        print(f"  ✓ Entity: Alex Chen ({alex.id})")

        # ─── Long-term memory: Preferences ───
        prefs = [
            ("fit", "narrow width (AA)", "Alex has narrow feet"),
            ("fit", "snug heel lock", "Loved heel lock on Brooks Ghost 15"),
            ("fit", "roomy toe box for long runs", "Ghost 15 toe box was snug at mile 8"),
            ("brand", "prefers Brooks and Saucony", "Best fit experience"),
            ("brand", "avoids Nike running shoes", "Pegasus 40 too wide in midfoot"),
            ("budget", "$100-150", "Sweet spot for running shoes"),
            ("category", "road running", "Primary use case"),
            ("category", "gym training", "Secondary use case"),
        ]
        for category, pref, context in prefs:
            await client.long_term.add_preference(
                category=category,
                preference=pref,
                context=context,
                confidence=0.95,
            )
        print(f"  ✓ Preferences: {len(prefs)}")

        # ─── Long-term memory: Facts about Alex ───
        facts = [
            ("Alex Chen", "purchased", "Brooks Ghost 15 (rated 4 stars)"),
            ("Alex Chen", "purchased", "Asics Kayano 28 (rated 3 stars)"),
            ("Alex Chen", "rejected", "Nike Pegasus 40 — too wide in midfoot"),
            ("Alex Chen", "rejected", "Hoka Bondi 8 — rocker sole throws off gait"),
            ("Alex Chen", "noted", "Ghost 15 has great heel lock, snug toe box at mile 8"),
            ("Alex Chen", "noted", "Kayano 28 was heavier than expected, good for long slow runs"),
        ]
        for subject, predicate, obj in facts:
            await client.long_term.add_fact(subject=subject, predicate=predicate, obj=obj)
        print(f"  ✓ Facts: {len(facts)}")

        # ─── Reasoning memory: a past successful trace ───
        trace = await client.reasoning.start_trace(
            session_id="alex-session-001",
            task="recommend running shoes for Alex (narrow, road)",
        )
        await client.reasoning.add_step(
            trace_id=trace.id,
            thought="Alex has narrow feet and prefers snug heel + roomy toe box. Need to find shoes matching this profile.",
            action="Cross-user traversal: similar narrow-footed runners → their purchases",
            observation="3 similar users all bought Saucony Kinvara 14N with 5-star ratings",
        )
        await client.reasoning.add_step(
            trace_id=trace.id,
            thought="Need review evidence specific to narrow-footed runners",
            action="Query review insights filtered by authorWidth='narrow'",
            observation="12 positive narrow-foot insights for Kinvara 14N (heel lock + toe box)",
        )
        await client.reasoning.complete_trace(
            trace_id=trace.id,
            outcome="Recommended Saucony Kinvara 14N (91% match), Asics Nimbus 25N (88%), NB 1080v13N (84%). Alex accepted Kinvara 14N.",
            success=True,
        )
        print(f"  ✓ Reasoning trace: {trace.id}")

        # ─── Short-term memory: a few past messages ───
        msgs = [
            ("user", "I need new running shoes for road training"),
            ("assistant", "From your profile, I see you're narrow width 9.5 with budget $100-150. Top pick: Saucony Kinvara 14N — 91% match based on 12 narrow-foot review insights."),
            ("user", "Tell me more about heel fit"),
            ("assistant", "Kinvara 14N has snug heel lock — matches your Ghost 15 preference. 4 narrow-foot reviews specifically praise the heel cradle."),
            ("user", "Going with the Kinvara"),
            ("assistant", "Recorded. I've updated your profile with this purchase."),
        ]
        for role, content in msgs:
            await client.short_term.add_message(
                session_id="alex-session-001",
                role=role,
                content=content,
            )
        print(f"  ✓ Messages: {len(msgs)}")

        print()
        print("Agent memory seed complete.")
        stats = await client.get_stats()
        print(f"Stats: {stats}")


if __name__ == "__main__":
    asyncio.run(seed())
