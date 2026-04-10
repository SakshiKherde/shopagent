"""
Seed the Neo4j database with ShopAgent demo data.
All writes use MERGE so this is idempotent.
"""

import os
from neo4j import GraphDatabase

# ---------------------------------------------------------------------------
# Schema / Indexes
# ---------------------------------------------------------------------------
SCHEMA_QUERIES = [
    # Unique constraints
    "CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE",
    "CREATE CONSTRAINT shoe_id IF NOT EXISTS FOR (s:Shoe) REQUIRE s.id IS UNIQUE",
    "CREATE CONSTRAINT review_id IF NOT EXISTS FOR (r:Review) REQUIRE r.id IS UNIQUE",
    "CREATE CONSTRAINT insight_id IF NOT EXISTS FOR (ri:ReviewInsight) REQUIRE ri.id IS UNIQUE",
    "CREATE CONSTRAINT conv_id IF NOT EXISTS FOR (c:Conversation) REQUIRE c.id IS UNIQUE",
    "CREATE CONSTRAINT msg_id IF NOT EXISTS FOR (m:Message) REQUIRE m.id IS UNIQUE",
    "CREATE CONSTRAINT rec_id IF NOT EXISTS FOR (rec:Recommendation) REQUIRE rec.id IS UNIQUE",
    "CREATE CONSTRAINT dt_id IF NOT EXISTS FOR (dt:DecisionTrace) REQUIRE dt.id IS UNIQUE",
    # Vector indexes (1536 dims, cosine — requires Neo4j 5.13+)
    """CREATE VECTOR INDEX shoe_embedding IF NOT EXISTS
       FOR (s:Shoe) ON s.embedding
       OPTIONS {indexConfig: {`vector.dimensions`: 1536, `vector.similarity_function`: 'cosine'}}""",
    """CREATE VECTOR INDEX review_embedding IF NOT EXISTS
       FOR (r:Review) ON r.embedding
       OPTIONS {indexConfig: {`vector.dimensions`: 1536, `vector.similarity_function`: 'cosine'}}""",
    """CREATE VECTOR INDEX conversation_embedding IF NOT EXISTS
       FOR (c:Conversation) ON c.embedding
       OPTIONS {indexConfig: {`vector.dimensions`: 1536, `vector.similarity_function`: 'cosine'}}""",
]

# ---------------------------------------------------------------------------
# Users (8 diverse profiles)
# ---------------------------------------------------------------------------
USERS = [
    {
        "id": "alex",
        "name": "Alex Chen",
        "footWidth": "narrow",
        "primarySize": 9.5,
        "fitNotes": "goes half size up in Nike, true to size in Asics and Brooks. High arch, prefers snug heel with roomy toe box.",
        "stylePrefs": ["road running", "gym training"],
        "priceRange": "100-150",
        "totalSessions": 3,
    },
    {
        "id": "priya",
        "name": "Priya Patel",
        "footWidth": "wide",
        "primarySize": 7.5,
        "fitNotes": "needs wide or extra-wide in most brands. Overpronator diagnosed by podiatrist. Requires medial post or guide rails for stability.",
        "stylePrefs": ["trail", "road running"],
        "priceRange": "80-130",
        "totalSessions": 5,
    },
    {
        "id": "marcus",
        "name": "Marcus Johnson",
        "footWidth": "medium",
        "primarySize": 11.0,
        "fitNotes": "true to size across brands. High arch, uses custom orthotics on long runs. Training for third Boston Marathon.",
        "stylePrefs": ["road running", "marathon training"],
        "priceRange": "140-200",
        "totalSessions": 8,
    },
    {
        "id": "sarah",
        "name": "Sarah Kim",
        "footWidth": "narrow",
        "primarySize": 8.0,
        "fitNotes": "plantar fasciitis in left foot since 2023. Needs max cushion and arch support. Doctor recommended 10mm+ drop. Prefers plush feel over responsive.",
        "stylePrefs": ["casual", "gym training", "walking"],
        "priceRange": "100-160",
        "totalSessions": 2,
    },
    {
        "id": "james",
        "name": "James Rodriguez",
        "footWidth": "wide",
        "primarySize": 10.5,
        "fitNotes": "wide forefoot, medium heel. Sprinter and track athlete. Prefers lightweight shoes under 9oz. Goes half size down for racing flats.",
        "stylePrefs": ["track", "speed training", "road running"],
        "priceRange": "120-180",
        "totalSessions": 4,
    },
    {
        "id": "emma",
        "name": "Emma Wilson",
        "footWidth": "medium",
        "primarySize": 8.5,
        "fitNotes": "brand new runner, completed couch to 5K. Not sure of foot type yet. Tried one pair of generic sneakers and got shin splints.",
        "stylePrefs": ["road running", "lifestyle"],
        "priceRange": "90-140",
        "totalSessions": 1,
    },
    {
        "id": "user_jordan",
        "name": "Jordan Kim",
        "footWidth": "narrow",
        "primarySize": 9.0,
        "fitNotes": "narrow heel, needs snug fit. Mild overpronation. Prefers lightweight trainers for daily 5-8 mile runs.",
        "stylePrefs": ["road running"],
        "priceRange": "120-160",
        "totalSessions": 6,
    },
    {
        "id": "user_sam",
        "name": "Sam Rivera",
        "footWidth": "narrow",
        "primarySize": 8.5,
        "fitNotes": "true to size in most brands. Runs trails on weekends, roads during the week. Prefers versatile shoes.",
        "stylePrefs": ["road running", "trail"],
        "priceRange": "100-150",
        "totalSessions": 5,
    },
]

# ---------------------------------------------------------------------------
# Shoes (20 models with rich retail data)
# ---------------------------------------------------------------------------
SHOES = [
    {
        "id": "saucony_kinvara_14_n",
        "brand": "Saucony",
        "model": "Kinvara 14",
        "sku": "SAU-KIN14-N",
        "widthOptions": ["narrow", "medium"],
        "availableSizes": [7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0],
        "price": 139.95,
        "category": "neutral",
        "cushioning": "moderate",
        "drop": 4.0,
        "weight": 7.8,
        "stability": "neutral",
        "releaseYear": 2023,
        "colorways": ["Black/White", "Navy/Coral", "Grey/Teal", "Fog/Zenith"],
        "toeBoxFit": "roomy",
        "heelFit": "snug",
        "inStock": True,
        "url": "https://www.saucony.com/en/kinvara-14",
    },
    {
        "id": "asics_nimbus_25_n",
        "brand": "Asics",
        "model": "Gel-Nimbus 25",
        "sku": "ASICS-NIM25-N",
        "widthOptions": ["narrow", "medium", "wide"],
        "availableSizes": [7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 11.5],
        "price": 149.95,
        "category": "neutral",
        "cushioning": "max",
        "drop": 8.0,
        "weight": 10.2,
        "stability": "neutral",
        "releaseYear": 2023,
        "colorways": ["Black/Pure Silver", "Island Blue/Sun Peach", "White/Deep Ocean", "Midnight/Lime Zest"],
        "toeBoxFit": "standard",
        "heelFit": "snug",
        "inStock": True,
        "url": "https://www.asics.com/en/gel-nimbus-25",
    },
    {
        "id": "nb_1080v13_n",
        "brand": "New Balance",
        "model": "Fresh Foam 1080v13",
        "sku": "NB-1080V13-N",
        "widthOptions": ["narrow", "medium", "wide"],
        "availableSizes": [7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0],
        "price": 129.95,
        "category": "neutral",
        "cushioning": "max",
        "drop": 6.0,
        "weight": 10.4,
        "stability": "neutral",
        "releaseYear": 2023,
        "colorways": ["Black/Thunder", "White/Navy", "Sea Salt/Linen", "Eclipse/Vibrant Apricot"],
        "toeBoxFit": "roomy",
        "heelFit": "standard",
        "inStock": True,
        "url": "https://www.newbalance.com/fresh-foam-1080v13",
    },
    {
        "id": "brooks_adrenaline_gts23_n",
        "brand": "Brooks",
        "model": "Adrenaline GTS 23",
        "sku": "BRK-ADR23-N",
        "widthOptions": ["narrow", "medium", "wide", "extra-wide"],
        "availableSizes": [7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 12.0],
        "price": 139.95,
        "category": "stability",
        "cushioning": "moderate",
        "drop": 12.0,
        "weight": 10.2,
        "stability": "moderate",
        "releaseYear": 2023,
        "colorways": ["Black/Grey/White", "Blue/Nightlife", "Peacoat/Tanager Turquoise"],
        "toeBoxFit": "standard",
        "heelFit": "snug",
        "inStock": True,
        "url": "https://www.brooksrunning.com/adrenaline-gts-23",
    },
    {
        "id": "brooks_adrenaline_gts24",
        "brand": "Brooks",
        "model": "Adrenaline GTS 24",
        "sku": "BRK-ADR24",
        "widthOptions": ["narrow", "medium", "wide", "extra-wide"],
        "availableSizes": [7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 11.5, 12.0, 13.0],
        "price": 139.95,
        "category": "stability",
        "cushioning": "moderate",
        "drop": 12.0,
        "weight": 10.0,
        "stability": "moderate",
        "releaseYear": 2024,
        "colorways": ["Black/Black/Ebony", "Peacoat/Lemon Chrome", "Blue/Surf the Web", "Grey/Red"],
        "toeBoxFit": "standard",
        "heelFit": "snug",
        "inStock": True,
        "url": "https://www.brooksrunning.com/adrenaline-gts-24",
    },
    {
        "id": "saucony_ride_17_n",
        "brand": "Saucony",
        "model": "Ride 17",
        "sku": "SAU-RIDE17-N",
        "widthOptions": ["narrow", "medium"],
        "availableSizes": [7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0],
        "price": 134.95,
        "category": "neutral",
        "cushioning": "moderate",
        "drop": 8.0,
        "weight": 9.2,
        "stability": "neutral",
        "releaseYear": 2024,
        "colorways": ["Black/White", "Fog/Bough", "Navy/Infrared"],
        "toeBoxFit": "standard",
        "heelFit": "snug",
        "inStock": True,
        "url": "https://www.saucony.com/en/ride-17",
    },
    {
        "id": "nb_fresh_foam_x1080_n",
        "brand": "New Balance",
        "model": "Fresh Foam X 1080",
        "sku": "NB-FFX1080-N",
        "widthOptions": ["narrow", "medium"],
        "availableSizes": [8.0, 8.5, 9.0, 9.5, 10.0, 10.5],
        "price": 164.95,
        "category": "neutral",
        "cushioning": "max",
        "drop": 6.0,
        "weight": 10.6,
        "stability": "neutral",
        "releaseYear": 2024,
        "colorways": ["Black/Gum", "White/Chrome Blue", "Sea Salt/Blacktop"],
        "toeBoxFit": "roomy",
        "heelFit": "snug",
        "inStock": False,
        "url": "https://www.newbalance.com/fresh-foam-x-1080",
    },
    {
        "id": "asics_gel_nimbus_lite4_n",
        "brand": "Asics",
        "model": "Gel-Nimbus Lite 4",
        "sku": "ASICS-NIMLITE4-N",
        "widthOptions": ["narrow", "medium"],
        "availableSizes": [7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0],
        "price": 119.95,
        "category": "neutral",
        "cushioning": "moderate",
        "drop": 8.0,
        "weight": 8.6,
        "stability": "neutral",
        "releaseYear": 2024,
        "colorways": ["Black/Carrier Grey", "White/Champagne", "French Blue/Denim Blue"],
        "toeBoxFit": "standard",
        "heelFit": "standard",
        "inStock": True,
        "url": "https://www.asics.com/en/gel-nimbus-lite-4",
    },
    {
        "id": "brooks_glycerin_21_n",
        "brand": "Brooks",
        "model": "Glycerin 21",
        "sku": "BRK-GLY21-N",
        "widthOptions": ["narrow", "medium", "wide"],
        "availableSizes": [7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 12.0],
        "price": 159.95,
        "category": "neutral",
        "cushioning": "max",
        "drop": 10.0,
        "weight": 10.6,
        "stability": "neutral",
        "releaseYear": 2024,
        "colorways": ["Black/Black/Ebony", "Coconut/Chateau Grey", "Blue/Icy Pink"],
        "toeBoxFit": "roomy",
        "heelFit": "snug",
        "inStock": True,
        "url": "https://www.brooksrunning.com/glycerin-21",
    },
    {
        "id": "brooks_ghost_15_n",
        "brand": "Brooks",
        "model": "Ghost 15",
        "sku": "BRK-GHO15-N",
        "widthOptions": ["narrow", "medium", "wide"],
        "availableSizes": [7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0],
        "price": 139.95,
        "category": "neutral",
        "cushioning": "moderate",
        "drop": 12.0,
        "weight": 9.8,
        "stability": "neutral",
        "releaseYear": 2023,
        "colorways": ["Black/Black/Ebony", "White/Grey", "Alloy/Oyster"],
        "toeBoxFit": "standard",
        "heelFit": "snug",
        "inStock": True,
        "url": "https://www.brooksrunning.com/ghost-15",
    },
    {
        "id": "asics_kayano_28_n",
        "brand": "Asics",
        "model": "Kayano 28",
        "sku": "ASICS-KAY28-N",
        "widthOptions": ["narrow", "medium"],
        "availableSizes": [7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0],
        "price": 149.95,
        "category": "stability",
        "cushioning": "max",
        "drop": 10.0,
        "weight": 11.2,
        "stability": "moderate",
        "releaseYear": 2022,
        "colorways": ["Black/White", "Thunder Blue/Glow Yellow", "Piedmont Grey/Shocking Orange"],
        "toeBoxFit": "standard",
        "heelFit": "snug",
        "inStock": True,
        "url": "https://www.asics.com/en/kayano-28",
    },
    {
        "id": "nike_pegasus_40",
        "brand": "Nike",
        "model": "Pegasus 40",
        "sku": "NIKE-PEG40",
        "widthOptions": ["medium", "wide", "extra-wide"],
        "availableSizes": [7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 12.0],
        "price": 134.99,
        "category": "road running",
        "cushioning": "moderate",
        "drop": 10.0,
        "weight": 9.6,
        "stability": "neutral",
        "releaseYear": 2023,
        "colorways": ["Black/White", "Ashen Slate/Football Grey", "Eggplant/Vivid Purple"],
        "toeBoxFit": "wide",
        "heelFit": "standard",
        "inStock": True,
        "url": "https://www.nike.com/pegasus-40",
    },
    {
        "id": "hoka_bondi_8",
        "brand": "Hoka",
        "model": "Bondi 8",
        "sku": "HOKA-BON8",
        "widthOptions": ["medium", "wide"],
        "availableSizes": [7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 12.0],
        "price": 164.95,
        "category": "road running",
        "cushioning": "max",
        "drop": 4.0,
        "weight": 10.8,
        "stability": "neutral",
        "releaseYear": 2023,
        "colorways": ["Black/White", "Coastal Sky/All Aboard", "Nimbus Cloud/Ice Water"],
        "toeBoxFit": "wide",
        "heelFit": "wide",
        "inStock": True,
        "url": "https://www.hoka.com/bondi-8",
    },
    {
        "id": "nike_vomero_17",
        "brand": "Nike",
        "model": "Vomero 17",
        "sku": "NIKE-VOM17",
        "widthOptions": ["medium", "wide"],
        "availableSizes": [7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 11.5, 12.0],
        "price": 159.99,
        "category": "neutral",
        "cushioning": "max",
        "drop": 10.0,
        "weight": 10.0,
        "stability": "neutral",
        "releaseYear": 2024,
        "colorways": ["Black/Anthracite", "Photon Dust/White", "Sail/Safety Orange"],
        "toeBoxFit": "standard",
        "heelFit": "standard",
        "inStock": True,
        "url": "https://www.nike.com/vomero-17",
    },
    {
        "id": "nike_invincible_3",
        "brand": "Nike",
        "model": "ZoomX Invincible 3",
        "sku": "NIKE-INV3",
        "widthOptions": ["medium", "wide"],
        "availableSizes": [7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 12.0, 13.0],
        "price": 179.99,
        "category": "neutral",
        "cushioning": "max",
        "drop": 9.0,
        "weight": 10.6,
        "stability": "neutral",
        "releaseYear": 2024,
        "colorways": ["Black/White", "Barely Green/Glacier Blue", "Crimson Bliss/Bright Mandarin"],
        "toeBoxFit": "roomy",
        "heelFit": "wide",
        "inStock": True,
        "url": "https://www.nike.com/invincible-3",
    },
    {
        "id": "hoka_clifton_9",
        "brand": "Hoka",
        "model": "Clifton 9",
        "sku": "HOKA-CLF9",
        "widthOptions": ["medium", "wide"],
        "availableSizes": [7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 12.0],
        "price": 144.95,
        "category": "neutral",
        "cushioning": "max",
        "drop": 5.0,
        "weight": 8.9,
        "stability": "neutral",
        "releaseYear": 2023,
        "colorways": ["Black/White", "Airy Blue/Ice Water", "Shifting Sand/Eggnog", "Cerise/Real Teal"],
        "toeBoxFit": "standard",
        "heelFit": "standard",
        "inStock": True,
        "url": "https://www.hoka.com/clifton-9",
    },
    {
        "id": "hoka_arahi_7",
        "brand": "Hoka",
        "model": "Arahi 7",
        "sku": "HOKA-ARA7",
        "widthOptions": ["medium", "wide"],
        "availableSizes": [7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 12.0, 13.0],
        "price": 139.95,
        "category": "stability",
        "cushioning": "max",
        "drop": 5.0,
        "weight": 9.7,
        "stability": "moderate",
        "releaseYear": 2024,
        "colorways": ["Black/White", "Outer Space/Bellwether Blue", "Real Teal/Shadow"],
        "toeBoxFit": "standard",
        "heelFit": "snug",
        "inStock": True,
        "url": "https://www.hoka.com/arahi-7",
    },
    {
        "id": "on_cloud_5",
        "brand": "On",
        "model": "Cloud 5",
        "sku": "ON-CLD5",
        "widthOptions": ["medium", "wide"],
        "availableSizes": [7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 12.0],
        "price": 149.99,
        "category": "lifestyle",
        "cushioning": "moderate",
        "drop": 6.0,
        "weight": 8.5,
        "stability": "neutral",
        "releaseYear": 2023,
        "colorways": ["All Black", "Ice/White", "Olive/Fawn", "Undyed White"],
        "toeBoxFit": "standard",
        "heelFit": "standard",
        "inStock": True,
        "url": "https://www.on.com/cloud-5",
    },
    {
        "id": "asics_gt2000_12",
        "brand": "Asics",
        "model": "GT-2000 12",
        "sku": "ASICS-GT2K12",
        "widthOptions": ["narrow", "medium", "wide", "extra-wide"],
        "availableSizes": [7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 11.5, 12.0, 13.0],
        "price": 129.95,
        "category": "stability",
        "cushioning": "moderate",
        "drop": 8.0,
        "weight": 9.5,
        "stability": "mild",
        "releaseYear": 2024,
        "colorways": ["Black/Carrier Grey", "Sheet Rock/Bright Orange", "Blue Expanse/Sunrise Red"],
        "toeBoxFit": "standard",
        "heelFit": "snug",
        "inStock": True,
        "url": "https://www.asics.com/en/gt-2000-12",
    },
    {
        "id": "saucony_triumph_22",
        "brand": "Saucony",
        "model": "Triumph 22",
        "sku": "SAU-TRI22",
        "widthOptions": ["medium", "wide"],
        "availableSizes": [7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 12.0, 13.0],
        "price": 159.95,
        "category": "neutral",
        "cushioning": "max",
        "drop": 10.0,
        "weight": 10.6,
        "stability": "neutral",
        "releaseYear": 2024,
        "colorways": ["Black/White", "Fog/Vapor", "Navy/Peel", "Blaze/Canteen"],
        "toeBoxFit": "roomy",
        "heelFit": "standard",
        "inStock": True,
        "url": "https://www.saucony.com/en/triumph-22",
    },
]

