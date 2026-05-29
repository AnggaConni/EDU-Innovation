"""
=======================================================================
  EDU INNOVATION RADAR v0.3 — Global Intelligence Engine
  AI Engine : Google Gemini 2.5 Flash
  Mode      : Multi-Schedule Tracker (Data = 2 Days, Resume = 3 Months)
  Feature   : Append-Only DB, Smart Execution, Independent Force Crawl
  Updated   : + Retry Logic, + Env Config, + Title Normalization,
              + Expanded Keywords
=======================================================================
"""

import os
import json
import logging
import random
import hashlib
import time
import unicodedata                         # ✅ NEW: for title normalization
from datetime import datetime, timedelta
import requests

# ── Logging Configuration ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
log = logging.getLogger("InnovationRadar")

# ── File Paths ──
BASE_DIR         = os.path.dirname(os.path.abspath(__file__))
DATA_FILE        = os.path.join(BASE_DIR, "data.json")
RESUME_FILE      = os.path.join(BASE_DIR, "resume.json")
HISTORY_FILE     = os.path.join(BASE_DIR, "history.json")
REPORT_MD_FILE   = os.path.join(BASE_DIR, "report.md")

# ✅ NEW: Configurable schedule intervals via environment variables.
# You can set these in your system/CI without touching the code.
# Defaults: data every 2 days, resume every 90 days, max 3 items per run.
DATA_INTERVAL_DAYS   = int(os.environ.get("DATA_INTERVAL_DAYS", 2))
RESUME_INTERVAL_DAYS = int(os.environ.get("RESUME_INTERVAL_DAYS", 90))
MAX_ITEMS_PER_RUN    = int(os.environ.get("MAX_ITEMS_PER_RUN", 3))

