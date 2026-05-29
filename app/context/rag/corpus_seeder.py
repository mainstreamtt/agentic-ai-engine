"""Corpus seeder – uploads sample travel documents into the RAG corpus.

Run once to populate the knowledge base:

    python -m app.context.rag.corpus_seeder

Each document is written to a temp file and uploaded via rag.upload_file,
so no GCS bucket is required.
"""

from __future__ import annotations

import tempfile
import os

import structlog
import vertexai as _vertexai
from vertexai.preview import rag

from app import config

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Sample travel knowledge-base documents
# ---------------------------------------------------------------------------

_DOCUMENTS: list[tuple[str, str]] = [
    (
        "europe_destinations_guide.txt",
        """\
# Europe Destinations Guide

## Paris, France
Paris is one of the world's most visited cities. The Eiffel Tower, Louvre Museum,
Notre-Dame Cathedral, and Champs-Élysées are must-visit landmarks.
Best neighbourhoods: Le Marais (art & history), Saint-Germain-des-Prés (café culture),
Montmartre (bohemian, great views).
Best time to visit: April–June and September–October (mild weather, fewer crowds).
Average daily budget: €80–150 mid-range. Metro pass ~€16/day.
Visa: Schengen visa required for non-EU visitors.

## Rome, Italy
The Colosseum, Vatican City, Trevi Fountain, and Roman Forum draw millions annually.
Best neighbourhoods: Trastevere (local vibe), Prati (near Vatican), Monti (hipster).
Best time to visit: April–May or September–October.
Average daily budget: €70–130 mid-range.
Tip: Book Vatican Museums tickets at least 2 weeks in advance.

## Barcelona, Spain
Sagrada Família, Park Güell, La Barceloneta beach, and Las Ramblas define the city.
Best neighbourhoods: Gothic Quarter (historic), Eixample (modernist architecture),
Barceloneta (beach).
Best time to visit: May–June or September–October.
Average daily budget: €70–120 mid-range. T-10 metro card saves money.

## Amsterdam, Netherlands
Canal houses, Rijksmuseum, Anne Frank House, and vibrant cycling culture.
Best neighbourhoods: Jordaan (charming canals), De Pijp (multicultural), Museum Quarter.
Best time to visit: April–May (tulip season) or September.
Average daily budget: €90–160 mid-range.

## Prague, Czech Republic
Prague Castle, Charles Bridge, Old Town Square, and affordable prices make it popular.
Best time to visit: May–June or September.
Average daily budget: €40–80 mid-range (very affordable).
""",
    ),
    (
        "asia_destinations_guide.txt",
        """\
# Asia Destinations Guide

## Tokyo, Japan
Tokyo blends ultra-modern technology with ancient temples. Shibuya Crossing, Senso-ji
Temple, teamLab, and Tsukiji Outer Market are highlights.
Best neighbourhoods: Shinjuku (entertainment), Shibuya (shopping), Asakusa (traditional).
Best time to visit: March–May (cherry blossom) or October–November (autumn foliage).
Average daily budget: ¥8,000–15,000 (~€50–95) mid-range.
Visa: Many nationalities get 90-day visa-free entry.
Transport: IC card (Suica/Pasmo) essential for seamless travel.

## Bali, Indonesia
Bali offers rice terraces, Hindu temples, surf beaches, and world-class wellness retreats.
Top areas: Ubud (culture & wellness), Seminyak (nightlife & beach), Canggu (surf & cafés),
Nusa Dua (luxury resorts).
Best time to visit: April–October (dry season).
Average daily budget: $30–80 USD mid-range. Budget travellers can manage on $25/day.
Visa: 30-day visa on arrival for most nationalities (~$35 USD).

## Bangkok, Thailand
Grand Palace, Wat Pho, floating markets, and legendary street food make Bangkok unmissable.
Best neighbourhoods: Sukhumvit (international), Silom (business & nightlife), Banglamphu/Khao San (backpacker).
Best time to visit: November–February (cool and dry).
Average daily budget: ฿1,500–3,000 (~€40–80) mid-range.
Tip: Tuk-tuks and BTS Skytrain are the fastest ways around.

## Singapore
A city-state with Marina Bay Sands, Gardens by the Bay, hawker centres, and excellent transit.
Best time to visit: February–April (least rainfall).
Average daily budget: SGD 100–200 (~€70–140) mid-range.
Visa: Visa-free for most Western passport holders (30–90 days).
Tip: Hawker centres offer world-class food from $3–8 SGD per dish.

## Kyoto, Japan
Kyoto is Japan's cultural heart: Fushimi Inari Shrine, Arashiyama bamboo grove,
Kinkaku-ji (Golden Pavilion), and traditional geisha districts.
Best time to visit: March–May or October–November.
Average daily budget: ¥7,000–12,000 mid-range.
Day trip from Osaka (35 min by Shinkansen) or Tokyo (2.5 hrs).
""",
    ),
    (
        "budget_travel_guide.txt",
        """\
# Budget Travel Guide

## Accommodation
- Hostels: $10–30/night in most destinations; private rooms available for $25–60.
- Guesthouses and B&Bs: More local experience at $20–50/night.
- Apartment rentals (Airbnb/Vrbo): Cost-effective for groups of 3+ staying 4+ nights.
- Couchsurfing: Free, but requires planning ahead.

## Flights
- Book 6–8 weeks ahead for domestic, 3–6 months for international.
- Be flexible with dates: flying Tuesday–Thursday saves 15–25%.
- Use budget airlines (Ryanair, easyJet, AirAsia, Scoot) for short hauls.
- Set fare alerts on Google Flights or Skyscanner.
- Consider positioning flights: fly to a cheap hub, then connect on budget carriers.

## Food
- Eat where locals eat: markets, food courts, hawker stalls.
- Supermarkets and self-catering cut food costs by 40–60%.
- Lunch menus (set meals) offer restaurant-quality food at half dinner prices.
- Avoid tourist-trap restaurants near major attractions.

## Transport
- City transport passes (metro/bus) are almost always cheaper than taxis.
- Walk distances under 2 km – it's free and you see more.
- Night buses or overnight trains save on accommodation and time.
- Intercity buses beat trains on price in Southeast Asia and Eastern Europe.

## Activities
- Many world-class museums have free admission on certain days/times.
- Free walking tours (tip-based) are available in most major European and Asian cities.
- National parks and nature hikes cost far less than city attractions.
- City tourist cards often bundle museums + transit at 20–40% savings.

## Average daily budgets by tier (excluding flights)
| Tier       | Western Europe | Southeast Asia | Japan     |
|------------|---------------|----------------|-----------|
| Budget     | €50–70        | $25–40         | €50–70    |
| Mid-range  | €100–150      | $50–80         | €80–120   |
| Luxury     | €200+         | $100–150+      | €150–250+ |
""",
    ),
    (
        "travel_tips_and_logistics.txt",
        """\
# Travel Tips and Logistics

## Before You Go
- Check visa requirements at least 6 weeks before departure.
  - Schengen Area: covers 27 European countries on one visa (90 days in 180).
  - E-visas available for USA (ESTA), Australia (ETA), Japan, and many others.
- Get travel insurance: covers medical, cancellation, and baggage (€30–80 for 2 weeks).
- Notify your bank of travel dates to prevent card blocks.
- Download offline maps (Google Maps, Maps.me) and translation apps.
- Carry a small first-aid kit and any prescription medication with documentation.

## Money
- Withdraw local currency from ATMs on arrival; avoid airport exchange desks.
- Use zero-fee travel cards (Revolut, Wise, Charles Schwab) to avoid FX fees.
- Keep a small emergency cash reserve ($50–100 USD widely accepted globally).
- In Southeast Asia and markets, cash is still king; haggling is expected.

## Health & Safety
- Check travel advisories (gov.uk/foreign-travel-advice or travel.state.gov).
- Vaccinations: check requirements 4–6 weeks before departure (Yellow Fever,
  Typhoid, Hepatitis A common for developing regions).
- Drink bottled water in regions with unreliable tap water (most of SE Asia,
  parts of South America, Africa).
- Register with your embassy when visiting higher-risk regions.

## Connectivity
- Buy a local SIM on arrival for the best data rates.
- International eSIMs (Airalo, Holafly) offer easy setup before you go.
- Most hostels, cafés, and hotels have free Wi-Fi.

## Cultural Etiquette
- Japan: remove shoes when entering homes/traditional restaurants; quiet on trains.
- Middle East: dress modestly, especially near religious sites.
- Southeast Asia: cover shoulders and knees at temples; never point feet at shrines.
- Europe: restaurant tipping 5–15%; not expected in Japan.
- Photography: always ask permission for portraits; many temples ban cameras.

## Packing Tips
- Pack light: a 40L carry-on backpack avoids checked-bag fees.
- Versatile layers beat climate-specific clothing.
- Merino wool is odour-resistant, quick-drying, and works in hot and cold climates.
- Universal travel adapter + power bank are essential.
""",
    ),
    (
        "top_global_destinations_overview.txt",
        """\
# Top Global Destinations Overview

## Most Visited Cities Worldwide (annual visitors)
1. Bangkok, Thailand – 22M visitors. Street food, temples, nightlife.
2. Paris, France – 19M visitors. Art, history, cuisine, romance.
3. London, UK – 19M visitors. Museums (mostly free), history, multicultural food.
4. Dubai, UAE – 16M visitors. Luxury, desert safaris, architecture.
5. Singapore – 15M visitors. Food, gardens, efficiency, cleanliness.
6. Kuala Lumpur, Malaysia – 13M visitors. Petronas Towers, affordable luxury.
7. Tokyo, Japan – 13M visitors. Culture, technology, food, safety.
8. Istanbul, Turkey – 13M visitors. East meets West; Grand Bazaar, Hagia Sophia.
9. Seoul, South Korea – 12M visitors. K-culture, palaces, DMZ tours.
10. New York, USA – 12M visitors. Iconic skyline, Broadway, Central Park.

## Emerging Destinations (2024–2025 trending)
- Tbilisi, Georgia: ancient architecture, wine culture, low cost (~€40/day).
- Medellín, Colombia: spring climate year-round, tech hub, transformed city.
- Chiang Mai, Thailand: digital nomad hub, temples, night markets (~€30/day).
- Tallinn, Estonia: medieval old town, digital e-residency, affordable EU city.
- Cape Town, South Africa: Table Mountain, wine routes, world-class beaches.

## Best Long-Haul Value Destinations
- Vietnam: 2-week trip including flights from Europe possible for €800–1,200.
- Mexico: Cancún–Mexico City–Oaxaca circuit; rich culture and food.
- Peru: Machu Picchu, Amazon, Cusco; 2 weeks ~€1,000–1,500 from Europe.
- Morocco: Marrakech, Sahara, coastal towns; 10 days ~€600–900 from Europe.

## Family-Friendly Picks
- Japan (ultra-safe, efficient transit, kid-friendly food)
- Portugal (affordable, safe, beach + culture)
- Costa Rica (nature, wildlife, stable)
- New Zealand (stunning scenery, English-speaking, safe)

## Adventure Travel Hotspots
- Iceland: Northern lights, glaciers, geothermal pools.
- Nepal: Everest Base Camp trek, Annapurna Circuit.
- Patagonia (Chile/Argentina): Torres del Paine, Perito Moreno glacier.
- New Zealand: Milford Sound, bungee jumping, Tongariro Crossing.
""",
    ),
]


