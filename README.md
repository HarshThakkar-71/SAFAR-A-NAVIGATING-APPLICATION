# 🧭 SAFAR — Smart AI Navigation System

**AI-powered route planning with safety intelligence, live tracking & emergency SOS.**
Professional navigation app built for hackathons & demos.

---

## ⚡ Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app
streamlit run safar_app.py
```

Open your browser at `http://localhost:8501`

---

## 📁 File Structure

```
safar/
├── safar_app.py        ← Streamlit frontend (UI, layout, interactions)
├── safar_core.py       ← Core logic (routing, safety, tracking, SOS)
├── geo_utils.py        ← Geocoding with retry, fallback & 60+ hardcoded places
├── graph_loader.py     ← OSMnx graph loading with disk caching
├── map_utils.py        ← Folium map building (routes, markers, heatmap)
├── requirements.txt    ← Python dependencies
└── .safar_cache/       ← Auto-created: cached road graphs (speeds up reruns)
```

---

## ✨ Features

| Feature | Description |
|---|---|
| 🗺️ Route Planning | Fastest + Safest routes between any two locations |
| 📍 Geocoding | 60+ hardcoded Indian cities + Nominatim with retry |
| 🛡️ Safety Score | AI-computed 0–100 safety rating with explanation |
| 🚗 Live Tracking | Animated vehicle simulation along route |
| 🔥 Danger Heatmap | Simulated danger zones overlay |
| 📴 Offline Mode | Dead-reckoning position prediction |
| 🚨 Emergency SOS | Instant alert with police/ambulance/fire contacts |
| 🗺️ Real Roads | OSMnx + OpenStreetMap road network routing |

---

## 🏙️ Pre-loaded Locations

Works instantly (no geocoding needed) for 60+ Indian locations including:

**Delhi:** Connaught Place, India Gate, Red Fort, IGI Airport, Chandni Chowk, Hauz Khas...
**Mumbai:** Gateway of India, CST Station, Bandra, Andheri, Marine Drive...
**Bangalore:** Koramangala, Indiranagar, Whitefield, Electronic City, MG Road...
**And:** Chennai, Hyderabad, Ahmedabad, Pune, Kolkata

---

## 🔧 Tech Stack

- **Frontend:** Streamlit (light theme, card-based, 2-column layout)
- **Maps:** Folium + AntPath animations + HeatMap plugin
- **Routing:** OSMnx + NetworkX (real OpenStreetMap roads)
- **Geocoding:** Geopy Nominatim + hardcoded fallbacks
- **Tracking:** Session-state simulation with step-by-step advancement

---

## 🎯 Demo Tips (Hackathon)

1. Start with **Connaught Place → Hauz Khas** (Delhi) — always works instantly
2. Toggle **Danger Heatmap** to show safety intelligence
3. Click **Start Simulation** to show live tracking
4. Hit **SOS** to demo emergency response
5. Toggle **Offline Mode** to show dead-reckoning

---

## 📝 Notes

- First route for a new area downloads the road graph (~5-30 seconds)
- Subsequent runs use cached graphs (instant)
- App works without OSMnx (uses interpolated routes as fallback)
- All geocoding includes retry logic and India-context fallback

---

*Built with ❤️ for SAFAR — Smart AI for All Roads*