# ── Keywords for Search Grounding ──
# ✅ EXPANDED: From 7 → 60 keywords across 10 thematic categories
KEYWORDS = [

    # --- Digital Learning & Access ---
    "offline education innovation rural school",
    "low cost digital classroom developing country",
    "community built e-learning platform local language",
    "solar powered learning station rural village",
    "DIY educational technology grassroots innovation",
    "offline first learning app remote area",
    "repurposed smartphones for education community project",
    "digital literacy training underserved youth",
    "portable classroom technology low infrastructure",
    "micro learning via feature phone developing country",
    "local server offline wikipedia school",
    "community wifi learning hub rural",
    "LMS innovation for low bandwidth environment",
    "Immersive learning with low cost VR cardboard",
    "Augmented reality for learning education",
    "IFP technology for interactive learning low resource setting",

    # --- Teaching Innovation ---
    "grassroots teacher innovation classroom",
    "self taught educator creative learning method",
    "project based learning low resource school",
    "peer to peer education village community",
    "interactive storytelling education local culture",
    "gamified learning low tech classroom",
    "community driven curriculum innovation",
    "multilingual teaching innovation indigenous language",
    "creative science experiment low cost materials",
    "teacher made learning aids recycled materials",
    "student centered learning rural school",
    "informal education innovation developing world",
    "Gamification in low resource educational settings",
    "Deep learning for teacher training in underserved areas",
    "Social emotional learning innovation grassroots initiative",
    "Pedagogy of care community education project",
    "Mental recreation for learning innovation low resource school",
    "Experiential learning through local environment project",
    "Immagination based learning innovation rural classroom",

    # --- Inclusive Education ---
    "inclusive education innovation disability low resource",
    "DIY assistive learning tools special needs",
    "braille learning innovation local materials",
    "sign language education community initiative",
    "accessible classroom technology developing country",
    "community learning support for disabled students",
    "low cost hearing aid classroom adaptation",
    "education for remote indigenous communities",
    "girls education grassroots initiative rural",
    "education innovation refugee camp learning",
    "UDL principles applied in low resource classroom",
    "Special needs education innovation grassroots",
    "LRE innovation for inclusive education developing world",
    "NCLB innovation for inclusive education low resource setting",
    "DSM 5 based learning support innovation grassroots initiative",
    "Pedagogy of inclusion community education project",
    "Paraeducator training innovation for inclusive education rural school",
    "Co-teaching model innovation for inclusive education low resource setting",
    "Neurodivergent friendly learning environment innovation grassroots initiative",
    "Typical development milestones based learning support innovation grassroots initiative",
    "Personalized learning plan innovation for inclusive education developing world",
    "PEER support network innovation for inclusive education rural community",
    "Assistive technology innovation for inclusive education low resource setting",
    "ICD 11 based learning support innovation grassroots initiative",
    "Multiple Intelligence theory based learning support innovation grassroots initiative",
    "Gifted education innovation grassroots initiative low resource setting",
    "Talented education innovation grassroots initiative developing world",
    "Neuroscience informed learning support innovation grassroots initiative",
    "Neurodiversity acceptance education innovation grassroots initiative",
    "ABA based learning support innovation for inclusive education grassroots initiative",
    "CBT based mental health support innovation for inclusive education grassroots initiative",
    "Therapy informed learning support innovation for inclusive education grassroots initiative",
    "Assessment accommodation innovation for inclusive education grassroots initiative",
    "Intervention accommodation innovation for inclusive education grassroots initiative",
    "RTI based learning support innovation for inclusive education grassroots initiative",
    "MTSS based learning support innovation for inclusive education grassroots initiative",
    "Collaboration between general and special education innovation grassroots initiative",
    "Parents as partners in inclusive education innovation grassroots initiative",
    "IEP development innovation for inclusive education grassroots initiative",

    # --- STEAM & Maker Culture ---
    "makerspace rural school grassroots innovation",
    "DIY robotics education low cost",
    "community science lab developing country",
    "local materials engineering education project",
    "student innovation challenge village school",
    "homemade science kit rural classroom",
    "coding education offline community center",
    "low cost STEAM education education toolkit",
    "low cost STEM education education toolkit",
    "youth innovation hub underserved area",
    "recycled electronics for STEAM learning",
    "Battery free science experiment innovation grassroots initiative",
    "Electrolysis based energy learning innovation grassroots initiative",
    "Plastic to fuel science experiment innovation grassroots initiative",
    "Olive oil lamp science experiment innovation grassroots initiative",
    "River turbine energy learning innovation grassroots initiative",
    "Nuclear literacy education innovation grassroots initiative",
    "Quantum computing education innovation grassroots initiative",
    "Artificial Sun science experiment innovation grassroots initiative",
    "Basic Radiation for School Education",

    # --- Libraries & Knowledge Sharing ---
    "mobile library innovation rural community",
    "community reading movement grassroots",
    "book sharing initiative underserved neighborhoods",
    "village learning center local innovation",
    "open educational resources local adaptation",
    "homemade classroom library low income school",
    "community storytelling and literacy project",
    "digital archive indigenous knowledge education",
    "DEWEY system adaptation local library",

    # --- Alternative & Informal Education ---
    "informal learning space community innovation",
    "street children education grassroots project",
    "education through local crafts tradition",
    "village apprenticeship learning model",
    "community mentorship education initiative",
    "youth empowerment through education innovation",
    "alternative school low cost community driven",
    "learning through farming and local practice",
    "education through environmental conservation project",
    "Refugee education innovation grassroots initiative",
    "Rural education innovation grassroots initiative",
    "CLC innovation for informal education developing world",
    "NGO based education innovation grassroots initiative",
    "Boarding school alternative education innovation grassroots initiative",
    "Home Schooling innovation grassroots initiative",
    "Unschooling innovation grassroots initiative",
    "Deschooling innovation grassroots initiative",
    
    # --- Educational Infrastructure ---
    "low cost classroom construction innovation",
    "DIY school furniture local materials",
    "recycled material classroom design",
    "portable school kit disaster area",
    "solar powered computer lab rural school",
    "rainproof outdoor classroom innovation",
    "community built school developing world",
    "eco friendly school infrastructure grassroots",
    "RAMP innovation for school accessibility developing world",
    "LIFT innovation for school infrastructure low resource setting",
    "Escalator innovation for school infrastructure developing world",
    "Guiding block innovation for school infrastructure low resource setting",
    "Automatic door innovation for school infrastructure developing world",
    "Trampoline innovation for school infrastructure low resource setting",
    "Garden classroom innovation for school infrastructure grassroots initiative",
    "Field classroom innovation for school infrastructure grassroots initiative",
    "Development of inclusive playground innovation for school infrastructure grassroots initiative",
    "Table and chair innovation for inclusive classroom innovation for school infrastructure grassroots initiative",
    "Foundry/workbench innovation for school infrastructure grassroots initiative",
    "Gallery space innovation for school infrastructure grassroots initiative",
    "Ballroom space innovation for school infrastructure grassroots initiative",

    # --- Educational Media & Communication ---
    "community radio for education rural",
    "podcast learning initiative local language",
    "educational comic innovation developing country",
    "DIY projector for classroom learning",
    "low bandwidth education content delivery",
    "SMS based learning system rural students",
    "educational animation grassroots creators",
    "open source education platform community adaptation",

    # --- Social & Cultural Learning ---
    "cultural heritage education innovation community",
    "traditional knowledge integration school curriculum",
    "intergenerational learning local wisdom",
    "local language preservation through education",
    "arts based education grassroots initiative",
    "community theater for education awareness",
    "education for peacebuilding local initiative",
    "environmental education grassroots movement",
    "Narrative based learning innovation grassroots initiative",
]

