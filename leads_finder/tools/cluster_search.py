from typing import Any, Dict, List, Optional
import math
import requests
from pydantic import BaseModel, Field
from crewai.tools import BaseTool

USER_AGENT = "sales-agent/1.0 (contact: you@example.com)"

class Business(BaseModel):
    name: str = Field(..., description="Business name")
    address: Optional[str] = Field(None, description="Full address")
    phone: Optional[str] = Field(None, description="Contact phone")
    website: Optional[str] = Field(None, description="Business website")
    category: Optional[str] = Field(None, description="Business category/type")
    established: Optional[str] = Field(None, description="Year established if known")


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(
        math.radians(lat2)
    ) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def _geocode_city(city: str) -> Optional[Dict[str, float]]:
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": city, "format": "json", "limit": 1, "addressdetails": 0},
            headers={"User-Agent": USER_AGENT},
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        if not data:
            return None
        return {"lat": float(data[0]["lat"]), "lon": float(data[0]["lon"])}
    except Exception:
        return None


def _overpass_businesses(lat: float, lon: float, radius_m: int = 3000) -> List[Dict[str, Any]]:
    q = f"""
    [out:json][timeout:25];
    (
      node(around:{radius_m},{lat},{lon})["amenity"];
      node(around:{radius_m},{lat},{lon})["shop"];
    );
    out body;
    """
    try:
        r = requests.post(
            "https://overpass-api.de/api/interpreter",
            data=q,
            headers={"User-Agent": USER_AGENT, "Content-Type": "text/plain"},
            timeout=30,
        )
        r.raise_for_status()
        j = r.json()
        return j.get("elements", [])
    except Exception:
        return []


def _normalize_osm(el: Dict[str, Any], city_fallback: str) -> Dict[str, Any]:
    tags = el.get("tags", {}) or {}
    name = tags.get("name")
    parts = [
        tags.get("addr:housenumber"),
        tags.get("addr:street"),
        tags.get("addr:city") or city_fallback,
        tags.get("addr:state"),
        tags.get("addr:postcode"),
        tags.get("addr:country"),
    ]
    address = ", ".join([p for p in parts if p]) or None
    phone = tags.get("phone") or tags.get("contact:phone")
    website = tags.get("website") or tags.get("contact:website")
    category = tags.get("amenity") or tags.get("shop")
    established = tags.get("start_date")
    return {
        "name": name,
        "address": address,
        "phone": phone,
        "website": website,
        "category": category,
        "established": established,
        "_lat": el.get("lat"),
        "_lon": el.get("lon"),
    }


def _dedupe(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    out: List[Dict[str, Any]] = []
    for it in items:
        key = (str(it.get("name") or "").strip().lower(), str(it.get("address") or "").strip().lower())
        if key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out


def _cluster(items: List[Dict[str, Any]], threshold_m: int = 150) -> List[List[Dict[str, Any]]]:
    clusters: List[List[Dict[str, Any]]] = []
    for it in items:
        lat = it.get("_lat"); lon = it.get("_lon")
        if lat is None or lon is None:
            clusters.append([it])
            continue
        placed = False
        for c in clusters:
            rep = c[0]
            rlat = rep.get("_lat"); rlon = rep.get("_lon")
            if rlat is None or rlon is None:
                continue
            if _haversine_m(float(lat), float(lon), float(rlat), float(rlon)) <= threshold_m:
                c.append(it)
                placed = True
                break
        if not placed:
            clusters.append([it])
    return clusters


def _representative(cluster: List[Dict[str, Any]]) -> Dict[str, Any]:
    def score(it: Dict[str, Any]) -> int:
        return sum(1 for k in ("address", "phone", "website", "category", "established") if it.get(k))
    rep = max(cluster, key=score)
    rep_clean = {k: v for k, v in rep.items() if not k.startswith("_")}
    return Business(**rep_clean).model_dump()


class ClusterSearchTool(BaseTool):
    """Tool to perform a custom cluster-based business search by city.

    Input: city name string.
    Output: JSON-serializable list of Business dicts.
    """

    name: str = "cluster_search"
    description: str = "Find businesses in a given city using OSM (Overpass) + clustering; returns structured results."

    def _run(self, query: str) -> str:  
        print("cluster search tool called!!")
        city = (query or "").strip()
        if not city:
            return "[]"

        geo = _geocode_city(city)
        if not geo:
            return "[]"

        elements = _overpass_businesses(geo["lat"], geo["lon"], radius_m=3000)
        normalized = [_normalize_osm(el, city) for el in elements if el.get("tags", {}).get("name")]
        deduped = _dedupe(normalized)
        clusters = _cluster(deduped, threshold_m=150)

        # Convert to MongoDB-compatible format
        mongodb_results = []
        for business in [_representative(c) for c in clusters]:
            mongodb_business = {
                "name": business.get('name', ''),
                "address": business.get('address', ''),
                "phone": business.get('phone'),
                "website": business.get('website'),
                "category": business.get('category'),
                "rating": None,  # OSM doesn't provide ratings
                "source": "cluster_search"
            }
            mongodb_results.append(mongodb_business)
        
        # Return JSON string for MongoDB upload tool
        import json
        return json.dumps(mongodb_results)