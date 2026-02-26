"""
kandilli-mcp: MCP Server for Kandilli Observatory Earthquake Data
Boğaziçi Üniversitesi Kandilli Rasathanesi verilerini MCP üzerinden sunar.
"""

import re
from typing import Optional
import httpx
from bs4 import BeautifulSoup
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("kandilli-mcp")

KANDILLI_URL = "http://www.koeri.boun.edu.tr/scripts/lst0.asp"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; kandilli-mcp/1.0)"}

_NULL_MAG = {"-.-", "-", "", "---", "0.0", "0"}


def parse_mag(val: str) -> Optional[float]:
    val = val.strip()
    if val in _NULL_MAG:
        return None
    try:
        f = float(val)
        return None if f == 0.0 else f
    except ValueError:
        return None


def normalize(s: str) -> str:
    return (
        s.lower()
        .replace("İ", "i").replace("I", "i")
        .replace("ı", "i").replace("i̇", "i")
        .replace("Ğ", "g").replace("ğ", "g")
        .replace("Ü", "u").replace("ü", "u")
        .replace("Ş", "s").replace("ş", "s")
        .replace("Ö", "o").replace("ö", "o")
        .replace("Ç", "c").replace("ç", "c")
    )


def parse_kandilli_data(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    pre = soup.find("pre")
    if not pre:
        return []

    earthquakes = []
    for line in pre.get_text().splitlines():
        line = line.strip()
        if not re.match(r"^\d{4}\.\d{2}\.\d{2}", line):
            continue
        parts = line.split()
        if len(parts) < 9:
            continue
        try:
            date_str = parts[0]
            time_str = parts[1]
            lat      = float(parts[2])
            lon      = float(parts[3])
            depth    = float(parts[4])
            md, ms, mb, mw = (parse_mag(parts[i]) for i in (5, 6, 7, 8))

            magnitudes = [m for m in [mw, ms, mb, md] if m is not None]
            magnitude  = max(magnitudes) if magnitudes else None

            lp = parts[9:] if len(parts) > 9 else []
            lp = [p for p in lp if p.upper() not in {"REVIZE", "PRELIMINARY", "İLKSEL", "ILKSEL"}]

            if len(lp) >= 2:
                city, location = lp[-1], " ".join(lp[:-1])
            elif len(lp) == 1:
                city = location = lp[0]
            else:
                city = location = ""

            if depth < 10:
                depth_category = "sığ"
            elif depth < 70:
                depth_category = "orta"
            else:
                depth_category = "derin"

            earthquakes.append({
                "datetime":        f"{date_str.replace('.', '-')}T{time_str}",
                "date":            date_str.replace(".", "-"),
                "time":            time_str,
                "latitude":        lat,
                "longitude":       lon,
                "depth_km":        depth,
                "depth_category":  depth_category,
                "magnitude":       magnitude,
                "magnitude_md":    md,
                "magnitude_ms":    ms,
                "magnitude_mb":    mb,
                "magnitude_mw":    mw,
                "location":        location,
                "city":            city,
            })
        except (ValueError, IndexError):
            continue
    return earthquakes


async def fetch_earthquakes() -> list[dict]:
    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            response = await client.get(KANDILLI_URL, headers=HEADERS)
            response.raise_for_status()
    except httpx.TimeoutException:
        raise RuntimeError(
            "Kandilli sunucusuna bağlanırken zaman aşımı oluştu. "
            "Lütfen birkaç dakika sonra tekrar deneyin."
        )
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(f"Kandilli sunucusu HTTP hata döndürdü: {exc.response.status_code}")
    except httpx.RequestError as exc:
        raise RuntimeError(f"Kandilli sunucusuna bağlanılamadı: {exc}")

    try:
        html = response.content.decode("windows-1254")
    except (UnicodeDecodeError, LookupError):
        html = response.text

    result = parse_kandilli_data(html)
    if not result:
        raise RuntimeError(
            "Kandilli sayfası alındı fakat veri parse edilemedi. "
            "Sayfa formatı değişmiş olabilir."
        )
    return result


# ─── MCP Tools ───────────────────────────────────────────────────────────────

@mcp.tool()
async def get_recent_earthquakes(limit: int = 20) -> dict:
    """
    Kandilli Rasathanesi'nden son depremleri getirir.

    Args:
        limit: Kaç deprem getirileceği (varsayılan: 20, max: 500)
    """
    limit = min(max(1, limit), 500)
    try:
        earthquakes = await fetch_earthquakes()
    except RuntimeError as e:
        return {"error": str(e), "earthquakes": []}

    return {
        "count":       min(len(earthquakes), limit),
        "source":      "Kandilli Rasathanesi (KOERI)",
        "earthquakes": earthquakes[:limit],
    }


@mcp.tool()
async def get_latest_earthquake() -> dict:
    """
    En son kaydedilen tek depremi getirir.
    Hızlı kontrol ve anlık durum için kullanılır.
    """
    try:
        earthquakes = await fetch_earthquakes()
    except RuntimeError as e:
        return {"error": str(e)}

    if not earthquakes:
        return {"error": "Deprem verisi bulunamadı."}

    return {
        "source":     "Kandilli Rasathanesi (KOERI)",
        "earthquake": earthquakes[0],
    }


@mcp.tool()
async def get_earthquakes_by_magnitude(
    min_magnitude: float = 3.0,
    max_magnitude: Optional[float] = None,
    limit: int = 50,
) -> dict:
    """
    Belirli büyüklük aralığındaki depremleri listeler.

    Args:
        min_magnitude: Minimum deprem büyüklüğü (varsayılan: 3.0)
        max_magnitude: Maksimum deprem büyüklüğü (opsiyonel, varsayılan: sınırsız)
        limit: Maksimum sonuç sayısı (varsayılan: 50)
    """
    try:
        earthquakes = await fetch_earthquakes()
    except RuntimeError as e:
        return {"error": str(e), "earthquakes": []}

    filtered = [
        eq for eq in earthquakes
        if eq["magnitude"] is not None
        and eq["magnitude"] >= min_magnitude
        and (max_magnitude is None or eq["magnitude"] <= max_magnitude)
    ][:limit]

    return {
        "count":          len(filtered),
        "min_magnitude":  min_magnitude,
        "max_magnitude":  max_magnitude,
        "source":         "Kandilli Rasathanesi (KOERI)",
        "earthquakes":    filtered,
    }


@mcp.tool()
async def get_earthquakes_by_location(
    keyword: str,
    limit: int = 30,
) -> dict:
    """
    Konum adına göre deprem filtreler. İl veya bölge adı ile arama yapılabilir.
    Örnek: "İzmir", "Marmara", "Kahramanmaraş", "Ege", "ADANA"

    Args:
        keyword: Aranacak konum (il, bölge, deniz adı) — büyük/küçük harf duyarsız
        limit: Maksimum sonuç sayısı (varsayılan: 30)
    """
    try:
        earthquakes = await fetch_earthquakes()
    except RuntimeError as e:
        return {"error": str(e), "earthquakes": []}

    kw_norm = normalize(keyword)
    filtered = [
        eq for eq in earthquakes
        if kw_norm in normalize(eq["location"]) or kw_norm in normalize(eq["city"])
    ][:limit]

    return {
        "count":       len(filtered),
        "keyword":     keyword,
        "source":      "Kandilli Rasathanesi (KOERI)",
        "earthquakes": filtered,
    }


@mcp.tool()
async def get_earthquakes_by_date(
    date: str,
    limit: int = 100,
) -> dict:
    """
    Belirli bir tarihe ait depremleri listeler.
    Tarih formatı: YYYY-MM-DD (örn: "2024-09-15")

    Args:
        date: Filtrelenecek tarih (YYYY-MM-DD formatında)
        limit: Maksimum sonuç sayısı (varsayılan: 100)
    """
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
        return {
            "error": f"Geçersiz tarih formatı: '{date}'. YYYY-MM-DD formatı kullanın (örn: '2024-09-15').",
            "earthquakes": [],
        }

    try:
        earthquakes = await fetch_earthquakes()
    except RuntimeError as e:
        return {"error": str(e), "earthquakes": []}

    filtered = [eq for eq in earthquakes if eq["date"] == date][:limit]

    return {
        "count":       len(filtered),
        "date":        date,
        "source":      "Kandilli Rasathanesi (KOERI)",
        "earthquakes": filtered,
    }


@mcp.tool()
async def get_earthquake_stats(
    min_magnitude: float = 0.0,
) -> dict:
    """
    Mevcut listedeki depremler için kapsamlı istatistik hesaplar.
    Büyüklük dağılımı, derinlik dağılımı, en büyük deprem bilgileri döner.

    Args:
        min_magnitude: İstatistiğe dahil edilecek minimum büyüklük (varsayılan: 0.0)
    """
    try:
        earthquakes = await fetch_earthquakes()
    except RuntimeError as e:
        return {"error": str(e)}

    filtered = [
        eq for eq in earthquakes
        if eq["magnitude"] is not None and eq["magnitude"] >= min_magnitude
    ]

    if not filtered:
        return {
            "count":   0,
            "message": f"Büyüklük >= {min_magnitude} kriteriyle eşleşen deprem bulunamadı.",
        }

    magnitudes = [eq["magnitude"] for eq in filtered]
    depths     = [eq["depth_km"] for eq in filtered]
    largest    = max(filtered, key=lambda x: x["magnitude"])
    deepest    = max(filtered, key=lambda x: x["depth_km"])
    total      = len(magnitudes)

    mag_dist = {"0-1": 0, "1-2": 0, "2-3": 0, "3-4": 0, "4-5": 0, "5+": 0}
    for m in magnitudes:
        if m < 1:   mag_dist["0-1"] += 1
        elif m < 2: mag_dist["1-2"] += 1
        elif m < 3: mag_dist["2-3"] += 1
        elif m < 4: mag_dist["3-4"] += 1
        elif m < 5: mag_dist["4-5"] += 1
        else:       mag_dist["5+"]  += 1

    depth_dist = {
        "sığ (<10 km)":    sum(1 for eq in filtered if eq["depth_km"] < 10),
        "orta (10-70 km)": sum(1 for eq in filtered if 10 <= eq["depth_km"] < 70),
        "derin (>70 km)":  sum(1 for eq in filtered if eq["depth_km"] >= 70),
    }

    return {
        "count":                   total,
        "min_magnitude_filter":    min_magnitude,
        "average_magnitude":       round(sum(magnitudes) / total, 2),
        "max_magnitude":           max(magnitudes),
        "min_magnitude_observed":  min(magnitudes),
        "average_depth_km":        round(sum(depths) / total, 1),
        "max_depth_km":            max(depths),
        "largest_earthquake":      largest,
        "deepest_earthquake":      deepest,
        "magnitude_distribution":  mag_dist,
        "depth_distribution":      depth_dist,
        "source":                  "Kandilli Rasathanesi (KOERI)",
    }


@mcp.tool()
async def get_significant_earthquakes(
    threshold: float = 4.0,
) -> dict:
    """
    Önemli (büyük) depremleri listeler. Varsayılan eşik 4.0.
    Haber değeri taşıyabilecek depremleri bulmak için kullanılır.

    Args:
        threshold: Önemli deprem eşiği (varsayılan: 4.0)
    """
    try:
        earthquakes = await fetch_earthquakes()
    except RuntimeError as e:
        return {"error": str(e), "earthquakes": []}

    significant = [
        eq for eq in earthquakes
        if eq["magnitude"] is not None and eq["magnitude"] >= threshold
    ]

    return {
        "count":       len(significant),
        "threshold":   threshold,
        "source":      "Kandilli Rasathanesi (KOERI)",
        "earthquakes": significant,
    }


@mcp.tool()
async def get_depth_analysis(
    depth_type: str = "all",
    limit: int = 50,
) -> dict:
    """
    Deprem derinlik analizini yapar. Sığ, orta ve derin depremleri filtreler.

    Derinlik kategorileri:
    - "sığ"   → 0-10 km (yüzeye yakın, daha hasarlı olabilir)
    - "orta"  → 10-70 km
    - "derin" → 70+ km
    - "all"   → tüm derinlikler (varsayılan)

    Args:
        depth_type: Derinlik kategorisi ("sığ", "orta", "derin", "all")
        limit: Maksimum sonuç sayısı (varsayılan: 50)
    """
    try:
        earthquakes = await fetch_earthquakes()
    except RuntimeError as e:
        return {"error": str(e), "earthquakes": []}

    dt = normalize(depth_type)
    if dt in ("sig", "sigi", "sığ", "sıg"):
        filtered = [eq for eq in earthquakes if eq["depth_km"] < 10]
        label = "Sığ (< 10 km)"
    elif dt == "orta":
        filtered = [eq for eq in earthquakes if 10 <= eq["depth_km"] < 70]
        label = "Orta (10-70 km)"
    elif dt == "derin":
        filtered = [eq for eq in earthquakes if eq["depth_km"] >= 70]
        label = "Derin (>= 70 km)"
    elif dt == "all":
        filtered = earthquakes
        label = "Tümü"
    else:
        return {
            "error": f"Geçersiz derinlik kategorisi: '{depth_type}'. "
                     "Geçerli değerler: 'sığ', 'orta', 'derin', 'all'",
            "earthquakes": [],
        }

    filtered = filtered[:limit]
    depths = [eq["depth_km"] for eq in filtered]

    return {
        "count":             len(filtered),
        "depth_category":    label,
        "average_depth_km":  round(sum(depths) / len(depths), 1) if depths else None,
        "max_depth_km":      max(depths) if depths else None,
        "min_depth_km":      min(depths) if depths else None,
        "source":            "Kandilli Rasathanesi (KOERI)",
        "earthquakes":       filtered,
    }


@mcp.tool()
async def get_city_ranking(
    min_magnitude: float = 0.0,
    top_n: int = 10,
) -> dict:
    """
    Deprem sayısına göre şehirleri/illeri sıralar.
    En çok deprem kaydedilen bölgeleri listeler.

    Args:
        min_magnitude: Sayıma dahil edilecek minimum büyüklük (varsayılan: 0.0)
        top_n: Kaç şehir listeleneceği (varsayılan: 10, max: 50)
    """
    try:
        earthquakes = await fetch_earthquakes()
    except RuntimeError as e:
        return {"error": str(e), "ranking": []}

    top_n = min(max(1, top_n), 50)

    filtered = [
        eq for eq in earthquakes
        if eq["magnitude"] is not None and eq["magnitude"] >= min_magnitude
    ]

    city_data: dict[str, dict] = {}
    for eq in filtered:
        city = eq["city"] if eq["city"] else "BELİRSİZ"
        if city not in city_data:
            city_data[city] = {"city": city, "count": 0, "magnitudes": [], "last_datetime": None}
        city_data[city]["count"] += 1
        if eq["magnitude"] is not None:
            city_data[city]["magnitudes"].append(eq["magnitude"])
        if city_data[city]["last_datetime"] is None:
            city_data[city]["last_datetime"] = eq["datetime"]

    ranking = []
    for d in city_data.values():
        mags = d["magnitudes"]
        ranking.append({
            "city":            d["city"],
            "count":           d["count"],
            "max_magnitude":   max(mags) if mags else None,
            "avg_magnitude":   round(sum(mags) / len(mags), 2) if mags else None,
            "last_earthquake": d["last_datetime"],
        })

    ranking.sort(key=lambda x: x["count"], reverse=True)

    return {
        "total_earthquakes": len(filtered),
        "min_magnitude":     min_magnitude,
        "top_n":             top_n,
        "source":            "Kandilli Rasathanesi (KOERI)",
        "ranking":           ranking[:top_n],
    }


if __name__ == "__main__":
    mcp.run()