# =====================================================================
# HELPER FUNCTIONS
# =====================================================================

def load_json_file(filepath, default_val):
    if not os.path.exists(filepath):
        return default_val
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        log.error(f"Error loading {filepath}: {e}")
        return default_val

def save_json_file(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def save_text_file(filepath, text):
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(text)

def extract_json_safe(text):
    try:
        text = text.strip()
        tick3 = '`' * 3
        if text.startswith(tick3 + 'json'): text = text[7:]
        if text.startswith(tick3): text = text[3:]
        if text.endswith(tick3): text = text[:-3]
        text = text.strip()
        start_idx = text.find('{') if '{' in text else text.find('[')
        end_idx = text.rfind('}') if '}' in text else text.rfind(']')
        if start_idx != -1 and end_idx != -1:
            return json.loads(text[start_idx:end_idx+1])
        return json.loads(text)
    except Exception as e:
        log.error(f"JSON Parse Error: {e}")
        return None

# ✅ NEW: Normalize title text before hashing.
# This prevents duplicates caused by different capitalizations
# or Unicode quirks (e.g., "café" vs "cafe", "DIY Tool" vs "diy tool").
def normalize_title(title):
    """Lowercase + strip + Unicode normalize a title for consistent hashing."""
    return unicodedata.normalize("NFKC", title).strip().lower()

def get_coordinates(location_name):
    if not location_name or str(location_name).lower() == "unknown":
        return None, None
    url = f"https://nominatim.openstreetmap.org/search?q={location_name}&format=json&limit=1"
    headers = {"User-Agent": "InnovationRadarApp/9.1 (research-bot)"}
    try:
        time.sleep(1.5)
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        log.warning(f"Geocoding failed for {location_name}: {e}")
    return None, None

def get_current_quarter():
    now = datetime.now()
    quarter = (now.month - 1) // 3 + 1
    return f"Q{quarter} {now.year}"

# =====================================================================
# CORE AI ENGINE (GEMINI)
# =====================================================================

def call_gemini(api_key, prompt, system_instruction, use_search=False, expect_json=True):
    # Pastikan prompt adalah string. Jika berupa objek/dict, ubah jadi teks JSON.
    if not isinstance(prompt, str):
        prompt = json.dumps(prompt)
        
    model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash") # Atau menyesuaikan
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
    
    # PERBAIKAN LOGIKA: Jika pakai Search, HARUS text/plain.
    mime_type = "text/plain"
    if expect_json and not use_search:
        mime_type = "application/json"
    
    # Konfigurasi payload
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "systemInstruction": {"parts": [{"text": system_instruction}]},
        "generationConfig": {
            "temperature": 0.5,
            "maxOutputTokens": 8192,
            "responseMimeType": mime_type
        }
    }
        
    if use_search:
        payload["tools"] = [{"googleSearch": {}}]
        
    headers = {
        'Content-Type': 'application/json',
        'x-goog-api-key': api_key
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=120)
        response.raise_for_status()
        data = response.json()
        raw_text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        
        # Meskipun dari LLM text/plain, Python kita (extract_json_safe) akan mengubahnya ke JSON
        if expect_json:
            return extract_json_safe(raw_text)
        return raw_text
    except Exception as e:
        error_details = e.response.text if hasattr(e, 'response') and e.response is not None else str(e)
        log.error(f"Gemini API Error: {error_details}")
        return None

# ✅ NEW: Retry wrapper around call_gemini.
# If Gemini fails (network glitch, timeout, empty response),
# it will automatically try again up to `retries` times.
# Each retry waits longer: 1s, 2s, 4s (exponential backoff).
def call_gemini_with_retry(api_key, prompt, system_instruction, retries=3, **kwargs):
    for attempt in range(retries):
        try:
            result = call_gemini(api_key, prompt, system_instruction, **kwargs)
            if result:
                return result
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            if status_code in [400, 403, 404]: # Error fatal yang tidak akan sembuh dengan retry
                log.error(f"Fatal HTTP Error {status_code}. Aborting retry.")
                break
            elif status_code == 429: # Too many requests
                log.warning("Rate limit hit. Retrying...")
                
        wait_time = 2 ** attempt
        log.warning(f"Gemini call failed (attempt {attempt + 1}/{retries}). Retrying in {wait_time}s...")
        time.sleep(wait_time)
        
    return None