# ---------------------------------------------------------------------------
# Reviews + Insights  (50+ across 8 shoes)
# ---------------------------------------------------------------------------
REVIEWS_DATA = {
    "saucony_kinvara_14_n": [
        {
            "id": "rev_kin14_001",
            "text": "Narrow footed runner here. Heel locks in immediately. Toe box has real room -- no black toenails after 10 miles.",
            "rating": 5, "authorWidth": "narrow", "verified": True, "source": "RunnerWorld",
            "insights": [
                {"id": "ins_kin14_001a", "aspect": "heel", "sentiment": "positive", "relevantToNarrow": True,
                 "quote": "Heel locks in immediately.", "confidence": 0.97},
                {"id": "ins_kin14_001b", "aspect": "toe-box", "sentiment": "positive", "relevantToNarrow": True,
                 "quote": "Toe box has real room -- no black toenails after 10 miles.", "confidence": 0.95},
            ],
        },
        {
            "id": "rev_kin14_002",
            "text": "I have a very narrow foot (AA width) and the Kinvara 14 narrow fits like a glove. No slipping in the heel at all.",
            "rating": 5, "authorWidth": "narrow", "verified": True, "source": "Amazon",
            "insights": [
                {"id": "ins_kin14_002a", "aspect": "overall-fit", "sentiment": "positive", "relevantToNarrow": True,
                 "quote": "Fits like a glove. No slipping in the heel at all.", "confidence": 0.96},
            ],
        },
        {
            "id": "rev_kin14_003",
            "text": "Finally a lightweight trainer that doesn't feel sloppy on my narrow foot. The upper hugs without squeezing the forefoot.",
            "rating": 5, "authorWidth": "narrow", "verified": True, "source": "Fleet Feet",
            "insights": [
                {"id": "ins_kin14_003a", "aspect": "overall-fit", "sentiment": "positive", "relevantToNarrow": True,
                 "quote": "The upper hugs without squeezing the forefoot.", "confidence": 0.93},
            ],
        },
        {
            "id": "rev_kin14_004",
            "text": "Wore these on a half marathon. My narrow heels stayed put the entire race. A little firm underfoot but I prefer that.",
            "rating": 4, "authorWidth": "narrow", "verified": True, "source": "Strava",
            "insights": [
                {"id": "ins_kin14_004a", "aspect": "heel", "sentiment": "positive", "relevantToNarrow": True,
                 "quote": "Narrow heels stayed put the entire race.", "confidence": 0.94},
            ],
        },
        {
            "id": "rev_kin14_005",
            "text": "Great speed shoe for narrow feet. Arch support is minimal -- ideal for runners with higher arches who need less bulk.",
            "rating": 4, "authorWidth": "narrow", "verified": False, "source": "Reddit",
            "insights": [
                {"id": "ins_kin14_005a", "aspect": "arch", "sentiment": "neutral", "relevantToNarrow": True,
                 "quote": "Arch support is minimal -- ideal for runners with higher arches who need less bulk.", "confidence": 0.80},
            ],
        },
        {
            "id": "rev_kin14_006",
            "text": "I switched from a Brooks Ghost and the Kinvara 14 N is noticeably lighter. Heel cradle is tighter which I love.",
            "rating": 5, "authorWidth": "narrow", "verified": True, "source": "RunnerWorld",
            "insights": [
                {"id": "ins_kin14_006a", "aspect": "heel", "sentiment": "positive", "relevantToNarrow": True,
                 "quote": "Heel cradle is tighter which I love.", "confidence": 0.92},
            ],
        },
        {
            "id": "rev_kin14_007",
            "text": "Toes have breathing room unlike my old narrow shoes. No hot spots after 8 miles.",
            "rating": 4, "authorWidth": "narrow", "verified": True, "source": "Amazon",
            "insights": [
                {"id": "ins_kin14_007a", "aspect": "toe-box", "sentiment": "positive", "relevantToNarrow": True,
                 "quote": "Toes have breathing room unlike my old narrow shoes.", "confidence": 0.91},
            ],
        },
        {
            "id": "rev_kin14_008",
            "text": "Medium width was too sloppy for my narrow foot. The N version is perfect. Don't bother with standard width.",
            "rating": 5, "authorWidth": "narrow", "verified": True, "source": "Fleet Feet",
            "insights": [
                {"id": "ins_kin14_008a", "aspect": "overall-fit", "sentiment": "positive", "relevantToNarrow": True,
                 "quote": "The N version is perfect. Don't bother with standard width.", "confidence": 0.97},
            ],
        },
        {
            "id": "rev_kin14_009",
            "text": "Good shoe overall. Fits normal footed people fine too but especially shines for narrow.",
            "rating": 4, "authorWidth": "medium", "verified": True, "source": "Amazon",
            "insights": [
                {"id": "ins_kin14_009a", "aspect": "overall-fit", "sentiment": "positive", "relevantToNarrow": False,
                 "quote": "Especially shines for narrow.", "confidence": 0.75},
            ],
        },
        {
            "id": "rev_kin14_010",
            "text": "I have a B width foot and the Kinvara 14N is a touch narrow even for me. Sizing up half worked.",
            "rating": 3, "authorWidth": "medium", "verified": True, "source": "RunnerWorld",
            "insights": [
                {"id": "ins_kin14_010a", "aspect": "overall-fit", "sentiment": "neutral", "relevantToNarrow": False,
                 "quote": "A touch narrow even for me.", "confidence": 0.72},
            ],
        },
        {
            "id": "rev_kin14_011",
            "text": "My narrow-footed running club swears by these. Everyone who has AA or B width loves the secure feel.",
            "rating": 5, "authorWidth": "narrow", "verified": False, "source": "Reddit",
            "insights": [
                {"id": "ins_kin14_011a", "aspect": "overall-fit", "sentiment": "positive", "relevantToNarrow": True,
                 "quote": "Everyone with AA or B width loves the secure feel.", "confidence": 0.88},
            ],
        },
        {
            "id": "rev_kin14_012",
            "text": "Ran my first marathon in these. Zero blisters. Heel stayed locked even downhill. Narrow width was exactly right.",
            "rating": 5, "authorWidth": "narrow", "verified": True, "source": "Strava",
            "insights": [
                {"id": "ins_kin14_012a", "aspect": "heel", "sentiment": "positive", "relevantToNarrow": True,
                 "quote": "Heel stayed locked even downhill.", "confidence": 0.96},
                {"id": "ins_kin14_012b", "aspect": "overall-fit", "sentiment": "positive", "relevantToNarrow": True,
                 "quote": "Zero blisters. Narrow width was exactly right.", "confidence": 0.95},
            ],
        },
    ],
    "asics_nimbus_25_n": [
        {
            "id": "rev_nim25_001",
            "text": "I've had narrow feet my whole life and Asics narrow width is the gold standard. The Nimbus 25 N is plush without being sloppy.",
            "rating": 5, "authorWidth": "narrow", "verified": True, "source": "Amazon",
            "insights": [
                {"id": "ins_nim25_001a", "aspect": "overall-fit", "sentiment": "positive", "relevantToNarrow": True,
                 "quote": "Asics narrow width is the gold standard. Plush without being sloppy.", "confidence": 0.97},
            ],
        },
        {
            "id": "rev_nim25_002",
            "text": "Heel counter on the Nimbus 25 N is exceptional. My narrow heel has never felt more supported on long runs.",
            "rating": 5, "authorWidth": "narrow", "verified": True, "source": "Fleet Feet",
            "insights": [
                {"id": "ins_nim25_002a", "aspect": "heel", "sentiment": "positive", "relevantToNarrow": True,
                 "quote": "My narrow heel has never felt more supported on long runs.", "confidence": 0.95},
            ],
        },
        {
            "id": "rev_nim25_003",
            "text": "Toe box is a bit snugger than I expected for 'standard' fit, but that's actually perfect for my narrow AA foot.",
            "rating": 4, "authorWidth": "narrow", "verified": True, "source": "RunnerWorld",
            "insights": [
                {"id": "ins_nim25_003a", "aspect": "toe-box", "sentiment": "positive", "relevantToNarrow": True,
                 "quote": "Snugger than expected -- perfect for my narrow AA foot.", "confidence": 0.88},
            ],
        },
        {
            "id": "rev_nim25_004",
            "text": "Best arch support I've found in a narrow shoe. Felt the arch engagement from mile 1.",
            "rating": 5, "authorWidth": "narrow", "verified": True, "source": "Amazon",
            "insights": [
                {"id": "ins_nim25_004a", "aspect": "arch", "sentiment": "positive", "relevantToNarrow": True,
                 "quote": "Best arch support I've found in a narrow shoe.", "confidence": 0.96},
            ],
        },
        {
            "id": "rev_nim25_005",
            "text": "Ran 20 miles in these. No foot sliding. The narrow version holds your foot like it was custom made.",
            "rating": 5, "authorWidth": "narrow", "verified": True, "source": "Strava",
            "insights": [
                {"id": "ins_nim25_005a", "aspect": "overall-fit", "sentiment": "positive", "relevantToNarrow": True,
                 "quote": "No foot sliding. Holds your foot like it was custom made.", "confidence": 0.97},
            ],
        },
        {
            "id": "rev_nim25_006",
            "text": "Heavier than the Kinvara but that cushioning is worth it for my narrow flat feet. Heel is locked in tight.",
            "rating": 4, "authorWidth": "narrow", "verified": True, "source": "Reddit",
            "insights": [
                {"id": "ins_nim25_006a", "aspect": "heel", "sentiment": "positive", "relevantToNarrow": True,
                 "quote": "Heel is locked in tight.", "confidence": 0.93},
            ],
        },
        {
            "id": "rev_nim25_007",
            "text": "Switched from Kayano 28 N to Nimbus 25 N. Much better toe box room and lighter by 0.5oz.",
            "rating": 5, "authorWidth": "narrow", "verified": True, "source": "Fleet Feet",
            "insights": [
                {"id": "ins_nim25_007a", "aspect": "toe-box", "sentiment": "positive", "relevantToNarrow": True,
                 "quote": "Much better toe box room.", "confidence": 0.92},
            ],
        },
        {
            "id": "rev_nim25_008",
            "text": "I was skeptical about the price but after 300 miles these are still holding up. Great for narrow runners.",
            "rating": 5, "authorWidth": "narrow", "verified": True, "source": "Amazon",
            "insights": [
                {"id": "ins_nim25_008a", "aspect": "overall-fit", "sentiment": "positive", "relevantToNarrow": True,
                 "quote": "Still holding up after 300 miles. Great for narrow runners.", "confidence": 0.90},
            ],
        },
        {
            "id": "rev_nim25_009",
            "text": "The standard version was way too wide. The N width is a completely different shoe -- snug and precise.",
            "rating": 5, "authorWidth": "narrow", "verified": True, "source": "RunnerWorld",
            "insights": [
                {"id": "ins_nim25_009a", "aspect": "overall-fit", "sentiment": "positive", "relevantToNarrow": True,
                 "quote": "The N width is a completely different shoe -- snug and precise.", "confidence": 0.96},
            ],
        },
        {
            "id": "rev_nim25_010",
            "text": "Minor complaint: the heel collar is so tight it took a few runs to break in. Worth it once broken in.",
            "rating": 4, "authorWidth": "narrow", "verified": False, "source": "Reddit",
            "insights": [
                {"id": "ins_nim25_010a", "aspect": "heel", "sentiment": "neutral", "relevantToNarrow": True,
                 "quote": "Heel collar so tight it took a few runs to break in.", "confidence": 0.82},
            ],
        },
        {
            "id": "rev_nim25_011",
            "text": "Perfect for my narrow high-arched feet. The arch support is better than any insole I've tried.",
            "rating": 5, "authorWidth": "narrow", "verified": True, "source": "Fleet Feet",
            "insights": [
                {"id": "ins_nim25_011a", "aspect": "arch", "sentiment": "positive", "relevantToNarrow": True,
                 "quote": "Arch support is better than any insole I've tried.", "confidence": 0.95},
            ],
        },
        {
            "id": "rev_nim25_012",
            "text": "Daily trainer for my narrow feet for 2 years running. Never going back to anything else.",
            "rating": 5, "authorWidth": "narrow", "verified": True, "source": "Amazon",
            "insights": [
                {"id": "ins_nim25_012a", "aspect": "overall-fit", "sentiment": "positive", "relevantToNarrow": True,
                 "quote": "Daily trainer for my narrow feet for 2 years running.", "confidence": 0.94},
            ],
        },
    ],
    "nb_1080v13_n": [
        {
            "id": "rev_1080_001",
            "text": "The 1080v13 N is the most comfortable shoe I've owned as a narrow-footed runner. Zero dead spots.",
            "rating": 5, "authorWidth": "narrow", "verified": True, "source": "Amazon",
            "insights": [
                {"id": "ins_1080_001a", "aspect": "overall-fit", "sentiment": "positive", "relevantToNarrow": True,
                 "quote": "Most comfortable shoe I've owned as a narrow-footed runner.", "confidence": 0.97},
            ],
        },
        {
            "id": "rev_1080_002",
            "text": "Narrow variant really is narrow -- my B-width foot fits perfectly with no sliding.",
            "rating": 5, "authorWidth": "narrow", "verified": True, "source": "Fleet Feet",
            "insights": [
                {"id": "ins_1080_002a", "aspect": "overall-fit", "sentiment": "positive", "relevantToNarrow": True,
                 "quote": "Narrow variant really is narrow -- no sliding.", "confidence": 0.96},
            ],
        },
        {
            "id": "rev_1080_003",
            "text": "Toe box is surprisingly roomy for a narrow shoe. My toes spread naturally without the shoe feeling loose.",
            "rating": 5, "authorWidth": "narrow", "verified": True, "source": "RunnerWorld",
            "insights": [
                {"id": "ins_1080_003a", "aspect": "toe-box", "sentiment": "positive", "relevantToNarrow": True,
                 "quote": "Toe box is surprisingly roomy for a narrow shoe.", "confidence": 0.95},
            ],
        },
        {
            "id": "rev_1080_004",
            "text": "Heel cup is average -- not the tightest I've experienced but acceptable for my narrow heel.",
            "rating": 3, "authorWidth": "narrow", "verified": True, "source": "Amazon",
            "insights": [
                {"id": "ins_1080_004a", "aspect": "heel", "sentiment": "neutral", "relevantToNarrow": True,
                 "quote": "Heel cup is average -- acceptable for my narrow heel.", "confidence": 0.83},
            ],
        },
        {
            "id": "rev_1080_005",
            "text": "The Fresh Foam cushioning is unmatched. Feels like running on clouds without the width penalty.",
            "rating": 5, "authorWidth": "narrow", "verified": True, "source": "Strava",
            "insights": [
                {"id": "ins_1080_005a", "aspect": "overall-fit", "sentiment": "positive", "relevantToNarrow": True,
                 "quote": "Feels like running on clouds without the width penalty.", "confidence": 0.93},
            ],
        },
        {
            "id": "rev_1080_006",
            "text": "Great arch support for a neutral shoe. My narrow foot doesn't pronate in these at all.",
            "rating": 4, "authorWidth": "narrow", "verified": False, "source": "Reddit",
            "insights": [
                {"id": "ins_1080_006a", "aspect": "arch", "sentiment": "positive", "relevantToNarrow": True,
                 "quote": "Narrow foot doesn't pronate in these at all.", "confidence": 0.88},
            ],
        },
        {
            "id": "rev_1080_007",
            "text": "Bought these on sale at $20 off and it's the best running investment I've made. Narrow fit is spot on.",
            "rating": 5, "authorWidth": "narrow", "verified": True, "source": "Amazon",
            "insights": [
                {"id": "ins_1080_007a", "aspect": "overall-fit", "sentiment": "positive", "relevantToNarrow": True,
                 "quote": "Narrow fit is spot on.", "confidence": 0.92},
            ],
        },
        {
            "id": "rev_1080_008",
            "text": "Used to run in Brooks but the NB 1080v13 N converted me. So much more room in the toe box while staying narrow at the heel.",
            "rating": 5, "authorWidth": "narrow", "verified": True, "source": "Fleet Feet",
            "insights": [
                {"id": "ins_1080_008a", "aspect": "toe-box", "sentiment": "positive", "relevantToNarrow": True,
                 "quote": "More room in the toe box while staying narrow at the heel.", "confidence": 0.96},
            ],
        },
        {
            "id": "rev_1080_009",
            "text": "Slightly heavier than expected but the cushion absorbs the impact beautifully. Narrow width holds everything in place.",
            "rating": 4, "authorWidth": "narrow", "verified": True, "source": "RunnerWorld",
            "insights": [
                {"id": "ins_1080_009a", "aspect": "overall-fit", "sentiment": "positive", "relevantToNarrow": True,
                 "quote": "Narrow width holds everything in place.", "confidence": 0.91},
            ],
        },
        {
            "id": "rev_1080_010",
            "text": "My narrow feet were slipping in the standard width. The N version eliminated that completely.",
            "rating": 5, "authorWidth": "narrow", "verified": True, "source": "Amazon",
            "insights": [
                {"id": "ins_1080_010a", "aspect": "overall-fit", "sentiment": "positive", "relevantToNarrow": True,
                 "quote": "N version eliminated slipping completely.", "confidence": 0.97},
            ],
        },
        {
            "id": "rev_1080_011",
            "text": "The 1080v13 N is a huge upgrade from v12. Better heel lock and roomier toe box at the same time.",
            "rating": 5, "authorWidth": "narrow", "verified": True, "source": "Strava",
            "insights": [
                {"id": "ins_1080_011a", "aspect": "heel", "sentiment": "positive", "relevantToNarrow": True,
                 "quote": "Better heel lock.", "confidence": 0.93},
                {"id": "ins_1080_011b", "aspect": "toe-box", "sentiment": "positive", "relevantToNarrow": True,
                 "quote": "Roomier toe box at the same time.", "confidence": 0.92},
            ],
        },
        {
            "id": "rev_1080_012",
            "text": "Long distance narrow runner -- this is my marathon shoe now. 26.2 miles and my feet felt fresh at the finish.",
            "rating": 5, "authorWidth": "narrow", "verified": True, "source": "RunnerWorld",
            "insights": [
                {"id": "ins_1080_012a", "aspect": "overall-fit", "sentiment": "positive", "relevantToNarrow": True,
                 "quote": "26.2 miles and my feet felt fresh at the finish.", "confidence": 0.96},
            ],
        },
    ],
    "brooks_adrenaline_gts24": [
        {
            "id": "rev_gts24_001",
            "text": "As an overpronator with wide feet, the GTS 24 wide is a dream. GuideRails keep me stable without feeling rigid. Ran a hilly 10K and my ankles felt supported the entire time.",
            "rating": 5, "authorWidth": "wide", "verified": True, "source": "RunnerWorld",
            "insights": [
                {"id": "ins_gts24_001a", "aspect": "stability", "sentiment": "positive", "relevantToNarrow": False,
                 "quote": "GuideRails keep me stable without feeling rigid.", "confidence": 0.96},
            ],
        },
        {
            "id": "rev_gts24_002",
            "text": "Upgraded from the GTS 23 and the midsole is noticeably softer. My plantar fasciitis has calmed down since switching. The wide version gives my bunions room to breathe.",
            "rating": 5, "authorWidth": "wide", "verified": True, "source": "Fleet Feet",
            "insights": [
                {"id": "ins_gts24_002a", "aspect": "cushioning", "sentiment": "positive", "relevantToNarrow": False,
                 "quote": "Midsole is noticeably softer. My plantar fasciitis has calmed down.", "confidence": 0.94},
                {"id": "ins_gts24_002b", "aspect": "toe-box", "sentiment": "positive", "relevantToNarrow": False,
                 "quote": "Wide version gives my bunions room to breathe.", "confidence": 0.93},
            ],
        },
        {
            "id": "rev_gts24_003",
            "text": "I need stability shoes for my overpronation and these deliver. 12mm drop is perfect for my Achilles issues. Ran my first half in these -- zero problems at mile 11 where I usually start breaking down.",
            "rating": 5, "authorWidth": "medium", "verified": True, "source": "Strava",
            "insights": [
                {"id": "ins_gts24_003a", "aspect": "stability", "sentiment": "positive", "relevantToNarrow": False,
                 "quote": "12mm drop is perfect for my Achilles issues.", "confidence": 0.92},
            ],
        },
        {
            "id": "rev_gts24_004",
            "text": "Good stability shoe but heavy for speed work. At 10oz it's firmly a daily trainer, not a tempo shoe. The arch support collapsed after about 200 miles which was disappointing.",
            "rating": 3, "authorWidth": "medium", "verified": True, "source": "Amazon",
            "insights": [
                {"id": "ins_gts24_004a", "aspect": "durability", "sentiment": "negative", "relevantToNarrow": False,
                 "quote": "Arch support collapsed after about 200 miles.", "confidence": 0.90},
            ],
        },
        {
            "id": "rev_gts24_005",
            "text": "Tried these based on my podiatrist's recommendation. As a budget-conscious runner, getting GTS-level stability for $140 is excellent value. The extra-wide fit saved my training block.",
            "rating": 4, "authorWidth": "wide", "verified": True, "source": "Reddit",
            "insights": [
                {"id": "ins_gts24_005a", "aspect": "value", "sentiment": "positive", "relevantToNarrow": False,
                 "quote": "Getting GTS-level stability for $140 is excellent value.", "confidence": 0.88},
            ],
        },
        {
            "id": "rev_gts24_006",
            "text": "Compared to the Hoka Arahi 7, the GTS 24 has firmer stability. I prefer the Brooks for road -- it doesn't roll as much on uneven pavement. Heel lock is excellent even in the wide version.",
            "rating": 4, "authorWidth": "wide", "verified": True, "source": "RunnerWorld",
            "insights": [
                {"id": "ins_gts24_006a", "aspect": "stability", "sentiment": "positive", "relevantToNarrow": False,
                 "quote": "Firmer stability than Hoka Arahi 7. Doesn't roll on uneven pavement.", "confidence": 0.91},
            ],
        },
    ],
    "hoka_clifton_9": [
        {
            "id": "rev_clf9_001",
            "text": "The Clifton 9 is absurdly light for a max-cushion shoe. At 8.9oz it feels like a racing flat but rides like a Bondi. I use these for my easy 60-minute runs and my legs recover faster than in any other shoe.",
            "rating": 5, "authorWidth": "medium", "verified": True, "source": "RunnerWorld",
            "insights": [
                {"id": "ins_clf9_001a", "aspect": "weight", "sentiment": "positive", "relevantToNarrow": False,
                 "quote": "Absurdly light for a max-cushion shoe. Feels like a racing flat but rides like a Bondi.", "confidence": 0.96},
            ],
        },
        {
            "id": "rev_clf9_002",
            "text": "New runner here. This was my first real running shoe and it made a huge difference. The rocker geometry felt weird for the first mile but now I can't imagine running without it. Did my first 10K in these.",
            "rating": 5, "authorWidth": "medium", "verified": True, "source": "Amazon",
            "insights": [
                {"id": "ins_clf9_002a", "aspect": "rocker", "sentiment": "positive", "relevantToNarrow": False,
                 "quote": "Rocker geometry felt weird for the first mile but now I can't imagine running without it.", "confidence": 0.89},
            ],
        },
        {
            "id": "rev_clf9_003",
            "text": "Love the cushion but the outsole wore through in 3 months and about 250 miles. For $145 I expected more durability. The foam itself is still fine but the rubber is paper thin in the forefoot.",
            "rating": 3, "authorWidth": "medium", "verified": True, "source": "Fleet Feet",
            "insights": [
                {"id": "ins_clf9_003a", "aspect": "durability", "sentiment": "negative", "relevantToNarrow": False,
                 "quote": "Outsole wore through in 3 months and about 250 miles.", "confidence": 0.94},
            ],
        },
        {
            "id": "rev_clf9_004",
            "text": "Compared this to the Nike Vomero 17 and the Clifton wins on weight by over an ounce. Both are max cushion but the Hoka rocker makes turnover feel effortless on my daily 8-milers.",
            "rating": 5, "authorWidth": "medium", "verified": True, "source": "Strava",
            "insights": [
                {"id": "ins_clf9_004a", "aspect": "weight", "sentiment": "positive", "relevantToNarrow": False,
                 "quote": "Wins on weight by over an ounce vs Nike Vomero 17.", "confidence": 0.91},
            ],
        },
        {
            "id": "rev_clf9_005",
            "text": "Wide version fits my EE feet perfectly. The meta-rocker takes pressure off my plantar fascia in a way that high-drop shoes never did. My podiatrist was surprised at the improvement.",
            "rating": 5, "authorWidth": "wide", "verified": True, "source": "Amazon",
            "insights": [
                {"id": "ins_clf9_005a", "aspect": "cushioning", "sentiment": "positive", "relevantToNarrow": False,
                 "quote": "Meta-rocker takes pressure off my plantar fascia in a way that high-drop shoes never did.", "confidence": 0.93},
            ],
        },
        {
            "id": "rev_clf9_006",
            "text": "Perfect out of the box, no break-in needed. I ran 6 miles the day they arrived and had zero hot spots. The breathable mesh keeps my feet cool even on 90-degree summer runs.",
            "rating": 5, "authorWidth": "medium", "verified": True, "source": "RunnerWorld",
            "insights": [
                {"id": "ins_clf9_006a", "aspect": "overall-fit", "sentiment": "positive", "relevantToNarrow": False,
                 "quote": "Perfect out of the box, no break-in needed.", "confidence": 0.95},
            ],
        },
        {
            "id": "rev_clf9_007",
            "text": "Great beginner shoe. I went from walking to running in these and never had shin splints like I did in my old sneakers. The cushion absorbs everything.",
            "rating": 5, "authorWidth": "medium", "verified": True, "source": "Reddit",
            "insights": [
                {"id": "ins_clf9_007a", "aspect": "cushioning", "sentiment": "positive", "relevantToNarrow": False,
                 "quote": "Never had shin splints like I did in my old sneakers.", "confidence": 0.90},
            ],
        },
    ],
    "nike_vomero_17": [
        {
            "id": "rev_vom17_001",
            "text": "Best daily trainer Nike has made in years. The ZoomX foam is the same as the Vaporfly but in a wider, more stable package. I log 50 miles a week in these for marathon training.",
            "rating": 5, "authorWidth": "medium", "verified": True, "source": "RunnerWorld",
            "insights": [
                {"id": "ins_vom17_001a", "aspect": "cushioning", "sentiment": "positive", "relevantToNarrow": False,
                 "quote": "ZoomX foam is the same as the Vaporfly but in a wider, more stable package.", "confidence": 0.94},
            ],
        },
        {
            "id": "rev_vom17_002",
            "text": "The wide version finally fits my feet without the upper looking distorted. Nike has historically been terrible for wide feet but the Vomero 17 wide is genuinely roomy.",
            "rating": 4, "authorWidth": "wide", "verified": True, "source": "Amazon",
            "insights": [
                {"id": "ins_vom17_002a", "aspect": "overall-fit", "sentiment": "positive", "relevantToNarrow": False,
                 "quote": "Nike has historically been terrible for wide feet but the Vomero 17 wide is genuinely roomy.", "confidence": 0.92},
            ],
        },
        {
            "id": "rev_vom17_003",
            "text": "Ran a 3:15 marathon in these as my training shoe. They feel heavy at 10oz compared to my Kinvara but the energy return on long runs is unreal. My legs were fresher at mile 22 than any race before.",
            "rating": 5, "authorWidth": "medium", "verified": True, "source": "Strava",
            "insights": [
                {"id": "ins_vom17_003a", "aspect": "cushioning", "sentiment": "positive", "relevantToNarrow": False,
                 "quote": "Energy return on long runs is unreal. Legs fresher at mile 22 than any race before.", "confidence": 0.95},
            ],
        },
        {
            "id": "rev_vom17_004",
            "text": "Too narrow in the forefoot for my wide feet, even in the wide version. Caused bunion pain after 4 miles. Returned and went with the Saucony Triumph instead.",
            "rating": 2, "authorWidth": "wide", "verified": True, "source": "Amazon",
            "insights": [
                {"id": "ins_vom17_004a", "aspect": "toe-box", "sentiment": "negative", "relevantToNarrow": False,
                 "quote": "Too narrow in the forefoot, caused bunion pain after 4 miles.", "confidence": 0.96},
            ],
        },
        {
            "id": "rev_vom17_005",
            "text": "Premium price but premium ride. The 10mm drop works well for my heel-striking style. Compared to the Glycerin 21, the Vomero feels more responsive while still being plush.",
            "rating": 4, "authorWidth": "medium", "verified": True, "source": "Fleet Feet",
            "insights": [
                {"id": "ins_vom17_005a", "aspect": "cushioning", "sentiment": "positive", "relevantToNarrow": False,
                 "quote": "More responsive than Glycerin 21 while still being plush.", "confidence": 0.90},
            ],
        },
    ],
    "hoka_arahi_7": [
        {
            "id": "rev_ara7_001",
            "text": "Finally a stability shoe that doesn't feel like a brick. The Arahi 7 is lighter than the Brooks GTS 24 and the J-Frame provides stability without a hard medial post. My overpronation is controlled without that awkward wedge feeling.",
            "rating": 5, "authorWidth": "wide", "verified": True, "source": "RunnerWorld",
            "insights": [
                {"id": "ins_ara7_001a", "aspect": "stability", "sentiment": "positive", "relevantToNarrow": False,
                 "quote": "J-Frame provides stability without a hard medial post. Overpronation controlled without awkward wedge feeling.", "confidence": 0.95},
            ],
        },
        {
            "id": "rev_ara7_002",
            "text": "Wide feet plus overpronation is a tough combo. The Arahi 7 wide handles both. I used to get knee pain around mile 5 in neutral shoes -- haven't felt it once in 200 miles of Arahis.",
            "rating": 5, "authorWidth": "wide", "verified": True, "source": "Amazon",
            "insights": [
                {"id": "ins_ara7_002a", "aspect": "stability", "sentiment": "positive", "relevantToNarrow": False,
                 "quote": "Used to get knee pain around mile 5 in neutral shoes -- haven't felt it once in 200 miles.", "confidence": 0.94},
            ],
        },
        {
            "id": "rev_ara7_003",
            "text": "Budget-friendly stability option at $140. Does 80% of what the ASICS Kayano does at $30 less. The wide option is true to width unlike some brands that just stretch the upper.",
            "rating": 4, "authorWidth": "wide", "verified": True, "source": "Reddit",
            "insights": [
                {"id": "ins_ara7_003a", "aspect": "value", "sentiment": "positive", "relevantToNarrow": False,
                 "quote": "Does 80% of what the Kayano does at $30 less.", "confidence": 0.87},
            ],
        },
        {
            "id": "rev_ara7_004",
            "text": "Trail runner here who also needs stability on road. The 5mm drop and rocker work great on pavement but the outsole is too soft for gravel trails. Strictly a road shoe despite Hoka's trail heritage.",
            "rating": 3, "authorWidth": "medium", "verified": True, "source": "Strava",
            "insights": [
                {"id": "ins_ara7_004a", "aspect": "durability", "sentiment": "negative", "relevantToNarrow": False,
                 "quote": "Outsole is too soft for gravel trails. Strictly a road shoe.", "confidence": 0.85},
            ],
        },
        {
            "id": "rev_ara7_005",
            "text": "Switched from ASICS GT-2000 and the Arahi is softer underfoot but equally stable. The heel lock is snug without being constricting. Perfect for my 30 miles per week training plan.",
            "rating": 5, "authorWidth": "medium", "verified": True, "source": "Fleet Feet",
            "insights": [
                {"id": "ins_ara7_005a", "aspect": "heel", "sentiment": "positive", "relevantToNarrow": False,
                 "quote": "Heel lock is snug without being constricting.", "confidence": 0.92},
            ],
        },
    ],
    "on_cloud_5": [
        {
            "id": "rev_cld5_001",
            "text": "I wear these to the gym and for casual walks. They look great with jeans and are comfortable enough for 3-4 miles on the treadmill. Not a performance running shoe but an excellent lifestyle crossover.",
            "rating": 4, "authorWidth": "medium", "verified": True, "source": "Amazon",
            "insights": [
                {"id": "ins_cld5_001a", "aspect": "versatility", "sentiment": "positive", "relevantToNarrow": False,
                 "quote": "Look great with jeans and comfortable enough for 3-4 miles on the treadmill.", "confidence": 0.90},
            ],
        },
        {
            "id": "rev_cld5_002",
            "text": "As a new runner I wanted something that works at the gym and on short jogs. The Cloud 5 is perfect for my 2-3 mile runs while I build up. Cushioning is firm compared to Hoka but I like the ground feel.",
            "rating": 4, "authorWidth": "medium", "verified": True, "source": "Fleet Feet",
            "insights": [
                {"id": "ins_cld5_002a", "aspect": "cushioning", "sentiment": "neutral", "relevantToNarrow": False,
                 "quote": "Cushioning is firm compared to Hoka but I like the ground feel.", "confidence": 0.85},
            ],
        },
        {
            "id": "rev_cld5_003",
            "text": "Tried to use these for a 10K and regretted it by mile 4. They don't have enough cushion for distance running. For walking and gym work they're excellent though. Know what you're getting.",
            "rating": 3, "authorWidth": "medium", "verified": True, "source": "Reddit",
            "insights": [
                {"id": "ins_cld5_003a", "aspect": "cushioning", "sentiment": "negative", "relevantToNarrow": False,
                 "quote": "Don't have enough cushion for distance running.", "confidence": 0.93},
            ],
        },
        {
            "id": "rev_cld5_004",
            "text": "The wide version is new and it actually fits my wide feet. Previous On shoes were too narrow. Great all-day comfort shoe for standing at work then hitting the gym after.",
            "rating": 4, "authorWidth": "wide", "verified": True, "source": "Amazon",
            "insights": [
                {"id": "ins_cld5_004a", "aspect": "overall-fit", "sentiment": "positive", "relevantToNarrow": False,
                 "quote": "Wide version actually fits my wide feet. Previous On shoes were too narrow.", "confidence": 0.91},
            ],
        },
    ],
    "asics_gt2000_12": [
        {
            "id": "rev_gt2k_001",
            "text": "The GT-2000 12 in narrow is perfect for my small, narrow feet that overpronate. Mild stability without being heavy. I use these for my daily 5-mile commute run and they handle sidewalks and light trails equally well.",
            "rating": 5, "authorWidth": "narrow", "verified": True, "source": "Fleet Feet",
            "insights": [
                {"id": "ins_gt2k_001a", "aspect": "stability", "sentiment": "positive", "relevantToNarrow": True,
                 "quote": "Mild stability without being heavy. Perfect for narrow feet that overpronate.", "confidence": 0.95},
            ],
        },
        {
            "id": "rev_gt2k_002",
            "text": "Best value stability shoe on the market at $130. Does everything the Kayano does for $40 less. The narrow option fits my AA feet better than any Brooks stability shoe I've tried.",
            "rating": 5, "authorWidth": "narrow", "verified": True, "source": "Amazon",
            "insights": [
                {"id": "ins_gt2k_002a", "aspect": "value", "sentiment": "positive", "relevantToNarrow": True,
                 "quote": "Does everything the Kayano does for $40 less. Narrow option fits AA feet better than any Brooks stability shoe.", "confidence": 0.93},
            ],
        },
        {
            "id": "rev_gt2k_003",
            "text": "I rotate between the GT-2000 12 and the Kinvara 14 -- the ASICS for easy/recovery days when I want stability, the Saucony for tempo days. Having both narrow options is a game changer.",
            "rating": 4, "authorWidth": "narrow", "verified": True, "source": "Strava",
            "insights": [
                {"id": "ins_gt2k_003a", "aspect": "overall-fit", "sentiment": "positive", "relevantToNarrow": True,
                 "quote": "Rotate between GT-2000 12 and Kinvara 14 -- having both narrow options is a game changer.", "confidence": 0.89},
            ],
        },
        {
            "id": "rev_gt2k_004",
            "text": "Wide version is generous. My bunions don't rub at all. The LITETRUSS stability is subtle -- you only notice it when you take it away. Ran my first injury-free training block in years.",
            "rating": 5, "authorWidth": "wide", "verified": True, "source": "RunnerWorld",
            "insights": [
                {"id": "ins_gt2k_004a", "aspect": "stability", "sentiment": "positive", "relevantToNarrow": False,
                 "quote": "LITETRUSS stability is subtle -- you only notice it when you take it away.", "confidence": 0.91},
            ],
        },
        {
            "id": "rev_gt2k_005",
            "text": "Solid workhorse shoe. Not exciting but reliable. I'm on my third pair and each one gives me 400+ miles. The 8mm drop is comfortable for my mild heel striking and my plantar fasciitis stays quiet.",
            "rating": 4, "authorWidth": "medium", "verified": True, "source": "Amazon",
            "insights": [
                {"id": "ins_gt2k_005a", "aspect": "durability", "sentiment": "positive", "relevantToNarrow": False,
                 "quote": "Each pair gives me 400+ miles. Plantar fasciitis stays quiet.", "confidence": 0.92},
            ],
        },
    ],
    "saucony_triumph_22": [
        {
            "id": "rev_tri22_001",
            "text": "The PWRRUN PB foam in the Triumph 22 is insane. It's the same tech as the Endorphin Pro racer but in a daily trainer. I ran a 2:55 marathon training entirely in these for my long runs.",
            "rating": 5, "authorWidth": "medium", "verified": True, "source": "RunnerWorld",
            "insights": [
                {"id": "ins_tri22_001a", "aspect": "cushioning", "sentiment": "positive", "relevantToNarrow": False,
                 "quote": "PWRRUN PB foam -- same tech as the Endorphin Pro racer in a daily trainer.", "confidence": 0.95},
            ],
        },
        {
            "id": "rev_tri22_002",
            "text": "Wide version is spacious in the toe box. I can splay my toes completely. At 10.6oz it's heavier than I'd like for tempo work, but for easy and long runs the cushion is unbeatable.",
            "rating": 4, "authorWidth": "wide", "verified": True, "source": "Fleet Feet",
            "insights": [
                {"id": "ins_tri22_002a", "aspect": "toe-box", "sentiment": "positive", "relevantToNarrow": False,
                 "quote": "Wide version spacious in the toe box. Can splay toes completely.", "confidence": 0.93},
            ],
        },
        {
            "id": "rev_tri22_003",
            "text": "Loved the cushion but the outsole wore through in 3 months at about 300 miles. For $160 I expected better durability. The foam is still bouncy but with no rubber left, wet roads are treacherous.",
            "rating": 3, "authorWidth": "medium", "verified": True, "source": "Amazon",
            "insights": [
                {"id": "ins_tri22_003a", "aspect": "durability", "sentiment": "negative", "relevantToNarrow": False,
                 "quote": "Outsole wore through in 3 months at about 300 miles.", "confidence": 0.94},
            ],
        },
        {
            "id": "rev_tri22_004",
            "text": "Compared to the ASICS Nimbus 25, the Triumph 22 is more responsive and slightly lighter. Both are max cushion but the Saucony feels faster. I alternate between them -- Triumph for tempo long runs, Nimbus for recovery.",
            "rating": 5, "authorWidth": "medium", "verified": True, "source": "Strava",
            "insights": [
                {"id": "ins_tri22_004a", "aspect": "cushioning", "sentiment": "positive", "relevantToNarrow": False,
                 "quote": "More responsive and slightly lighter than ASICS Nimbus 25. Feels faster.", "confidence": 0.91},
            ],
        },
    ],
}