# ---------------------------------------------------------------------------
# Corpus bootstrap + seeder
# ---------------------------------------------------------------------------

_DISPLAY_NAME = "agentic-ai-engineering-rag"


def get_or_create_corpus() -> str | None:
    """Return the RAG corpus resource name, creating it if it does not exist."""
    _vertexai.init(project=config.GOOGLE_CLOUD_PROJECT, location=config.GOOGLE_CLOUD_LOCATION)
    try:
        for corpus in rag.list_corpora():
            if corpus.display_name == _DISPLAY_NAME:
                logger.info("Found existing RAG corpus", corpus_name=corpus.name)
                return corpus.name

        # Switch engine to Serverless mode before creating.
        # The default (Spanner) is restricted on new projects in some regions.
        engine_config_name = (
            f"projects/{config.GOOGLE_CLOUD_PROJECT}"
            f"/locations/{config.GOOGLE_CLOUD_LOCATION}"
            f"/ragEngineConfig"
        )
        rag.update_rag_engine_config(
            rag_engine_config=rag.RagEngineConfig(
                name=engine_config_name,
                rag_managed_db_config=rag.RagManagedDbConfig(mode=rag.Serverless()),
            )
        )
        logger.info("RAG engine switched to Serverless mode")

        logger.info("No RAG corpus found – creating one", display_name=_DISPLAY_NAME)
        corpus = rag.create_corpus(display_name=_DISPLAY_NAME)
        logger.info("RAG corpus created", corpus_name=corpus.name)
        return corpus.name
    except Exception:
        logger.error("Failed to get or create RAG corpus", exc_info=True)
        return None