# =====================================================================
# 5-LAYER PIPELINE (DISCOVERY)
# ✅ All pass_* functions now use call_gemini_with_retry instead of call_gemini
# =====================================================================

def pass_1_validate(api_key, raw_content):
    sys_prompt = """Determine whether the following content represents a real-world grassroots or local innovation SPECIFICALLY IN EDUCATION OR LEARNING. Criteria: Must solve a clear educational problem, involve teaching/learning methods, literacy, STEAM, or schooling tools. Return exactly: {"is_innovation": true/false, "confidence": 0.0-1.0}"""
    return call_gemini_with_retry(api_key, raw_content, sys_prompt)   # ✅ changed

def pass_2_extract(api_key, raw_content):
    sys_prompt = """You are an expert Educational Curriculum Designer and OSINT Analyst. 
    Extract structured data about this educational innovation. 
    
    CRITICAL RULES FOR SOURCES:
    - Provide ONLY direct, original website URLs (e.g., https://www.bbc.com/..., https://en.unesco.org/...).
    - STRIP OUT any Google Search redirect wrappers (DO NOT output links starting with google.com/url?q=).
    - If no direct link is available, leave the array empty [].
    
    Return EXACTLY this JSON structure:
{
  "title": "",
  "sources": [],
  "summary": "",
  "category": ["category1", "category2"],
  "innovation_level": "grassroots | semi-formal | institutional", 
  "location": {
    "country": "", 
    "region": "", 
    "city_or_village": "", 
    "institution_name": ""
  }, 
  "education_details": {
    "education_type": "formal | informal | non-formal | alternative | special_needs",
    "related_fields": ["STEM", "Arts", "Literacy", "Vocational", "Environment", "Health", "Civics", "Other"],
    "target_learners": "", 
    "learning_outcomes": [], 
    "pedagogical_approach": ""
  }, 
  "tutorial_how_to": {
    "materials_required": [], 
    "preparation_steps": [], 
    "execution_steps": [],
    "tips_for_success": ""
  }, 
  "impact": {
    "problem_solved": "", 
    "evidence_of_success": "", 
    "beneficiaries_reach": "", 
    "scale": "low | medium | high", 
    "impact_score": <int 1-10>
  }, 
  "replicability": {
    "cost_level": "low | medium | high", 
    "difficulty": "easy | medium | hard"
  }
}"""
    return call_gemini_with_retry(api_key, raw_content, sys_prompt)   # ✅ changed

def pass_3_risk(api_key, raw_content):
    sys_prompt = """Analyze the educational innovation and assess potential risks. Focus on: data privacy, child safety, cognitive overload, exclusion/accessibility barriers, cultural friction, or physical safety (only for STEAM/hardware). Return EXACTLY this JSON:
{"risk_score": <int 1-10>, "risk_type": ["data_privacy", "exclusion", "cultural", "physical", "other"], "safety_level": "low|medium|high", "needs_intervention": true/false, "explanation": ""}"""
    return call_gemini_with_retry(api_key, raw_content, sys_prompt)   # ✅ changed

def pass_4_lineage(api_key, raw_content):
    sys_prompt = """Determine the origin of knowledge behind this innovation. Options: [traditional, self-taught, internet, adapted_from_existing, formal_education]. Return EXACTLY this JSON: {"knowledge_source": ["source1"]}"""
    return call_gemini_with_retry(api_key, raw_content, sys_prompt)   # ✅ changed

def calculate_advanced_metrics(data):
    try:
        repl_map = {"easy": 10, "medium": 5, "hard": 2, "unknown": 0}
        
        # Ambil score langsung dari pass 2, default ke 5 jika gagal
        impact_val = data.get("impact", {}).get("impact_score", 5) 
        repl_val = repl_map.get(str(data.get("replicability", {}).get("difficulty", "")).lower(), 0)
        risk_val = data.get("risk_assessment", {}).get("risk_score", 1)

        # Risiko tinggi justru MENGURANGI prioritas (safety = 10 - risk)
        safety_val = 10 - risk_val 
        priority_score = int(((impact_val * 0.4) + (repl_val * 0.4) + (safety_val * 0.2)) * 10)
        data["priority_score"] = min(100, max(0, priority_score))

        is_grassroots = data.get("innovation_level", "").lower() == "grassroots"
        is_low_cost = data.get("replicability", {}).get("cost_level", "").lower() == "low"
        data["hidden_gem"] = bool(is_grassroots and is_low_cost and impact_val >= 7)

        # Flag Kritis
        risk_types = [str(x).lower() for x in data.get("risk_assessment", {}).get("risk_type", [])]
        edu_critical_risks = ["privacy", "exclusion", "safety", "harm", "abuse"]
        has_critical = any(k in t for t in risk_types for k in edu_critical_risks)
        data["critical_flag"] = bool(risk_val >= 7 and has_critical)
        
        return data
    except Exception as e:
        log.warning(f"Failed calculating metrics: {e}")
        return data