# ---------------------------------------------------------------------------
# Seed Cypher
# ---------------------------------------------------------------------------

def run_seed(uri: str, user: str, password: str):
    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        # Schema
        for q in SCHEMA_QUERIES:
            try:
                session.run(q)
            except Exception as e:
                print(f"Schema warning (may already exist): {e}")

        # Users
        for u in USERS:
            session.run(
                """
                MERGE (u:User {id: $id})
                SET u.name = $name,
                    u.footWidth = $footWidth,
                    u.primarySize = $primarySize,
                    u.fitNotes = $fitNotes,
                    u.stylePrefs = $stylePrefs,
                    u.priceRange = $priceRange,
                    u.totalSessions = $totalSessions,
                    u.createdAt = datetime()
                """,
                **u,
            )
        print(f"Upserted {len(USERS)} users")

        # Shoes (with new properties)
        for s in SHOES:
            session.run(
                """
                MERGE (s:Shoe {id: $id})
                SET s.brand = $brand,
                    s.model = $model,
                    s.sku = $sku,
                    s.widthOptions = $widthOptions,
                    s.availableSizes = $availableSizes,
                    s.price = $price,
                    s.category = $category,
                    s.cushioning = $cushioning,
                    s.drop = $drop,
                    s.weight = $weight,
                    s.stability = $stability,
                    s.releaseYear = $releaseYear,
                    s.colorways = $colorways,
                    s.toeBoxFit = $toeBoxFit,
                    s.heelFit = $heelFit,
                    s.inStock = $inStock,
                    s.url = $url
                """,
                **s,
            )
        print(f"Upserted {len(SHOES)} shoes")

        # ---------------------------------------------------------------
        # PURCHASED relationships (2-4 per user, realistic notes)
        # ---------------------------------------------------------------

        # Alex Chen purchases
        session.run("""
            MATCH (u:User {id: 'alex'}), (s:Shoe {id: 'brooks_ghost_15_n'})
            MERGE (u)-[r:PURCHASED]->(s)
            SET r.date = date('2023-09-15'),
                r.rating = 4,
                r.notes = 'great heel lock, toe box snug around mile 8'
        """)
        session.run("""
            MATCH (u:User {id: 'alex'}), (s:Shoe {id: 'asics_kayano_28_n'})
            MERGE (u)-[r:PURCHASED]->(s)
            SET r.date = date('2024-01-10'),
                r.rating = 3,
                r.notes = 'heavier than expected, good for long slow runs but felt sluggish on tempo days'
        """)
        session.run("""
            MATCH (u:User {id: 'alex'}), (s:Shoe {id: 'saucony_kinvara_14_n'})
            MERGE (u)-[r:PURCHASED]->(s)
            SET r.date = date('2024-06-12'),
                r.rating = 5,
                r.notes = 'perfect out of the box, no break-in needed. Heel lock is the best I have found.'
        """)

        # Priya Patel purchases
        session.run("""
            MATCH (u:User {id: 'priya'}), (s:Shoe {id: 'brooks_adrenaline_gts24'})
            MERGE (u)-[r:PURCHASED]->(s)
            SET r.date = date('2024-03-20'),
                r.rating = 5,
                r.notes = 'GuideRails finally solved my overpronation. Extra-wide fits my bunions perfectly.'
        """)
        session.run("""
            MATCH (u:User {id: 'priya'}), (s:Shoe {id: 'hoka_arahi_7'})
            MERGE (u)-[r:PURCHASED]->(s)
            SET r.date = date('2024-07-15'),
                r.rating = 4,
                r.notes = 'softer than the GTS 24 but equally stable. Prefer these for longer trail-adjacent runs.'
        """)
        session.run("""
            MATCH (u:User {id: 'priya'}), (s:Shoe {id: 'asics_gt2000_12'})
            MERGE (u)-[r:PURCHASED]->(s)
            SET r.date = date('2024-01-05'),
                r.rating = 3,
                r.notes = 'decent stability but arch support collapsed after 200 miles. Switched to Brooks.'
        """)

        # Marcus Johnson purchases
        session.run("""
            MATCH (u:User {id: 'marcus'}), (s:Shoe {id: 'nike_vomero_17'})
            MERGE (u)-[r:PURCHASED]->(s)
            SET r.date = date('2024-04-01'),
                r.rating = 5,
                r.notes = 'ZoomX foam is incredible for marathon training. Logged 600 miles and still bouncy.'
        """)
        session.run("""
            MATCH (u:User {id: 'marcus'}), (s:Shoe {id: 'saucony_kinvara_14_n'})
            MERGE (u)-[r:PURCHASED]->(s)
            SET r.date = date('2024-02-10'),
                r.rating = 4,
                r.notes = 'great tempo shoe, too firm for 20-milers. Use it for speed work only.'
        """)
        session.run("""
            MATCH (u:User {id: 'marcus'}), (s:Shoe {id: 'asics_nimbus_25_n'})
            MERGE (u)-[r:PURCHASED]->(s)
            SET r.date = date('2024-06-01'),
                r.rating = 5,
                r.notes = 'my go-to long run shoe. Plush enough for 22-mile days. Used for Boston training block.'
        """)
        session.run("""
            MATCH (u:User {id: 'marcus'}), (s:Shoe {id: 'saucony_triumph_22'})
            MERGE (u)-[r:PURCHASED]->(s)
            SET r.date = date('2024-08-15'),
                r.rating = 4,
                r.notes = 'PWRRUN PB foam is amazing but outsole durability is mediocre. 300 miles and rubber is thinning.'
        """)

        # Sarah Kim purchases
        session.run("""
            MATCH (u:User {id: 'sarah'}), (s:Shoe {id: 'hoka_bondi_8'})
            MERGE (u)-[r:PURCHASED]->(s)
            SET r.date = date('2024-05-20'),
                r.rating = 4,
                r.notes = 'max cushion helps my plantar fasciitis. Rocker geometry takes pressure off the heel. A bit wide for my narrow feet though.'
        """)
        session.run("""
            MATCH (u:User {id: 'sarah'}), (s:Shoe {id: 'on_cloud_5'})
            MERGE (u)-[r:PURCHASED]->(s)
            SET r.date = date('2024-02-10'),
                r.rating = 3,
                r.notes = 'fine for gym and errands but not enough cushion for my plantar fasciitis on longer walks.'
        """)

        # James Rodriguez purchases
        session.run("""
            MATCH (u:User {id: 'james'}), (s:Shoe {id: 'saucony_kinvara_14_n'})
            MERGE (u)-[r:PURCHASED]->(s)
            SET r.date = date('2024-03-01'),
                r.rating = 4,
                r.notes = 'lightweight and fast. Good for speed work. Forefoot is a bit narrow for my wide foot though.'
        """)
        session.run("""
            MATCH (u:User {id: 'james'}), (s:Shoe {id: 'hoka_clifton_9'})
            MERGE (u)-[r:PURCHASED]->(s)
            SET r.date = date('2024-06-20'),
                r.rating = 5,
                r.notes = 'lightest max-cushion shoe I have tried. Wide version fits my forefoot. Great for recovery runs between track sessions.'
        """)
        session.run("""
            MATCH (u:User {id: 'james'}), (s:Shoe {id: 'nike_pegasus_40'})
            MERGE (u)-[r:PURCHASED]->(s)
            SET r.date = date('2024-01-15'),
                r.rating = 3,
                r.notes = 'solid all-arounder but nothing special. Too heavy for track work at 9.6oz.'
        """)

        # Emma Wilson purchases
        session.run("""
            MATCH (u:User {id: 'emma'}), (s:Shoe {id: 'on_cloud_5'})
            MERGE (u)-[r:PURCHASED]->(s)
            SET r.date = date('2024-08-01'),
                r.rating = 3,
                r.notes = 'bought for gym and first runs. Looks great but started getting shin splints at 2 miles. Might need more cushion.'
        """)

        # Jordan Kim purchases
        for shoe_data in [
            ("saucony_kinvara_14_n", "2024-02-01", 5, "perfect for narrow feet, heel lock is outstanding"),
            ("asics_nimbus_25_n", "2024-03-15", 4, "great support for narrow width, best arch support I have found"),
            ("nb_1080v13_n", "2024-04-01", 5, "best cushion for narrow foot, roomy toe box without being sloppy"),
        ]:
            session.run(
                """
                MATCH (u:User {id: 'user_jordan'}), (s:Shoe {id: $shoe_id})
                MERGE (u)-[r:PURCHASED]->(s)
                SET r.date = date($date), r.rating = $rating, r.notes = $notes
                """,
                shoe_id=shoe_data[0], date=shoe_data[1], rating=shoe_data[2], notes=shoe_data[3],
            )

        # Sam Rivera purchases
        for shoe_data in [
            ("saucony_kinvara_14_n", "2024-02-15", 5, "lightweight and versatile, works on light trails too"),
            ("asics_nimbus_25_n", "2024-04-10", 4, "plush for recovery days, narrow fits my feet well"),
            ("nb_1080v13_n", "2024-05-01", 5, "best all-around narrow shoe, my daily driver"),
            ("asics_gt2000_12", "2024-07-01", 4, "mild stability for when my form breaks down on long runs"),
        ]:
            session.run(
                """
                MATCH (u:User {id: 'user_sam'}), (s:Shoe {id: $shoe_id})
                MERGE (u)-[r:PURCHASED]->(s)
                SET r.date = date($date), r.rating = $rating, r.notes = $notes
                """,
                shoe_id=shoe_data[0], date=shoe_data[1], rating=shoe_data[2], notes=shoe_data[3],
            )

        print("Upserted purchase relationships")

        # ---------------------------------------------------------------
        # REJECTED relationships (1-3 per user, realistic reasons)
        # ---------------------------------------------------------------
        rejections = [
            ("alex", "nike_pegasus_40", "too wide in midfoot, foot slides on turns", "2023-06-01"),
            ("alex", "hoka_bondi_8", "rocker sole throws off my gait, too squishy for tempo work", "2023-11-20"),
            ("priya", "nike_pegasus_40", "no stability support, ankle rolled twice in the first week", "2023-09-10"),
            ("priya", "saucony_kinvara_14_n", "way too narrow for my wide feet, could not even lace them comfortably", "2024-01-20"),
            ("marcus", "hoka_bondi_8", "too heavy for marathon training at 10.8oz, felt like bricks after mile 15", "2023-12-05"),
            ("marcus", "brooks_ghost_15_n", "too much heel drop at 12mm, aggravated my calf tightness", "2024-01-20"),
            ("sarah", "saucony_kinvara_14_n", "minimal cushioning made my plantar fasciitis flare up immediately", "2024-04-01"),
            ("sarah", "nike_pegasus_40", "too wide, foot slid around and aggravated my heel pain", "2024-03-15"),
            ("james", "hoka_bondi_8", "way too heavy for speed work, felt like running in sand", "2024-02-01"),
            ("james", "asics_kayano_28_n", "stability features interfere with my sprinting form", "2024-04-10"),
            ("james", "brooks_glycerin_21_n", "too soft, no ground feel for track sessions", "2024-05-01"),
            ("emma", "nike_invincible_3", "too expensive for a beginner, and the wobbly feel scared me", "2024-07-20"),
            ("user_jordan", "nike_pegasus_40", "too wide in the heel, constant slipping", "2023-08-15"),
            ("user_sam", "hoka_bondi_8", "rocker too aggressive for trail running, ankle instability on roots", "2024-01-10"),
        ]
        for uid, shoe_id, reason, date in rejections:
            session.run(
                """
                MATCH (u:User {id: $uid}), (s:Shoe {id: $shoe_id})
                MERGE (u)-[r:REJECTED]->(s)
                SET r.reason = $reason, r.date = date($date)
                """,
                uid=uid, shoe_id=shoe_id, reason=reason, date=date,
            )
        print(f"Upserted {len(rejections)} rejection relationships")

        # ---------------------------------------------------------------
        # VIEWED relationships with counts and timestamps
        # ---------------------------------------------------------------
        views = [
            # Alex: researching carefully
            ("alex", "saucony_kinvara_14_n", 7, "2024-06-17T09:20:00"),
            ("alex", "asics_nimbus_25_n", 4, "2024-06-17T09:16:00"),
            ("alex", "nb_1080v13_n", 3, "2024-06-12T14:30:00"),
            ("alex", "brooks_glycerin_21_n", 1, "2024-05-02T11:00:00"),
            ("alex", "saucony_ride_17_n", 2, "2024-06-10T14:35:00"),
            # Priya: comparing stability options
            ("priya", "brooks_adrenaline_gts24", 6, "2024-07-20T10:00:00"),
            ("priya", "hoka_arahi_7", 5, "2024-07-18T15:30:00"),
            ("priya", "asics_gt2000_12", 4, "2024-03-01T09:00:00"),
            ("priya", "brooks_adrenaline_gts23_n", 2, "2024-02-15T14:00:00"),
            ("priya", "asics_kayano_28_n", 3, "2024-01-10T11:00:00"),
            # Marcus: marathon researcher
            ("marcus", "nike_vomero_17", 8, "2024-08-20T07:30:00"),
            ("marcus", "saucony_triumph_22", 5, "2024-08-18T19:00:00"),
            ("marcus", "asics_nimbus_25_n", 4, "2024-06-05T12:00:00"),
            ("marcus", "nike_invincible_3", 3, "2024-07-10T08:00:00"),
            ("marcus", "brooks_glycerin_21_n", 2, "2024-05-15T16:00:00"),
            # Sarah: plantar fasciitis research
            ("sarah", "hoka_bondi_8", 6, "2024-05-25T13:00:00"),
            ("sarah", "hoka_clifton_9", 4, "2024-06-01T10:00:00"),
            ("sarah", "brooks_glycerin_21_n", 3, "2024-05-10T14:00:00"),
            ("sarah", "asics_nimbus_25_n", 2, "2024-04-20T11:00:00"),
            ("sarah", "nike_invincible_3", 1, "2024-07-18T16:00:00"),
            # James: speed-focused browsing
            ("james", "saucony_kinvara_14_n", 5, "2024-06-25T06:30:00"),
            ("james", "hoka_clifton_9", 4, "2024-06-22T07:00:00"),
            ("james", "nike_pegasus_40", 3, "2024-01-20T18:00:00"),
            ("james", "saucony_ride_17_n", 2, "2024-05-15T12:00:00"),
            # Emma: exploring as a new runner
            ("emma", "hoka_clifton_9", 5, "2024-08-10T20:00:00"),
            ("emma", "on_cloud_5", 3, "2024-07-25T19:00:00"),
            ("emma", "brooks_ghost_15_n", 2, "2024-08-05T21:00:00"),
            ("emma", "nike_pegasus_40", 2, "2024-08-08T18:00:00"),
            ("emma", "asics_gt2000_12", 1, "2024-08-12T14:00:00"),
            # Jordan and Sam: occasional browsing
            ("user_jordan", "saucony_ride_17_n", 3, "2024-05-20T10:00:00"),
            ("user_jordan", "asics_gel_nimbus_lite4_n", 2, "2024-06-01T15:00:00"),
            ("user_sam", "brooks_ghost_15_n", 2, "2024-03-10T09:00:00"),
            ("user_sam", "hoka_clifton_9", 1, "2024-06-15T12:00:00"),
        ]
        for uid, shoe_id, count, last_viewed in views:
            session.run(
                """
                MATCH (u:User {id: $uid}), (s:Shoe {id: $shoe_id})
                MERGE (u)-[v:VIEWED]->(s)
                SET v.count = $count, v.lastViewed = datetime($lastViewed)
                """,
                uid=uid, shoe_id=shoe_id, count=count, lastViewed=last_viewed,
            )
        print(f"Upserted {len(views)} view relationships")

        # ---------------------------------------------------------------
        # SIMILAR_TO relationships (based on shared attributes)
        # ---------------------------------------------------------------
        similarities = [
            # Narrow foot cluster
            ("alex", "user_jordan", ["footWidth:narrow", "stylePrefs:road running", "heelFit:snug preference"]),
            ("alex", "user_sam", ["footWidth:narrow", "stylePrefs:road running"]),
            ("alex", "sarah", ["footWidth:narrow", "plantar fasciitis awareness"]),
            ("user_jordan", "user_sam", ["footWidth:narrow", "stylePrefs:road running", "overlapping purchases"]),
            # Wide foot + stability cluster
            ("priya", "james", ["footWidth:wide", "need wide/extra-wide options"]),
            # Marathon / high-mileage cluster
            ("marcus", "user_sam", ["stylePrefs:road running", "high mileage training"]),
            ("marcus", "user_jordan", ["stylePrefs:road running", "overlapping purchases:kinvara"]),
            # New runner + casual cluster
            ("emma", "sarah", ["stylePrefs:gym training", "lifestyle crossover", "cushion preference"]),
            # Overpronation cluster
            ("priya", "user_jordan", ["overpronation concerns", "stability shoe preference"]),
        ]
        for uid_a, uid_b, shared in similarities:
            session.run(
                """
                MATCH (a:User {id: $uid_a}), (b:User {id: $uid_b})
                MERGE (a)-[r:SIMILAR_TO]->(b)
                SET r.sharedAttributes = $shared
                """,
                uid_a=uid_a, uid_b=uid_b, shared=shared,
            )
        print(f"Upserted {len(similarities)} similarity relationships")

        # Reviews + Insights
        review_count = 0
        insight_count = 0
        for shoe_id, reviews in REVIEWS_DATA.items():
            for rev in reviews:
                insights = rev.pop("insights", [])
                session.run(
                    """
                    MERGE (r:Review {id: $id})
                    SET r.text = $text, r.rating = $rating,
                        r.authorWidth = $authorWidth,
                        r.verified = $verified, r.source = $source,
                        r.date = date()
                    WITH r
                    MATCH (s:Shoe {id: $shoe_id})
                    MERGE (s)-[:HAS_REVIEW]->(r)
                    """,
                    shoe_id=shoe_id,
                    **rev,
                )
                review_count += 1
                for ins in insights:
                    session.run(
                        """
                        MERGE (i:ReviewInsight {id: $id})
                        SET i.aspect = $aspect, i.sentiment = $sentiment,
                            i.relevantToNarrow = $relevantToNarrow,
                            i.quote = $quote, i.confidence = $confidence
                        WITH i
                        MATCH (r:Review {id: $rev_id})
                        MERGE (r)-[:CONTAINS_INSIGHT]->(i)
                        WITH i
                        MATCH (s:Shoe {id: $shoe_id})
                        MERGE (i)-[:ABOUT]->(s)
                        """,
                        rev_id=rev["id"],
                        shoe_id=shoe_id,
                        **ins,
                    )
                    insight_count += 1
        print(f"Upserted {review_count} reviews, {insight_count} insights")

        # ==================================================================
        # THREE MEMORY TYPES -- the core value prop of neo4j-agent-memory
        #
        # 1. SHORT-TERM MEMORY: Current session messages (Conversation ->
        #    FIRST_MESSAGE -> Message -> NEXT_MESSAGE -> Message chain)
        #
        # 2. LONG-TERM MEMORY: Cross-session user profile, preferences,
        #    purchase history, entity resolution across interactions
        #    (User properties + PURCHASED/REJECTED/VIEWED/SIMILAR_TO rels)
        #
        # 3. REASONING MEMORY: Decision traces, recommendations, and the
        #    causal chains the agent used to arrive at decisions
        #    (DecisionTrace -> PART_OF -> Conversation, LED_TO -> Recommendation)
        # ==================================================================

        # ------------------------------------------------------------------
        # SESSION 1 (4 weeks ago) -- Alex's first interaction, no context
        # Shows: painful cold-start without long-term memory
        # The agent asks redundant questions, recommends a shoe Alex already
        # rejected (Pegasus 40), and cannot verify fit or availability.
        # ------------------------------------------------------------------
        session.run("""
            MERGE (c:Conversation {id: 'conv_session_1'})
            SET c.startTime = datetime('2024-05-01T10:00:00'),
                c.endTime = datetime('2024-05-01T10:37:00'),
                c.intent = 'shoe recommendation',
                c.resolved = false,
                c.timeToDecisionSeconds = 2220,
                c.questionCount = 8,
                c.factsRecalled = 0,
                c.graphHops = 0,
                c.hasContextGraph = false,
                c.memoryType = 'none'
            WITH c
            MATCH (u:User {id: 'alex'})
            MERGE (u)-[:HAD_CONVERSATION]->(c)
        """)
        # Short-term memory: message chain for session 1
        # 12 messages of painful back-and-forth culminating in a bad generic rec
        s1_msgs = [
            ("s1_m1", "user",
             "I need running shoes",
             "2024-05-01T10:00:00"),
            ("s1_m2", "assistant",
             "I would be happy to help you find running shoes! What size do you wear?",
             "2024-05-01T10:00:15"),
            ("s1_m3", "user",
             "9.5",
             "2024-05-01T10:01:30"),
            ("s1_m4", "assistant",
             "Great. Do you have narrow, medium, or wide feet?",
             "2024-05-01T10:01:45"),
            ("s1_m5", "user",
             "Narrow",
             "2024-05-01T10:03:00"),
            ("s1_m6", "assistant",
             "Thanks. What is your budget range?",
             "2024-05-01T10:03:15"),
            ("s1_m7", "user",
             "Around 130-150",
             "2024-05-01T10:05:00"),
            ("s1_m8", "assistant",
             "And what type of running do you do -- road, trail, or gym?",
             "2024-05-01T10:05:15"),
            ("s1_m9", "user",
             "Road running mostly",
             "2024-05-01T10:07:00"),
            ("s1_m10", "assistant",
             "Do you have any preferences for cushioning level -- minimal, moderate, or maximum?",
             "2024-05-01T10:07:15"),
            ("s1_m11", "user",
             "Moderate I guess. I liked my Brooks Ghost but the toe box got tight on long runs. And I tried Nike Pegasus and hated it -- way too wide.",
             "2024-05-01T10:10:00"),
            ("s1_m12", "assistant",
             "Based on what you told me, here are some popular suggestions: 1. Nike Pegasus 40 -- a versatile daily trainer at $135. 2. ASICS Gel-Nimbus 25 -- plush cushioning for long runs. 3. Brooks Glycerin 21 -- premium cushioned ride. I do not have information on which models come in narrow width or your specific availability. You may want to check a local running store for a fit test.",
             "2024-05-01T10:12:00"),
        ]
        for i, (mid, role, content, ts) in enumerate(s1_msgs):
            session.run("""
                MERGE (m:Message {id: $mid})
                SET m.role = $role, m.content = $content, m.timestamp = datetime($ts)
            """, mid=mid, role=role, content=content, ts=ts)
            if i == 0:
                session.run("""
                    MATCH (c:Conversation {id: 'conv_session_1'}), (m:Message {id: $mid})
                    MERGE (c)-[:FIRST_MESSAGE]->(m)
                """, mid=mid)
            else:
                prev_mid = s1_msgs[i - 1][0]
                session.run("""
                    MATCH (prev:Message {id: $prev}), (m:Message {id: $mid})
                    MERGE (prev)-[:NEXT_MESSAGE]->(m)
                """, prev=prev_mid, mid=mid)

        # ------------------------------------------------------------------
        # SESSION 2 (2 weeks ago) -- With context graph
        # Shows: SHORT-TERM + LONG-TERM + REASONING memory all working
        # Agent references specific review quotes, avoids rejected shoes,
        # and cross-references with similar users.
        # ------------------------------------------------------------------
        session.run("""
            MERGE (c:Conversation {id: 'conv_session_2'})
            SET c.startTime = datetime('2024-06-10T14:30:00'),
                c.endTime = datetime('2024-06-10T14:34:12'),
                c.intent = 'shoe recommendation',
                c.resolved = true,
                c.timeToDecisionSeconds = 252,
                c.questionCount = 0,
                c.factsRecalled = 6,
                c.graphHops = 8,
                c.hasContextGraph = true,
                c.memoryType = 'full'
            WITH c
            MATCH (u:User {id: 'alex'})
            MERGE (u)-[:HAD_CONVERSATION]->(c)
        """)
        # Session 2 was INFORMED_BY Session 1 (cross-session learning)
        session.run("""
            MATCH (c2:Conversation {id: 'conv_session_2'}),
                  (c1:Conversation {id: 'conv_session_1'})
            MERGE (c2)-[:INFORMED_BY]->(c1)
        """)

        # Short-term memory: message chain for session 2
        s2_msgs = [
            ("s2_m1", "user",
             "I need new running shoes for road training",
             "2024-06-10T14:30:00"),
            ("s2_m2", "assistant",
             "Welcome back, Alex. From your profile: narrow width (AA), size 9.5, $100-150 budget. You rated Brooks Ghost 15N 4 stars (great heel lock, toe box snug around mile 8) and Asics Kayano 28N 3 stars (heavier than expected). I see you rejected the Nike Pegasus 40 (too wide in midfoot) and the Hoka Bondi 8 (rocker throws off your gait) so I will exclude those. Checking 3 similar narrow-footed users (Jordan, Sam, and Morgan) who overlap with your purchase history. Here are my top picks:\n\n1. Saucony Kinvara 14N -- 91% match. $139.95, in stock. 4mm drop, 7.8oz. 12 positive narrow-foot review insights. Jordan, Sam, and Morgan all rated it 5 stars.\n2. Asics Nimbus 25N -- 88% match. $149.95, in stock. 8mm drop, more cushion than the Ghost. From review: \"Asics narrow width is the gold standard.\"\n3. NB Fresh Foam 1080v13N -- 84% match. $129.95 (lowest price). Roomy toe box addresses your Ghost 15 complaint about tightness at mile 8. Review quote: \"Toe box is surprisingly roomy for a narrow shoe.\"",
             "2024-06-10T14:30:08"),
            ("s2_m3", "user",
             "Tell me more about the Kinvara 14N heel fit -- that is the most important thing for me",
             "2024-06-10T14:31:20"),
            ("s2_m4", "assistant",
             "Great question. From 12 narrow-foot reviews on the Kinvara 14N, here are the heel-specific insights:\n\n- \"Heel locks in immediately\" (5 stars, verified, RunnerWorld, confidence 0.97)\n- \"Narrow heels stayed put the entire race\" (4 stars, Strava half marathon runner, confidence 0.94)\n- \"Heel cradle is tighter which I love -- switched from a Brooks Ghost\" (5 stars, verified, RunnerWorld, confidence 0.92)\n- \"Heel stayed locked even downhill\" during a full marathon (5 stars, verified, confidence 0.96)\n\nThis matches your long-term preference: you noted the Ghost 15N had \"great heel lock\" which you rated as your favorite feature. The Kinvara 14N appears to match or exceed that based on the reviewer who directly compared the two shoes. Also worth noting: the reviewer who switched from Brooks Ghost specifically called out the tighter heel cradle as an improvement.",
             "2024-06-10T14:31:28"),
            ("s2_m5", "user",
             "That sounds perfect. I will go with the Kinvara 14N. What about the similar user who bought it -- any long-term issues?",
             "2024-06-10T14:33:00"),
            ("s2_m6", "assistant",
             "All three similar users (Jordan, Sam, Morgan) rated the Kinvara 14N 5 stars with no reported issues. Jordan has logged the most miles and noted the heel lock as \"outstanding.\" Sam called it \"lightweight and versatile.\" No durability complaints in any of their notes.\n\nI have saved this decision to your profile. The Saucony Kinvara 14N in size 9.5 narrow is $139.95 and in stock. Based on your Ghost 15 experience, you should be true to size in Saucony. I have logged the full decision trace with provenance for future reference -- this means next time you come back, I will remember what worked and why.",
             "2024-06-10T14:33:10"),
        ]
        for i, (mid, role, content, ts) in enumerate(s2_msgs):
            session.run("""
                MERGE (m:Message {id: $mid})
                SET m.role = $role, m.content = $content, m.timestamp = datetime($ts)
            """, mid=mid, role=role, content=content, ts=ts)
            if i == 0:
                session.run("""
                    MATCH (c:Conversation {id: 'conv_session_2'}), (m:Message {id: $mid})
                    MERGE (c)-[:FIRST_MESSAGE]->(m)
                """, mid=mid)
            else:
                prev_mid = s2_msgs[i - 1][0]
                session.run("""
                    MATCH (prev:Message {id: $prev}), (m:Message {id: $mid})
                    MERGE (prev)-[:NEXT_MESSAGE]->(m)
                """, prev=prev_mid, mid=mid)

        # ------------------------------------------------------------------
        # REASONING MEMORY: Decision traces for Session 2
        # Full audit trail -- tool invocation, parameters, results, reasoning
        # ------------------------------------------------------------------

        # DT1: Load user profile from long-term memory
        session.run("""
            MERGE (dt:DecisionTrace {id: 'dt_001'})
            SET dt.toolName = 'execute_cypher',
                dt.cypherQuery = 'MATCH (u:User {id: \"alex\"}) OPTIONAL MATCH (u)-[p:PURCHASED]->(bought:Shoe) OPTIONAL MATCH (u)-[rej:REJECTED]->(r:Shoe) RETURN u, collect({shoe: bought.brand+\" \"+bought.model, rating: p.rating, notes: p.notes}) as purchases, collect({shoe: r.brand+\" \"+r.model, reason: rej.reason}) as rejections',
                dt.reasoning = 'LONG-TERM MEMORY RECALL: Loading Alex full profile -- foot width, size, purchase history, fit notes, and rejection reasons. This eliminates all clarifying questions that plagued session 1 (8 questions, 37 minutes wasted).',
                dt.memoryType = 'long-term',
                dt.timestamp = datetime('2024-06-10T14:30:02'),
                dt.durationMs = 45,
                dt.result = 'Recalled: narrow, 9.5, Ghost 15N rating 4, Kayano 28N rating 3, rejected Pegasus 40 (too wide) and Bondi 8 (rocker gait issue)'
            WITH dt
            MATCH (c:Conversation {id: 'conv_session_2'})
            MERGE (dt)-[:PART_OF]->(c)
            WITH dt
            MATCH (m:Message {id: 's2_m1'})
            MERGE (m)-[:TRIGGERED]->(dt)
        """)

        # DT2: Check reasoning memory for similar past decisions
        session.run("""
            MERGE (dt:DecisionTrace {id: 'dt_002'})
            SET dt.toolName = 'execute_cypher',
                dt.cypherQuery = 'MATCH (u:User {id: \"alex\"})-[:HAD_CONVERSATION]->(past:Conversation)-[:PRODUCED]->(rec:Recommendation)-[:RECOMMENDS]->(s:Shoe) WHERE past.resolved = true RETURN past.id, rec.confidence, s.brand + \" \" + s.model AS shoe, rec.accepted',
                dt.reasoning = 'REASONING MEMORY: Checking if Alex has received prior recommendations -- reusing successful decision patterns instead of starting from scratch.',
                dt.memoryType = 'reasoning',
                dt.timestamp = datetime('2024-06-10T14:30:03'),
                dt.durationMs = 32,
                dt.result = 'No prior accepted recommendations found -- this is a fresh recommendation path'
            WITH dt
            MATCH (c:Conversation {id: 'conv_session_2'})
            MERGE (dt)-[:PART_OF]->(c)
            WITH dt
            MATCH (m:Message {id: 's2_m1'})
            MERGE (m)-[:TRIGGERED]->(dt)
        """)

        # DT3: Cross-user graph traversal for recommendations
        session.run("""
            MERGE (dt:DecisionTrace {id: 'dt_003'})
            SET dt.toolName = 'execute_cypher',
                dt.cypherQuery = 'MATCH (alex:User {id:\"alex\"})-[:PURCHASED]->(s:Shoe)<-[:PURCHASED]-(similar:User {footWidth: \"narrow\"})-[:PURCHASED]->(candidate:Shoe) WHERE NOT (alex)-[:PURCHASED|REJECTED]->(candidate) AND candidate.inStock = true OPTIONAL MATCH (candidate)-[:HAS_REVIEW]->(rv:Review {authorWidth:\"narrow\"})-[:CONTAINS_INSIGHT]->(i:ReviewInsight {sentiment:\"positive\"}) RETURN candidate.brand, candidate.model, candidate.price, count(i) AS narrowInsights, collect(i.quote)[..3] AS quotes ORDER BY narrowInsights DESC LIMIT 3',
                dt.reasoning = 'CONTEXT GRAPH TRAVERSAL: 5-hop query across User->Purchase->Shoe->Review->Insight. Finds shoes bought by similar narrow-footed users, ranked by positive narrow-foot review signals. Single query replaces 6 round-trips in a vector DB. Excludes Pegasus 40 and Bondi 8 (REJECTED rels in long-term memory).',
                dt.memoryType = 'reasoning',
                dt.timestamp = datetime('2024-06-10T14:30:05'),
                dt.durationMs = 135,
                dt.result = 'Found: Kinvara 14N (12 narrow insights, 3 similar users rating 5), Nimbus 25N (10 insights), 1080v13N (9 insights, roomy toe box)'
            WITH dt
            MATCH (c:Conversation {id: 'conv_session_2'})
            MERGE (dt)-[:PART_OF]->(c)
        """)

        # DT4: Heel-specific insight drill-down (triggered by user question)
        session.run("""
            MERGE (dt:DecisionTrace {id: 'dt_004'})
            SET dt.toolName = 'execute_cypher',
                dt.cypherQuery = 'MATCH (s:Shoe {id:\"saucony_kinvara_14_n\"})-[:HAS_REVIEW]->(r:Review {authorWidth:\"narrow\"})-[:CONTAINS_INSIGHT]->(i:ReviewInsight) WHERE i.aspect = \"heel\" RETURN i.quote, i.sentiment, i.confidence ORDER BY i.confidence DESC',
                dt.reasoning = 'SHORT-TERM MEMORY: User asked about heel fit in this session. Drilling into heel-specific review insights for Kinvara 14N from narrow-footed reviewers. Cross-referencing with Alex long-term note that Ghost 15N had great heel lock. Also checking reviewer who compared Ghost to Kinvara directly.',
                dt.memoryType = 'short-term',
                dt.timestamp = datetime('2024-06-10T14:31:22'),
                dt.durationMs = 42,
                dt.result = '4 heel insights found, all positive. Top: Heel locks in immediately (0.97 confidence). One reviewer directly compared Ghost to Kinvara heel favorably.'
            WITH dt
            MATCH (c:Conversation {id: 'conv_session_2'})
            MERGE (dt)-[:PART_OF]->(c)
            WITH dt
            MATCH (m:Message {id: 's2_m3'})
            MERGE (m)-[:TRIGGERED]->(dt)
        """)

        # DT5: Similar-user long-term durability check
        session.run("""
            MERGE (dt:DecisionTrace {id: 'dt_005'})
            SET dt.toolName = 'execute_cypher',
                dt.cypherQuery = 'MATCH (u:User)-[p:PURCHASED]->(s:Shoe {id:\"saucony_kinvara_14_n\"}) WHERE u.footWidth = \"narrow\" RETURN u.name, p.rating, p.notes, p.date ORDER BY p.date DESC',
                dt.reasoning = 'LONG-TERM MEMORY: User asked about similar users durability experience. Checking purchase notes from all narrow-footed users who bought Kinvara 14N for any reported long-term issues.',
                dt.memoryType = 'long-term',
                dt.timestamp = datetime('2024-06-10T14:33:02'),
                dt.durationMs = 38,
                dt.result = 'Jordan: 5 stars, heel lock outstanding. Sam: 5 stars, lightweight and versatile. No durability complaints from any narrow-foot purchaser.'
            WITH dt
            MATCH (c:Conversation {id: 'conv_session_2'})
            MERGE (dt)-[:PART_OF]->(c)
            WITH dt
            MATCH (m:Message {id: 's2_m5'})
            MERGE (m)-[:TRIGGERED]->(dt)
        """)

        # DT6: Write decision back to reasoning memory
        session.run("""
            MERGE (dt:DecisionTrace {id: 'dt_006'})
            SET dt.toolName = 'execute_cypher',
                dt.cypherQuery = 'CREATE (dt2:DecisionTrace {id: randomUUID(), toolName: \"persist_decision\", reasoning: \"Alex chose Kinvara 14N based on cross-user traversal + heel fit review insights + Ghost comparison. This decision pattern can be reused for future narrow-foot running shoe queries.\", timestamp: datetime(), durationMs: 0})',
                dt.reasoning = 'REASONING MEMORY WRITE: Persisting this successful decision pattern back to the graph. Future sessions can find and reuse this trace -- reducing loops, calls, latency, and token usage.',
                dt.memoryType = 'reasoning',
                dt.timestamp = datetime('2024-06-10T14:33:15'),
                dt.durationMs = 25,
                dt.result = 'Decision persisted to reasoning memory with full provenance chain: dt_001 -> dt_003 -> dt_004 -> dt_005 -> rec_001'
            WITH dt
            MATCH (c:Conversation {id: 'conv_session_2'})
            MERGE (dt)-[:PART_OF]->(c)
            WITH dt
            MATCH (m:Message {id: 's2_m5'})
            MERGE (m)-[:TRIGGERED]->(dt)
        """)

        # ------------------------------------------------------------------
        # RECOMMENDATIONS with full provenance chain
        # ------------------------------------------------------------------

        # Rec 1: Kinvara 14N -- accepted
        session.run("""
            MERGE (rec:Recommendation {id: 'rec_001'})
            SET rec.reasoning = 'Cross-user traversal: 3 similar narrow-footed users all purchased Kinvara 14N with 5-star ratings. 12 positive narrow-foot review insights confirm heel and toe-box fit. Long-term memory shows Alex prefers snug heel (Ghost 15N notes). Reviewer who switched from Ghost specifically praised tighter heel cradle. Decision trace dt_003 produced this recommendation.',
                rec.confidence = 0.91,
                rec.rank = 1,
                rec.accepted = true,
                rec.rejectedReason = null,
                rec.memorySource = 'long-term + reasoning'
            WITH rec
            MATCH (c:Conversation {id: 'conv_session_2'})
            MERGE (c)-[:PRODUCED]->(rec)
            WITH rec
            MATCH (s:Shoe {id: 'saucony_kinvara_14_n'})
            MERGE (rec)-[:RECOMMENDS]->(s)
        """)
        # Link decision trace to recommendation (provenance chain)
        session.run("""
            MATCH (dt:DecisionTrace {id: 'dt_003'}), (rec:Recommendation {id: 'rec_001'})
            MERGE (dt)-[:LED_TO]->(rec)
        """)

        # Rec 2: Nimbus 25N
        session.run("""
            MERGE (rec:Recommendation {id: 'rec_002'})
            SET rec.reasoning = 'Same brand as Kayano 28N (long-term memory: already purchased, rated 3 stars). Upgraded cushioning, snug heel confirmed by 10 narrow-foot insights. Review gold standard quote adds confidence. Addresses heavier-than-expected complaint about Kayano by being lighter.',
                rec.confidence = 0.88,
                rec.rank = 2,
                rec.accepted = false,
                rec.rejectedReason = null,
                rec.memorySource = 'long-term + reasoning'
            WITH rec
            MATCH (c:Conversation {id: 'conv_session_2'})
            MERGE (c)-[:PRODUCED]->(rec)
            WITH rec
            MATCH (s:Shoe {id: 'asics_nimbus_25_n'})
            MERGE (rec)-[:RECOMMENDS]->(s)
        """)

        # Rec 3: NB 1080v13N
        session.run("""
            MERGE (rec:Recommendation {id: 'rec_003'})
            SET rec.reasoning = 'Lowest price option ($129.95). Roomy toe box directly addresses Alex long-term memory note: Ghost 15N toe box snug around mile 8. 9 positive narrow-foot insights. Reviewer said: roomy for a narrow shoe. Trade-off: heel cup rated average (not snug) per review.',
                rec.confidence = 0.84,
                rec.rank = 3,
                rec.accepted = false,
                rec.rejectedReason = null,
                rec.memorySource = 'long-term + reasoning'
            WITH rec
            MATCH (c:Conversation {id: 'conv_session_2'})
            MERGE (c)-[:PRODUCED]->(rec)
            WITH rec
            MATCH (s:Shoe {id: 'nb_1080v13_n'})
            MERGE (rec)-[:RECOMMENDS]->(s)
        """)

        # ------------------------------------------------------------------
        # SESSION 3 (1 week ago) -- Return visit, reasoning memory kicks in
        # Shows: agent REUSES past decision traces, avoids repeating work
        # Agent recalls the prior accepted recommendation and knows what
        # did not work from session 2 reasoning memory.
        # ------------------------------------------------------------------
        session.run("""
            MERGE (c:Conversation {id: 'conv_session_3'})
            SET c.startTime = datetime('2024-06-17T09:15:00'),
                c.endTime = datetime('2024-06-17T09:19:45'),
                c.intent = 'follow-up on purchase',
                c.resolved = true,
                c.timeToDecisionSeconds = 150,
                c.questionCount = 0,
                c.factsRecalled = 8,
                c.graphHops = 5,
                c.hasContextGraph = true,
                c.memoryType = 'full'
            WITH c
            MATCH (u:User {id: 'alex'})
            MERGE (u)-[:HAD_CONVERSATION]->(c)
        """)
        session.run("""
            MATCH (c3:Conversation {id: 'conv_session_3'}),
                  (c2:Conversation {id: 'conv_session_2'})
            MERGE (c3)-[:INFORMED_BY]->(c2)
        """)

        s3_msgs = [
            ("s3_m1", "user",
             "I got the Kinvara 14N last week. The heel is perfect like you said but I want something with more cushion for long runs over 15 miles. Same requirements otherwise.",
             "2024-06-17T09:15:00"),
            ("s3_m2", "assistant",
             "Welcome back, Alex! I see from your profile that you purchased the Kinvara 14N (from our session on June 10, decision trace dt_003). Great to hear the heel fit matches the review data -- 4 of 4 heel insights were positive and the reviewer who compared it to the Ghost confirmed the tighter cradle.\n\nFor more cushion with the same narrow/snug heel profile, my reasoning memory from session 2 has two strong candidates you already considered but did not purchase:\n\n1. Asics Nimbus 25N (88% match, $149.95) -- max cushion, 8mm drop. 10 narrow-foot insights all positive. Quote: \"Plush without being sloppy.\" This was your rank 2 from last session.\n2. NB 1080v13N (84% match, $129.95) -- max cushion, roomy toe box. Note: heel cup rated average by one reviewer, which may matter given your heel preference. This was rank 3.\n\nGiven that heel lock is your top priority and the Nimbus 25N has 3 positive heel-specific insights vs the 1080v13N neutral heel rating, I would lean toward the Nimbus. It also has max cushion (vs the Kinvara moderate cushion) which directly addresses your 15-mile comfort need.\n\nShall I pull any updated review data or check inventory?",
             "2024-06-17T09:15:18"),
            ("s3_m3", "user",
             "The Nimbus sounds right. What about the Saucony Triumph 22 -- I saw an ad for it.",
             "2024-06-17T09:17:00"),
            ("s3_m4", "assistant",
             "Good question. The Triumph 22 is max cushion and uses PWRRUN PB foam (same as the Endorphin Pro racer). It is $159.95 -- above your $100-150 range. Key concern: it only comes in medium and wide, not narrow. Given your narrow width and the importance of a snug fit, this would be a risky purchase. One reviewer also noted outsole durability issues at 300 miles.\n\nThe Nimbus 25N remains the stronger pick: narrow width available, proven heel lock from similar users, and within your budget at $149.95. Marcus, one of our marathon trainers, rates it 5 stars and uses it for 22-mile training days.",
             "2024-06-17T09:17:15"),
        ]
        for i, (mid, role, content, ts) in enumerate(s3_msgs):
            session.run("""
                MERGE (m:Message {id: $mid})
                SET m.role = $role, m.content = $content, m.timestamp = datetime($ts)
            """, mid=mid, role=role, content=content, ts=ts)
            if i == 0:
                session.run("""
                    MATCH (c:Conversation {id: 'conv_session_3'}), (m:Message {id: $mid})
                    MERGE (c)-[:FIRST_MESSAGE]->(m)
                """, mid=mid)
            else:
                prev_mid = s3_msgs[i - 1][0]
                session.run("""
                    MATCH (prev:Message {id: $prev}), (m:Message {id: $mid})
                    MERGE (prev)-[:NEXT_MESSAGE]->(m)
                """, prev=prev_mid, mid=mid)

        # Decision traces for session 3 -- reuses reasoning memory

        # DT7: Reuse un-accepted recommendations from session 2
        session.run("""
            MERGE (dt:DecisionTrace {id: 'dt_007'})
            SET dt.toolName = 'execute_cypher',
                dt.cypherQuery = 'MATCH (u:User {id: \"alex\"})-[:HAD_CONVERSATION]->(c:Conversation {id: \"conv_session_2\"})-[:PRODUCED]->(rec:Recommendation) WHERE rec.accepted = false MATCH (rec)-[:RECOMMENDS]->(s:Shoe) WHERE s.inStock = true RETURN s.brand, s.model, s.price, s.cushioning, rec.confidence, rec.reasoning',
                dt.reasoning = 'REASONING MEMORY REUSE: Instead of re-running the full 5-hop cross-user traversal (dt_003, 135ms), reusing the 2 un-accepted recommendations from session conv_session_2. This saves 3 tool calls, reduces latency by ~300ms, and cuts token usage by ~40%. Both candidates had max cushion which aligns with the new long-run requirement.',
                dt.memoryType = 'reasoning',
                dt.timestamp = datetime('2024-06-17T09:15:05'),
                dt.durationMs = 28,
                dt.result = 'Reused: Nimbus 25N (88% match, max cushion, snug heel) and 1080v13N (84% match, max cushion, average heel) from prior session'
            WITH dt
            MATCH (c:Conversation {id: 'conv_session_3'})
            MERGE (dt)-[:PART_OF]->(c)
            WITH dt
            MATCH (m:Message {id: 's3_m1'})
            MERGE (m)-[:TRIGGERED]->(dt)
        """)

        # DT8: Triumph 22 comparison check (triggered by user question)
        session.run("""
            MERGE (dt:DecisionTrace {id: 'dt_008'})
            SET dt.toolName = 'execute_cypher',
                dt.cypherQuery = 'MATCH (s:Shoe {id: \"saucony_triumph_22\"}) OPTIONAL MATCH (s)-[:HAS_REVIEW]->(r:Review)-[:CONTAINS_INSIGHT]->(i:ReviewInsight) RETURN s.price, s.widthOptions, s.cushioning, s.weight, collect({quote: i.quote, sentiment: i.sentiment}) AS insights',
                dt.reasoning = 'SHORT-TERM MEMORY: User asked about Triumph 22 (saw an ad). Checking width options, price, and review insights. Need to cross-reference with Alex long-term profile (narrow width, $100-150 budget) to evaluate fit.',
                dt.memoryType = 'short-term',
                dt.timestamp = datetime('2024-06-17T09:17:03'),
                dt.durationMs = 52,
                dt.result = 'Triumph 22: $159.95 (over budget), medium/wide only (no narrow), max cushion, 10.6oz. Durability concern from reviews. Not recommended for Alex: no narrow option available.'
            WITH dt
            MATCH (c:Conversation {id: 'conv_session_3'})
            MERGE (dt)-[:PART_OF]->(c)
            WITH dt
            MATCH (m:Message {id: 's3_m3'})
            MERGE (m)-[:TRIGGERED]->(dt)
        """)

        # DT9: Cross-reference Marcus purchase data for Nimbus endorsement
        session.run("""
            MERGE (dt:DecisionTrace {id: 'dt_009'})
            SET dt.toolName = 'execute_cypher',
                dt.cypherQuery = 'MATCH (u:User {id: \"marcus\"})-[p:PURCHASED]->(s:Shoe {id: \"asics_nimbus_25_n\"}) RETURN u.name, p.rating, p.notes',
                dt.reasoning = 'LONG-TERM MEMORY: Cross-referencing Marcus (marathon trainer) purchase data to add social proof for Nimbus 25N. Marcus has a different foot width (medium) but is a high-mileage runner which is relevant to the 15-mile cushion requirement.',
                dt.memoryType = 'long-term',
                dt.timestamp = datetime('2024-06-17T09:17:08'),
                dt.durationMs = 35,
                dt.result = 'Marcus: 5 stars, uses for 22-mile training days in Boston Marathon prep. Strong endorsement for long-run cushion.'
            WITH dt
            MATCH (c:Conversation {id: 'conv_session_3'})
            MERGE (dt)-[:PART_OF]->(c)
        """)

        print("Upserted 3 sessions, messages, 3 recommendations, 9 decision traces (short/long/reasoning memory)")

    driver.close()
    print("Seed complete.")


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()
    run_seed(
        os.environ["NEO4J_URI"],
        os.environ["NEO4J_USERNAME"],
        os.environ["NEO4J_PASSWORD"],
    )
