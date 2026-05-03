import sqlite3
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from insight_engine.engine import DB_PATH, init_db, run as run_insight_engine


CLIENT_ID = "demo-abq"


SEEDS = [
    {
        "label": "trip planning — couple, late October",
        "messages": [
            ("user", "Hi! My partner and I are flying into Albuquerque the last week of October. First-time visitors. What should we plan?"),
            ("assistant", "Welcome! Late October in Albuquerque is gorgeous — cool mornings, sunny afternoons. Are you more interested in Old Town and dining, or scenic drives and hiking?"),
            ("user", "Both honestly. We love good food and a sunset hike sounds amazing."),
            ("assistant", "For dining, El Pinto and Sadie's of New Mexico are go-tos for authentic New Mexican. For sunset, the Sandia Peak Tramway is unmatched, and the La Luz Trail is a serious hike if you want to earn the view."),
            ("user", "Perfect. Any chance the Marigold Parade is happening while we're there?"),
            ("assistant", "I don't have confirmed dates for this year's Marigold Parade — I'd recommend checking the South Valley Muertos y Marigolds Facebook page for current info."),
        ],
    },
    {
        "label": "trip planning — family with kids",
        "messages": [
            ("user", "Planning a spring break trip with two kids (ages 7 and 10). What's good for families in Albuquerque?"),
            ("assistant", "Great age range! The ABQ BioPark is a must — zoo, aquarium, and botanical garden in one. Explora Science Center is also fantastic for hands-on learning."),
            ("user", "Are there any family-friendly hotels with a pool near the BioPark?"),
            ("assistant", "Hotel Albuquerque at Old Town is close to the BioPark and has a pool. The Hotel Chaco is more upscale but has great amenities too."),
            ("user", "Any kid-friendly restaurants you'd recommend for green chile that isn't too spicy?"),
            ("assistant", "Frontier Restaurant near UNM is iconic and has mild options. Garcia's Kitchen is also family-friendly with kid-sized portions."),
        ],
    },
    {
        "label": "on-site visitor asking about events today",
        "messages": [
            ("user", "I'm in Old Town right now. Anything fun happening in town tonight?"),
            ("assistant", "Old Town often has live music in the plaza on weekends. Are you looking for music, food events, or something else?"),
            ("user", "Live music sounds great. Any specific venues open tonight?"),
            ("assistant", "I don't have a real-time event feed, so I can't confirm tonight's lineup. The Launchpad and Sister Bar usually have shows — I'd check their websites or Instagram for tonight's schedule."),
            ("user", "Got it. What about a late dinner spot still open after 9pm?"),
            ("assistant", "Sadie's of New Mexico typically serves until 10pm. Frontier Restaurant on Central is open late and very popular."),
        ],
    },
    {
        "label": "group travel — bachelorette",
        "messages": [
            ("user", "Hi! I'm organizing a bachelorette weekend in Albuquerque for 8 women in June. Looking for ideas."),
            ("assistant", "Fun! Albuquerque has great options for groups. Are you thinking spa-and-wine vibes, outdoor adventure, or party-focused?"),
            ("user", "A mix. Definitely a wine tour, maybe a hot air balloon ride, and good nightlife."),
            ("assistant", "Rainbow Ryders does private balloon flights for groups. For wines, check out Casa Rondeña Winery in Los Ranchos. For nightlife, Marble Brewery and the Launchpad area are solid."),
            ("user", "Do you have group rates for the balloon ride or should I contact them directly?"),
            ("assistant", "I don't have specific group pricing — you'll need to reach out to Rainbow Ryders directly for a quote."),
            ("user", "Any recommendations for a group-friendly hotel?"),
            ("assistant", "Hotel Chaco and Hotel Andaluz both work well for larger groups and are walkable to nightlife and dining."),
        ],
    },
    {
        "label": "general browsing",
        "messages": [
            ("user", "What's Albuquerque known for?"),
            ("assistant", "Albuquerque is famous for the International Balloon Fiesta, authentic New Mexican cuisine (especially green chile), Old Town's adobe architecture, and stunning desert and mountain landscapes."),
            ("user", "Cool. Is it walkable?"),
            ("assistant", "Old Town and Nob Hill are walkable. Most of the city is car-friendly though — you'll want a vehicle to explore widely."),
            ("user", "Got it, just curious. Thanks!"),
            ("assistant", "You're welcome! Reach out anytime you want to dig deeper."),
        ],
    },
    {
        "label": "event research — Balloon Fiesta",
        "messages": [
            ("user", "I want to come for the Balloon Fiesta this year. What do I need to know?"),
            ("assistant", "The Albuquerque International Balloon Fiesta is the largest hot air balloon event in the world, held every year over the first nine days of October at Balloon Fiesta Park."),
            ("user", "What's the difference between Mass Ascension and the Glowdeo?"),
            ("assistant", "Mass Ascension is the morning event where 500+ balloons launch together at sunrise. The Balloon Glow (sometimes called Glowdeo) is an evening event where tethered balloons light up at dusk to music — visually spectacular."),
            ("user", "Are tickets sold out for opening weekend this year?"),
            ("assistant", "I don't have current ticket availability — the official Balloon Fiesta website would have the most up-to-date inventory and pricing."),
            ("user", "What hotels book up the fastest?"),
            ("assistant", "Hotels near I-25 and the north valley book first because they're closest to Balloon Fiesta Park. Marriott Pyramid North and Hotel Chaco are popular picks."),
        ],
    },
    {
        "label": "dining-focused",
        "messages": [
            ("user", "I'm a foodie and want the best New Mexican meals of my life. Hit me."),
            ("assistant", "You came to the right place. For elevated New Mexican: Antiquity in Old Town. For classic comfort: El Pinto. For breakfast burritos done right: Frontier Restaurant or Tia B's La Waffleria."),
            ("user", "What's the difference between red and green chile? Which is hotter?"),
            ("assistant", "Red chile is from ripened, dried pods — earthier and often slightly milder. Green chile is from unripe pods — fresher, brighter, often hotter. Order 'Christmas' to get both!"),
            ("user", "Any standout Mexican (not New Mexican) places too?"),
            ("assistant", "Mary & Tito's is legendary for carne adovada. Los Cuates is great for traditional Mexican. M'Tucci's leans Italian-American but worth a mention."),
            ("user", "Is there a chile festival I could plan around?"),
            ("assistant", "I'm not certain about Albuquerque-specific dates — Hatch (south of ABQ) hosts the famous Hatch Chile Festival around Labor Day weekend. Worth checking their official site for confirmed dates."),
        ],
    },
    {
        "label": "outdoor activities",
        "messages": [
            ("user", "I want to spend a long weekend outdoors near Albuquerque. Hiking, biking, climbing — open to anything."),
            ("assistant", "You'll have a great time. The Sandia Mountains have La Luz Trail, the Pino Trail, and easier options like Embudito Canyon. For biking, the Paseo del Bosque is a flat 16-mile riverside trail."),
            ("user", "What about climbing? Real rock, not gym."),
            ("assistant", "Sandia Mountains have classic granite climbing — The Shield and Muralla Grande are well-known. Diablo Canyon farther north is also popular for sport climbing."),
            ("user", "Any guided options if I don't have a partner?"),
            ("assistant", "I don't have a vetted list of climbing guides for the area — I'd recommend checking with the local climbing shop Stone Age Climbing Gym for guide referrals."),
            ("user", "Would late April be a good time weather-wise?"),
            ("assistant", "Late April is excellent — mild temps, low precipitation. Mornings can still be cool in the mountains, so layer up."),
        ],
    },
]


def utc_iso(offset_seconds: int = 0) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=offset_seconds)).isoformat()


def insert_session_with_messages(db_path: Path, session_id: str, messages: list[tuple[str, str]]) -> None:
    started = utc_iso(-len(messages) * 60)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO sessions (session_id, client_id, started_at, status) VALUES (?, ?, ?, ?)",
            (session_id, CLIENT_ID, started, "closed"),
        )
        rows = []
        for i, (role, content) in enumerate(messages):
            rows.append((session_id, role, content, utc_iso(-len(messages) * 60 + i * 30)))
        conn.executemany(
            "INSERT INTO messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            rows,
        )
        conn.commit()
    finally:
        conn.close()


def main() -> None:
    load_dotenv()
    init_db()

    total = len(SEEDS)
    for i, seed in enumerate(SEEDS, start=1):
        session_id = str(uuid.uuid4())
        insert_session_with_messages(DB_PATH, session_id, seed["messages"])
        run_insight_engine(session_id)
        print(f"[seed] session {i}/{total} → {session_id} ({seed['label']})")


if __name__ == "__main__":
    main()