# =====================================================================
# CORE TASKS: DATA CRAWL & RESUME GENERATION
# =====================================================================

def run_discovery_pipeline(api_key, database, max_items=3):
    """Mencari data baru dan menambahkannya ke database dengan Anti-Redundansi."""
    keyword = random.choice(KEYWORDS)
    log.info(f"Initiating radar ping with keyword: '{keyword}'")

    # ==========================================
    # ANTI-REDUNDANSI 1: Beritahu AI apa yang sudah kita punya
    # ==========================================
    existing_titles = [item.get("title", "") for item in database if item.get("title")]
    
    # Ambil maksimal 50 judul secara acak agar Prompt tidak kepanjangan (hemat token)
    avoid_sample = random.sample(existing_titles, min(len(existing_titles), 50))
    avoid_str = ", ".join(avoid_sample) if avoid_sample else "None"

    # Modifikasi Prompt: Larang AI mencari inovasi yang sudah ada, dan minta format 'title' eksplisit.
    seed_prompt = f"""Search the web for 5 distinct, real-world examples of: {keyword}. 
CRITICAL RULE: DO NOT return any of these known examples: {avoid_str}.
Provide a detailed paragraph for each, AND include a list of all relevant source URLs found. 
Return a JSON object with an array 'innovations' where each item contains exactly: "title" (string), "description" (string), and "urls" (array of strings)."""
    
    seed_sys = "You are an OSINT web scraper. Use google search. IMPORTANT: Always return the direct, original source URLs. Return pure JSON."

    seed_data = call_gemini_with_retry(api_key, seed_prompt, seed_sys, use_search=True)
    if not seed_data or "innovations" not in seed_data:
        log.warning("No raw material found on this run.")
        return 0

    raw_descriptions = seed_data["innovations"]
    success_count = 0

    for idx, item in enumerate(raw_descriptions):
        if success_count >= max_items: break

        # Ambil data awal
        if isinstance(item, dict):
            raw_title = item.get("title", "Unknown Title")
            raw_text = item.get("description", str(item))
            discovered_urls = item.get("urls", [])
        else:
            raw_title = "Unknown Title"
            raw_text = str(item)
            discovered_urls = []

        # ==========================================
        # ANTI-REDUNDANSI 2: Early Check (Hemat API)
        # ==========================================
        norm_raw_title = normalize_title(raw_title)
        # Cek apakah judul mentah dari AI mirip dengan judul yang sudah ada di database kita
        is_duplicate = any(normalize_title(ext_t) in norm_raw_title or norm_raw_title in normalize_title(ext_t) for ext_t in existing_titles if ext_t)
        
        if is_duplicate and norm_raw_title != "unknown title":
            log.info(f"⏭️ AI suggested a known item. Skipping early to save API quota: {raw_title}")
            continue

        # --------------------------------------------------
        # Masuk ke Pipeline Validasi jika Lolos Pengecekan
        # --------------------------------------------------
        validation = pass_1_validate(api_key, raw_text)
        if not validation.get("is_innovation") or validation.get("confidence", 0) < 0.6:
            continue

        base_data = pass_2_extract(api_key, raw_text)
        if not base_data or not base_data.get("title"):
            continue

        # Hash Final Validation
        normalized_title = normalize_title(base_data["title"])
        country = base_data.get("location", {}).get("country", "unknown").lower()
        
        unique_string = f"{normalized_title}-{country}"
        title_hash = hashlib.md5(unique_string.encode('utf-8')).hexdigest()

        if any(db_item.get("id") == title_hash for db_item in database):
            log.info(f"⏭️ Skipping duplicate after extraction: {base_data['title']}")
            continue

        risk_data = pass_3_risk(api_key, raw_text)
        lineage_data = pass_4_lineage(api_key, raw_text)

        final_item = {
            "id": title_hash, 
            "timestamp": datetime.now().isoformat(),
            **base_data,
            "origin": lineage_data if lineage_data else {"knowledge_source": []},
            "risk_assessment": risk_data if risk_data else {}
        }

        if "sources" not in final_item: final_item["sources"] = []
        final_item["sources"] = list(set(final_item.get("sources", []) + discovered_urls))

        # Geocoding Akurat
        loc_data = final_item.get("location", {})
        country = loc_data.get("country", "")
        region = loc_data.get("region", "")
        city = loc_data.get("city_or_village", "")
        
        search_parts = [p for p in [city, region, country] if p and p.lower() != "unknown"]
        location_query = ", ".join(search_parts)
        
        lat, lon = get_coordinates(location_query)
        final_item["location"]["lat"], final_item["location"]["lon"] = lat, lon

        final_item = calculate_advanced_metrics(final_item)
        database.append(final_item)
        success_count += 1
        
        log.info(f"🔥 New Innovation Added: {final_item['title']}")

    return success_count
    
