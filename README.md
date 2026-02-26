# kandilli-mcp

MCP Server for Kandilli Observatory Earthquake Data

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![MCP](https://img.shields.io/badge/FastMCP-2.x-green)](https://gofastmcp.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Veri Kaynağı](https://img.shields.io/badge/Veri-KOERI%20Kandilli-red)](http://www.koeri.boun.edu.tr)

Boğaziçi Üniversitesi Kandilli Rasathanesi ve Deprem Araştırma Enstitüsü (KOERI) gerçek zamanlı deprem verilerini MCP protokolü üzerinden sunar. Claude Desktop ve diğer AI agent'larla doğrudan kullanılabilir.

---

## ⚠️ Önemli Uyarılar

- **LLM'ler halüsinasyon yapabilir** — Verileri mutlaka resmi kaynaktan doğrulayın
- **Acil durumlarda AFAD'ı arayın** — 122
- **Eğitim / araştırma amaçlıdır** — Sorumluluk kullanıcıya aittir

---

## 🚀 Kurulum

### Hızlı Kurulum

```bash
# Repo'yu klonla
git clone https://github.com/MustafaKemal0146/kandilli-mcp
cd kandilli-mcp

# Bağımlılıkları kur
pip install -e .
```

Veya doğrudan:

```bash
pip install mcp[cli] httpx beautifulsoup4 pydantic
```

### uvx ile Tek Satır Kurulum

```bash
uvx --from git+https://github.com/MustafaKemal0146/kandilli-mcp kandilli-mcp
```

---

## 🖥️ Claude Desktop ile Kullanım

`~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) veya
`%APPDATA%\Claude\claude_desktop_config.json` (Windows) dosyasını açın ve `mcpServers` altına ekleyin:

```json
{
  "mcpServers": {
    "kandilli": {
      "command": "python",
      "args": ["/tam/yol/kandilli-mcp/server.py"]
    }
  }
}
```

> **İpucu:** `python` yerine `python3` veya sanal ortam Python yolunu kullanabilirsiniz.
> Örn: `/Users/kullanici/.venv/bin/python`

Değişiklikten sonra **Claude Desktop'ı yeniden başlatın.**

### uvx ile Claude Desktop Kurulumu

```json
{
  "mcpServers": {
    "kandilli": {
      "command": "uvx",
      "args": [
        "--from", "git+https://github.com/MustafaKemal0146/kandilli-mcp",
        "kandilli-mcp"
      ]
    }
  }
}
```

---

## 🛠️ Kullanılabilir Araçlar (MCP Tools)

**9 araç** ile kapsamlı deprem sorgulama ve analiz.

| Araç | Açıklama | Parametreler |
|------|----------|--------------|
| `get_recent_earthquakes` | Son N depremi listeler | `limit` (varsayılan: 20, max: 500) |
| `get_latest_earthquake` | En son tek depremi getirir | — |
| `get_earthquakes_by_magnitude` | Büyüklük aralığına göre filtreler | `min_magnitude` (3.0), `max_magnitude`, `limit` (50) |
| `get_earthquakes_by_location` | Konum/il/bölge adına göre arama | `keyword`, `limit` (30) |
| `get_earthquakes_by_date` | Belirli güne ait depremler | `date` (YYYY-MM-DD), `limit` (100) |
| `get_earthquake_stats` | Kapsamlı istatistik: büyüklük + derinlik dağılımı | `min_magnitude` (0.0) |
| `get_significant_earthquakes` | Büyük depremleri listeler | `threshold` (4.0) |
| `get_depth_analysis` | Derinlik analizini (sığ/orta/derin) yapar | `depth_type` ("all"), `limit` (50) |
| `get_city_ranking` | Şehirleri deprem sayısına göre sıralar | `min_magnitude` (0.0), `top_n` (10) |

### Örnek JSON Çıktısı

```json
{
  "count": 2,
  "source": "Kandilli Rasathanesi (KOERI)",
  "earthquakes": [
    {
      "datetime":        "2024-09-15T01:23:45",
      "date":            "2024-09-15",
      "time":            "01:23:45",
      "latitude":        38.1234,
      "longitude":       26.5678,
      "depth_km":        7.0,
      "depth_category":  "sığ",
      "magnitude":       3.2,
      "magnitude_md":    3.2,
      "magnitude_ms":    null,
      "magnitude_mb":    null,
      "magnitude_mw":    null,
      "location":        "IZMIR KORFEZI (EGE)",
      "city":            "IZMIR"
    }
  ]
}
```

---

## 📊 Örnek Sorular (Claude ile)

```
# Anlık durum
En son deprem nerede ve ne zaman oldu?
Şu an Türkiye'de deprem aktivitesi var mı?

# Büyüklük bazlı sorgular
Son depremlerde 4 üzeri kaç tane var?
Bu hafta 5 ve üzeri deprem oldu mu?
2 ile 3 arasındaki depremleri listele

# Lokasyon bazlı sorgular
İzmir'deki son depremleri göster
Marmara Denizi'nde deprem aktivitesi nasıl?
Kahramanmaraş'ta son zamanlarda deprem oldu mu?
Ege'deki depremlerin listesi

# Tarih bazlı sorgular
Bugünkü tüm depremleri listele
Dünkü depremleri getir

# İstatistik ve analiz
Son depremlerin büyüklük ortalaması nedir?
En çok deprem yaşanan iller hangileri?
Sığ depremlerin (10 km altı) listesini göster
Derin depremlerin istatistiklerini ver
Büyüklük dağılımı nasıl görünüyor?

# Karşılaştırmalı analiz
İzmir ile Ankara'yı deprem sayısı açısından karşılaştır
Sığ ve derin depremlerin ortalama büyüklüklerini karşılaştır
En tehlikeli (sığ + büyük) depremleri bul
```

---

## 🔍 Veri Kaynağı & Kapsam

### Kandilli Rasathanesi (KOERI)

- **Kaynak:** Boğaziçi Üniversitesi Kandilli Rasathanesi ve Deprem Araştırma Enstitüsü
- **URL:** http://www.koeri.boun.edu.tr/scripts/lst0.asp
- **Kapsam:** Son ~500 deprem (genellikle son birkaç gün)
- **Güncelleme:** Gerçek zamanlı, Kandilli'nin yayınlama sıklığına bağlı
- **Encoding:** windows-1254 (Türkçe karakter desteği)
- **Format:** HTML içinde `<pre>` tag'i, space-separated tablo

### Veri Alanları

| Alan | Açıklama |
|------|----------|
| `datetime` | ISO 8601 formatında tarih+saat |
| `latitude / longitude` | Enlem / Boylam (ondalık derece) |
| `depth_km` | Odak derinliği (km) |
| `depth_category` | `sığ` / `orta` / `derin` |
| `magnitude` | En büyük geçerli büyüklük (MW > MS > MB > MD önceliği) |
| `magnitude_md/ms/mb/mw` | Ayrı büyüklük ölçümleri (yoksa `null`) |
| `location` | Bölge / deniz adı |
| `city` | En yakın il |

### Derinlik Kategorileri

| Kategori | Derinlik | Not |
|----------|----------|-----|
| **Sığ** | < 10 km | Yüzeye yakın, daha fazla hasar yapabilir |
| **Orta** | 10 – 70 km | En yaygın kategori |
| **Derin** | > 70 km | Geniş alana yayılır, genelde az hasar |

---

## 🧪 Manuel Test

```bash
# Sunucuyu doğrudan çalıştır (stdio modu)
python server.py

# Parse testi
python - <<'EOF'
import asyncio, json, sys
sys.path.insert(0, ".")
from server import fetch_earthquakes

async def main():
    data = await fetch_earthquakes()
    print(f"Toplam deprem: {len(data)}")
    print(json.dumps(data[0], ensure_ascii=False, indent=2))

asyncio.run(main())
EOF
```

---

## ⚙️ Bilinen Sınırlamalar

- Kandilli sayfası yaklaşık **son 500 depremi** listeler (genellikle son 3-5 gün)
- Veriler gerçek zamanlı değildir; Kandilli'nin güncelleme sıklığına bağlıdır
- Kandilli sunucusu yoğun trafik veya bakım dönemlerinde zaman zaman yanıt vermeyebilir
- Büyüklük bilgisi olmayan depremler (`null`) bazı filtrelerde görünmez

---

## 📋 Geliştirme

```
kandilli-mcp/
├── server.py          # Ana MCP sunucusu (9 tool)
├── pyproject.toml     # Paket tanımı ve bağımlılıklar
└── README.md          # Bu dosya
```

### Bağımlılıklar

| Paket | Versiyon | Amaç |
|-------|----------|------|
| `mcp[cli]` | ≥ 1.0.0 | MCP protokol altyapısı |
| `httpx` | ≥ 0.27.0 | Async HTTP istemci |
| `beautifulsoup4` | ≥ 4.12.0 | HTML parse |
| `pydantic` | ≥ 2.0.0 | Veri doğrulama |

---

## 📜 Lisans

MIT — Detaylar için `LICENSE` dosyasına bakınız.

---

**Veri Kaynağı:** [Boğaziçi Üniversitesi Kandilli Rasathanesi ve Deprem Araştırma Enstitüsü](http://www.koeri.boun.edu.tr)

Veriler Kandilli'nin kamuya açık web sitesinden alınmaktadır.
Ticari kullanım için Boğaziçi Üniversitesi Rektörlüğü'nün yazılı izni gerekmektedir.