def seed_corpus() -> None:
    """Ensure the RAG corpus exists, then upload all sample documents."""
    corpus = get_or_create_corpus()
    if not corpus:
        logger.error("RAG corpus unavailable – cannot seed")
        return

    _vertexai.init(project=config.GOOGLE_CLOUD_PROJECT, location=config.GOOGLE_CLOUD_LOCATION)

    transformation_config = rag.TransformationConfig(
        chunking_config=rag.ChunkingConfig(
            chunk_size=512,
            chunk_overlap=100,
        )
    )

    for display_name, content in _DOCUMENTS:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".txt",
            prefix=display_name.replace(".txt", "_"),
            delete=False,
            encoding="utf-8",
        ) as f:
            f.write(content)
            tmp_path = f.name

        try:
            rag_file = rag.upload_file(
                corpus_name=corpus,
                path=tmp_path,
                display_name=display_name,
                description=f"Sample travel knowledge-base document: {display_name}",
                transformation_config=transformation_config,
            )
            logger.info("Uploaded RAG document", name=rag_file.name, display_name=display_name)
        except Exception:
            logger.error("Failed to upload document", display_name=display_name, exc_info=True)
        finally:
            os.unlink(tmp_path)

    logger.info("Corpus seeding complete", total=len(_DOCUMENTS))


if __name__ == "__main__":
    from app.config import configure_logging
    configure_logging()
    seed_corpus()