def generate_intelligence_report(api_key, database):
    """Membaca database dan menambahkan resume baru dengan rotasi ID."""
    if not database:
        log.warning("Database is empty. Skipping report generation.")
        return

    log.info("📊 Generating Periodic Intelligence Resume...")
    quarter = get_current_quarter()
    db_string = json.dumps(database, ensure_ascii=False)

    sys_prompt = """
                You are an elite AI Educator Intelligence Analyst generating a quarterly global report on education innovation.

                You will be given a JSON array containing structured innovation records.

                YOUR OBJECTIVE:
                - Detect patterns (not just summarize)
                - Identify risks and emerging threats
                - Highlight high-impact innovations
                - Identify intervention opportunities
                - Analyze knowledge evolution

                CRITICAL THINKING RULES:
                - Do NOT summarize blindly
                - Aggregate across multiple records
                - Identify trends, anomalies, and clusters
                - If data is insufficient, return empty arrays or zero values (DO NOT hallucinate)

                ----------------------------------------
                OUTPUT FORMAT (STRICT JSON ONLY)
                ----------------------------------------

                {
                "report_metadata": {
                    "report_id": "edu-current",
                    "generated_at": "YYYY-MM-DD",
                    "period": "Q_ YYYY",
                    "total_records_analyzed": 0
                },

                "global_summary": {
                    "total_education_innovations": 0,
                    "grassroots_percentage": 0,
                    "institutional_percentage": 0,
                    "formal_percentage": 0,
                    "informal_percentage": 0
                },

                "top_categories": [
                    {
                    "category": "",
                    "count": 0,
                    "trend": "increasing | decreasing | stable"
                    }
                ],

                "geographic_insights": [
                    {
                    "region": "",
                    "key_pattern": "",
                    "impact_level": "low | medium | high"
                    }
                ],

                "impact_analysis": {
                    "high_impact_cases": 0,
                    "critical_cases": 0,
                    "top_impact_types": [],
                    "emerging_impacts": []
                },

                "innovation_patterns": [
                    {
                    "pattern_name": "",
                    "description": "",
                    "regions": [],
                    "impact_level": "low | medium | high"
                    }
                ],

                "hidden_gems": [
                    {
                    "title": "",
                    "country": "",
                    "reason": ""
                    }
                ],

                "intervention_opportunities": [
                    {
                    "type": "training | funding | regulation | research | collaboration | perception | evaluation | criticism",
                    "target": "",
                    "priority_level": "low | medium | high",
                    "justification": ""
                    }
                ],

                "knowledge_insights": {
                    "most_common_source": "",
                    "trend": "increasing | decreasing | shifting | fostering | promoting",
                    "observation": ""
                },

                "recommendations": [
                    ""
                ],

                "charts": {
                    "innovation_by_region": [
                    { "region": "", "count": 0 }
                    ],
                    "impact_distribution": [
                    { "level": "low | medium | high", "count": 0 }
                    ],
                    "knowledge_source_trend": [
                    { "source": "", "count": 0 }
                    ],
                    "learning_outcomes": [
                    { "level": "low | medium | high", "count": 0 }
                    ]
                }
                }

                ----------------------------------------
                ANALYSIS GUIDELINES
                ----------------------------------------

                1. GLOBAL SUMMARY
                - Calculate percentages from dataset
                - Ensure total ≈ 100%

                2. TOP CATEGORIES
                - Rank by frequency
                - Trend = based on relative dominance in dataset (not time series)

                3. GEOGRAPHIC INSIGHTS
                - Identify regional clusters
                - Highlight dominant innovation type or issue per region

                4. IMPACT ANALYSIS (Dropouts, Impacts)
                - High impact = impact_score >= 6
                - Critical = impact_score >= 8
                - Identify repeated regressed patterns

                5. EDUCATION INNOVATION PATTERNS
                - Group similar innovations into themes
                - Example: "DIY energy generator systems learning", "low-cost educational tools"

                6. HIDDEN GEMS
                - Must meet ALL:
                - grassroots
                - low cost
                - high impact
                - High Collaboration Potential (based on replicability and risk)
                - Select top 5–10 only

                7. INTERVENTION OPPORTUNITIES
                - Focus on:
                - high impact + high priority
                - scalable innovations needing support

                8. KNOWLEDGE INSIGHTS
                - Analyze distribution of:
                - traditional
                - self-taught
                - internet
                - adapted
                - formal

                9. RECOMMENDATIONS
                - Must be actionable (not generic)
                - Max 5–8 items

                ----------------------------------------
                STRICT RULES
                ----------------------------------------

                - Output MUST be valid JSON (no markdown, no explanation)
                - Do NOT include text outside JSON
                - Do NOT hallucinate missing data
                - Keep text concise but meaningful
                """

    prompt = f"Analyze the following innovation dataset and generate the report.\n\nDATASET:\n{db_string}"
    new_report = call_gemini_with_retry(api_key, prompt, sys_prompt, expect_json=True)

    if new_report:
        total_records = len(database)
        
        # 1. Hitung manual dengan Python agar 100% akurat
        grass_count = sum(1 for x in database if x.get("innovation_level") == "grassroots")
        semi_count = sum(1 for x in database if x.get("innovation_level") == "semi-formal")
        inst_count = sum(1 for x in database if x.get("innovation_level") == "institutional")

        # 2. Paksa (override) hasil halusinasi matematika AI
        new_report["report_metadata"]["total_records_analyzed"] = total_records
        
        if "global_summary" not in new_report:
            new_report["global_summary"] = {}
            
        new_report["global_summary"]["total_innovations"] = total_records
        new_report["global_summary"]["grassroots_percentage"] = round((grass_count / total_records) * 100, 2) if total_records > 0 else 0
        new_report["global_summary"]["semi_formal_percentage"] = round((semi_count / total_records) * 100, 2) if total_records > 0 else 0
        new_report["global_summary"]["institutional_percentage"] = round((inst_count / total_records) * 100, 2) if total_records > 0 else 0

        new_report["report_metadata"]["generated_at"] = datetime.now().isoformat()
        new_report["report_metadata"]["period"] = quarter

        # ==========================================
        # PERBAIKAN 2: PAKSA HITUNGAN IMPACT ANALYSIS
        # ==========================================
        high_impact_count = sum(1 for x in database if x.get("impact", {}).get("impact_score", 0) >= 8)
        medium_impact_count = sum(1 for x in database if 4 <= x.get("impact", {}).get("impact_score", 0) <= 7)
        low_impact_count = sum(1 for x in database if x.get("impact", {}).get("impact_score", 0) <= 3)
        critical_count = sum(1 for x in database if x.get("critical_flag") == True)

        # Timpa angka di panel atas Impact Analysis
        if "impact_analysis" not in new_report:
            new_report["impact_analysis"] = {}
        new_report["impact_analysis"]["high_impact_cases"] = high_impact_count
        new_report["impact_analysis"]["critical_cases"] = critical_count

        # Timpa angka di diagram batang (Bar Chart)
        if "charts" not in new_report:
            new_report["charts"] = {}
        new_report["charts"]["impact_distribution"] =[
            {"level": "High", "count": high_impact_count},
            {"level": "Medium", "count": medium_impact_count},
            {"level": "Low", "count": low_impact_count}
        ]
        
        # Load data lama
        resume_db = load_json_file(RESUME_FILE, [])
        if not isinstance(resume_db, list): 
            resume_db = []

        # ✅ ROTASI ID: Ubah semua 'edu-current' lama menjadi 'edu-older'
        for report in resume_db:
            if isinstance(report, dict):
                if "report_metadata" not in report: report["report_metadata"] = {}
                report["report_metadata"]["report_id"] = "edu-older"

        # Setup metadata laporan baru
        new_report["report_metadata"]["generated_at"] = datetime.now().isoformat()
        new_report["report_metadata"]["period"] = quarter
        new_report["report_metadata"]["report_id"] = "edu-current"
        
        # ✅ SIMPAN HANYA SEKALI
        resume_db.append(new_report)
        save_json_file(RESUME_FILE, resume_db)
        
        # Update file Markdown untuk preview cepat
        md_content = convert_report_to_markdown(new_report)
        save_text_file(REPORT_MD_FILE, md_content)

        log.info(f"✅ Resume successfully generated and rotated. ID: edu-current")
    else:
        log.error("Failed to generate intelligence report.")

