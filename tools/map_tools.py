# tools/map_tools.py
import unicodedata
import requests

try:
    from crewai.tools import tool       # CrewAI 1.x
except ImportError:
    from crewai_tools import tool       # older versions

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
_HEADERS = {"User-Agent": "StartupLaunchCopilot/1.0"}

_OSM_TAGS = {
    "cafe": '["amenity"="cafe"]',
    "coffee": '["amenity"="cafe"]',
    "restaurant": '["amenity"="restaurant"]',
    "food": '["amenity"="restaurant"]',
    "bakery": '["shop"="bakery"]',
    "grocery": '["shop"="supermarket"]',
    "supermarket": '["shop"="supermarket"]',
    "clothing": '["shop"="clothes"]',
    "clothes": '["shop"="clothes"]',
    "fashion": '["shop"="clothes"]',
    "pharmacy": '["amenity"="pharmacy"]',
    "gym": '["leisure"="fitness_centre"]',
    "fitness": '["leisure"="fitness_centre"]',
    "salon": '["shop"="hairdresser"]',
    "barber": '["shop"="hairdresser"]',
    "bookstore": '["shop"="books"]',
    "books": '["shop"="books"]',
    "electronics": '["shop"="electronics"]',
}

# substring keywords → tag key (handles "café", "coffee shop", "clothing store"...)
_KEYWORDS = [
    ("caf", "cafe"), ("coffee", "cafe"),
    ("restaurant", "restaurant"), ("food", "food"),
    ("baker", "bakery"),
    ("supermarket", "supermarket"), ("grocer", "grocery"),
    ("cloth", "clothing"), ("fashion", "fashion"),
    ("pharma", "pharmacy"), ("drug", "pharmacy"),
    ("gym", "gym"), ("fitness", "fitness"),
    ("salon", "salon"), ("barber", "barber"), ("hair", "salon"),
    ("book", "bookstore"),
    ("electronic", "electronics"), ("phone", "electronics"),
]

_cache = {}


def _normalize(text: str) -> str:
    """Lowercase + strip accents so 'Café' matches 'cafe'."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return text.lower().strip()


def _osm_tag_for(business_type: str) -> str:
    t = _normalize(business_type)
    if t in _OSM_TAGS:
        return _OSM_TAGS[t]
    for kw, key in _KEYWORDS:
        if kw in t:
            return _OSM_TAGS[key]
    return '["shop"]'


def _geocode_city(city: str):
    resp = requests.get(
        NOMINATIM_URL,
        params={"q": city, "format": "json", "limit": 1},
        headers=_HEADERS,
        timeout=15,
    )
    data = resp.json()
    if not data:
        return None
    return float(data[0]["lat"]), float(data[0]["lon"])


def _find_competitors(business_type: str, city: str, radius: int = 5000, limit: int = 40):
    key = (business_type.lower(), city.lower())
    if key in _cache:
        return _cache[key]

    try:
        coords = _geocode_city(city)
    except Exception:
        coords = None
    if not coords:
        return None, [], None

    tag = _osm_tag_for(business_type)
    # nwr = nodes + ways + relations (many POIs are mapped as areas, not nodes)
    query = f"""
    [out:json][timeout:25];
    nwr{tag}(around:{radius},{coords[0]},{coords[1]});
    out center {limit};
    """
    try:
        resp = requests.post(OVERPASS_URL, data={"data": query}, headers=_HEADERS, timeout=45)
        elements = resp.json().get("elements", [])
    except Exception:
        elements = []

    competitors = []
    for el in elements:
        name = el.get("tags", {}).get("name")
        if not name:
            continue
        lat = el.get("lat") or el.get("center", {}).get("lat")
        lon = el.get("lon") or el.get("center", {}).get("lon")
        if lat is None or lon is None:
            continue
        competitors.append({"name": name, "lat": lat, "lon": lon})

    _cache[key] = (coords, competitors, coords)
    return coords, competitors, coords


@tool("Competitor Map Search")
def competitor_map_search(business_type: str, city: str) -> str:
    """Find similar existing businesses (competitors) in a city using OpenStreetMap.
    Returns the number of competitors, their names, and coordinates."""
    coords, competitors, _ = _find_competitors(business_type, city)
    if coords is None:
        return f"Could not geocode the city '{city}'. Use your own knowledge instead."
    if not competitors:
        return (
            f"No similar businesses found for '{business_type}' within 5 km of {city}. "
            f"This may indicate a market gap OR low OpenStreetMap coverage."
        )

    lines = [f"Found {len(competitors)} similar businesses within 5 km of {city}:"]
    for c in competitors[:25]:
        lines.append(f"- {c['name']} (lat {c['lat']:.5f}, lon {c['lon']:.5f})")
    density = "HIGH" if len(competitors) > 15 else "MEDIUM" if len(competitors) > 5 else "LOW"
    lines.append(f"\nCompetitor density: {density}")
    return "\n".join(lines)


def build_demo_map(business_type: str, city: str):
    """Helper (NOT a CrewAI tool): builds a folium map for the Streamlit UI."""
    import folium

    coords, competitors, _ = _find_competitors(business_type, city)
    if coords is None:
        return None

    m = folium.Map(location=coords, zoom_start=13)
    for c in competitors:
        folium.CircleMarker(
            location=[c["lat"], c["lon"]],
            radius=6,
            popup=c["name"],
            color="red",
            fill=True,
            fill_opacity=0.6,
        ).add_to(m)
    return m