def convert_report_to_markdown(report_data):
    meta = report_data.get("report_metadata", {})
    global_sum = report_data.get("global_summary", {})
    impact = report_data.get("impact_analysis", {})

    md = f"""# Global Innovation Intelligence Report
**Period:** {meta.get('period', 'N/A')} | **Generated:** {meta.get('generated_at', 'N/A')} | **Records Analyzed:** {meta.get('total_records_analyzed', 0)}

---
## 🌍 Executive Summary
Out of {global_sum.get('total_innovations', 0)} innovations tracked:
- **{global_sum.get('grassroots_percentage', 0)}%** Grassroots
- **{global_sum.get('formal_percentage', 0)}%** Formal
- **{global_sum.get('informal_percentage', 0)}%** Informal
- **{global_sum.get('institutional_percentage', 0)}%** Institutional

## ⚠️ Emerging Impacts
- **High-Impact Cases:** {impact.get('high_impact_cases', 0)} | **Critical:** {impact.get('critical_cases', 0)}
- **Top Impacts:** {', '.join(impact.get('top_impact_types', []))}

## 💎 Hidden Gems\n"""
    for gem in report_data.get("hidden_gems", []):
        md += f"- **{gem.get('title', 'Unknown')}** ({gem.get('country', 'Unknown')})\n"

    md += "\n---\n*Report auto-generated by Innovation Radar AI Framework v9.1.*\n"
    return md

# =====================================================================
# MAIN SCHEDULER & EXECUTION CONTROLLER
# =====================================================================

def main():
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    run_type = os.environ.get("RUN_TYPE", "auto").strip().lower()

    if not api_key:
        log.error("GEMINI_API_KEY not found or empty!")
        return

    try:
        db = load_json_file(DATA_FILE, [])
        # ✅ NEW: Auto-correction jika format data.json salah (misal: terbaca sisa ICH Radar)
        if not isinstance(db, list):
            log.warning("Format data.json bukan List! Melakukan auto-correction...")
            if isinstance(db, dict) and "inventory" in db:
                db = db["inventory"]  # Ekstrak list jika ini file bekas ICH Radar
            else:
                db = []  # Reset menjadi list kosong agar aman di-append
        history = load_json_file(HISTORY_FILE, {
            "last_data_crawl": "2000-01-01T00:00:00",
            "last_resume_gen": "2000-01-01T00:00:00"
        })

        now = datetime.now()
        last_data_time = datetime.fromisoformat(history.get("last_data_crawl", "2000-01-01T00:00:00"))
        last_resume_time = datetime.fromisoformat(history.get("last_resume_gen", "2000-01-01T00:00:00"))

        do_data = False
        do_resume = False

        if run_type == "force_data":
            do_data = True
            log.info("🚀 TRIGGER: Force Crawl Data (Ignoring Schedule)")
        elif run_type == "force_resume":
            do_resume = True
            log.info("🚀 TRIGGER: Force Resume Generate (Ignoring Schedule)")
        elif run_type == "force_both":
            do_data = True
            do_resume = True
            log.info("🚀 TRIGGER: Force Both Data & Resume (Ignoring Schedule)")
        else:
            log.info("⏳ TRIGGER: Auto Schedule Mode. Checking Timestamps...")

            # ✅ CHANGED: Using env-var constants instead of hardcoded values
            if now - last_data_time >= timedelta(days=DATA_INTERVAL_DAYS):
                do_data = True
                log.info(f"-> Data schedule triggered (>= {DATA_INTERVAL_DAYS} days).")
            else:
                log.info(f"-> Data schedule skipped. Last run: {last_data_time.strftime('%Y-%m-%d')}.")

            if now - last_resume_time >= timedelta(days=RESUME_INTERVAL_DAYS):
                do_resume = True
                log.info(f"-> Resume schedule triggered (>= {RESUME_INTERVAL_DAYS} days).")
            else:
                log.info(f"-> Resume schedule skipped. Last run: {last_resume_time.strftime('%Y-%m-%d')}.")

        if do_data:
            log.info("--- 🟢 STARTING DATA PIPELINE ---")
            # ✅ CHANGED: Using MAX_ITEMS_PER_RUN env-var constant
            found = run_discovery_pipeline(api_key, db, max_items=MAX_ITEMS_PER_RUN)
            if found > 0:
                save_json_file(DATA_FILE, db)
            history["last_data_crawl"] = now.isoformat()
            log.info(f"🟢 DATA PIPELINE COMPLETE. Added {found} new items. Total: {len(db)}")

        if do_resume:
            log.info("--- 🔵 STARTING RESUME PIPELINE ---")
            generate_intelligence_report(api_key, db)
            history["last_resume_gen"] = now.isoformat()
            log.info("🔵 RESUME PIPELINE COMPLETE.")

        save_json_file(HISTORY_FILE, history)
        log.info("✅ All requested tasks completed.")

    except Exception as e:
        log.error(f"Fatal Error during execution: {e}", exc_info=True)

if __name__ == "__main__":
    main()
