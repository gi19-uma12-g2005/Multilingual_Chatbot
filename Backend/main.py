import os

# 🚀 FIX: Disable OneDNN and GPU to prevent startup hangs
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import time
import re
import logging
import signal
import threading
import asyncio
from contextlib import asynccontextmanager
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict, deque
from typing import Optional, Dict, Any, List, Set

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from rasa.core.agent import Agent

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from deep_translator import MyMemoryTranslator, GoogleTranslator
from rapidfuzz import fuzz

# -----------------------------------------------------------
# ✅ CONFIGURATION
# -----------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT_JSON = os.path.join(BASE_DIR, "service_account.json")
SHEET_ID = "14MlIfFyXAJG-bB_iZb0TbeRts5hlIQIlXSgHNHfyd8M"

MODEL_PATHS = {
    "en": "D:/Umang_Coding/AI_chatbot/Backend/models/model_en.tar.gz",
    "hi": "D:/Umang_Coding/AI_chatbot/Backend/models/model_hi.tar.gz",
    "mr": "D:/Umang_Coding/AI_chatbot/Backend/models/model_mr.tar.gz",
    "bn": "D:/Umang_Coding/AI_chatbot/Backend/models/model_bn.tar.gz",
}

FALLBACK_LANG = "en"
SHEET_CACHE_TTL = 600
TRANSLATION_CACHE_SIZE = 4096
TRANSLATION_CONCURRENCY = 4
RAG_MIN_SCORE = 0.70
RATE_LIMIT_WINDOW = 10
RATE_LIMIT_COUNT = 20

# -----------------------------------------------------------
# ✅ LOGGING
# -----------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("chatbot")

# -----------------------------------------------------------
# ✅ GLOBAL CACHES & THREADS
# -----------------------------------------------------------
_sheet_cache: List[Dict[str, Any]] = []
_sheet_last_fetch = 0.0
_sheet_lock = threading.Lock()

_loaded_agents: Dict[str, Agent] = {}
_agents_lock = threading.Lock()

_bg_executor = ThreadPoolExecutor(max_workers=6)
_translation_semaphore = threading.Semaphore(TRANSLATION_CONCURRENCY)
_rate_store: Dict[str, deque] = defaultdict(deque)
_rate_lock = threading.Lock()

# -----------------------------------------------------------
# ✅ GOOGLE SHEETS
# -----------------------------------------------------------
def _sheet_client():
    if not os.path.exists(SERVICE_ACCOUNT_JSON):
        log.warning("⚠ Service account JSON missing: %s", SERVICE_ACCOUNT_JSON)
        return None
    try:
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_JSON, scope)
        return gspread.authorize(creds)
    except Exception as e:
        log.error(f"❌ Google Sheet auth failed: {e}")
        return None


def _normalize(text: Optional[str]) -> str:
    if not text:
        return ""
    text = re.sub(r"[^a-z0-9\u0900-\u097F\s]", " ", text.strip().lower())
    return re.sub(r"\s+", " ", text)


def _token_set(text: str) -> Set[str]:
    return set(_normalize(text).split())


def _fetch_sheet_rows(force_refresh: bool = False):
    global _sheet_cache, _sheet_last_fetch
    now = time.time()
    with _sheet_lock:
        if not force_refresh and _sheet_cache and (now - _sheet_last_fetch) < SHEET_CACHE_TTL:
            return _sheet_cache
        client = _sheet_client()
        if not client:
            return _sheet_cache
        try:
            ws = client.open_by_key(SHEET_ID).sheet1
            rows = ws.get_all_records()
            
            # 🚀 OPTIMIZATION: Pre-calculate tokens
            for row in rows:
                q = str(row.get("question", "")).strip()
                row["_tokens"] = _token_set(q)
                row["_norm_q"] = _normalize(q)

            _sheet_cache = rows
            _sheet_last_fetch = now
            log.info(f"✅ Sheet loaded: {len(rows)} rows")
            return rows
        except Exception as e:
            log.error(f"❌ Sheet fetch failed: {e}")
            return _sheet_cache

# -----------------------------------------------------------
# ✅ RASA MODEL LOADER
# -----------------------------------------------------------
def load_agent_sync(lang: str):
    with _agents_lock:
        if lang in _loaded_agents:
            return _loaded_agents[lang]
        path = MODEL_PATHS.get(lang)
        if not path or not os.path.exists(path):
            raise FileNotFoundError(f"Model not found: {path}")
        agent = Agent.load(path)
        _loaded_agents[lang] = agent
        log.info(f"✅ Loaded Rasa model for {lang}")
        return agent


def _safe_load_agent(lang):
    try:
        load_agent_sync(lang)
    except Exception as e:
        log.warning(f"⚠ Could not preload model {lang}: {e}")


def preload_all_models():
    for lang in MODEL_PATHS.keys():
        _bg_executor.submit(_safe_load_agent, lang)

# -----------------------------------------------------------
# ✅ SMART INTENT-AWARE RAG SEARCH
# -----------------------------------------------------------
def rag_search(user_message: str, lang: str) -> Optional[str]:
    rows = _fetch_sheet_rows()
    if not rows:
        return None

    lang_rows = [r for r in rows if r.get("language", "").strip().lower() == lang] or rows
    user_norm = _normalize(user_message)
    user_tokens = _token_set(user_message)
    user_lower = user_norm.lower()

    # 🔹 Intent synonym map (expandable)
    intent_synonyms = {
        "fee_deadline": ["fees", "last date", "fee bharne", "payment date", "fee due", "fees kab tak"],
        "scholarship_info": ["scholarship", "chhatravriti", "form", "apply", "stipend", "form bharna"],
        "admission_status": ["admission", "enroll", "apply", "college entry", "pravesh"],
        "office_hours": ["timing", "office", "kab khulta", "time", "samay"],
        "greet": ["hello", "hi", "namaste", "hey", "good morning"],
    }

    best_score, best_answer, best_intent = 0.0, None, None

    for row in lang_rows:
        q = str(row.get("question", "")).strip()
        a = str(row.get("answer", "")).strip()
        intent = str(row.get("intent", "")).strip().lower()
        if not q or not a:
            continue

        # 🚀 OPTIMIZATION: Use cached tokens
        norm_q = row.get("_norm_q")
        if norm_q is None:
            norm_q = _normalize(q)
            
        q_tokens = row.get("_tokens")
        if q_tokens is None:
            q_tokens = _token_set(q)

        token_score = len(user_tokens & q_tokens) / max(1, len(user_tokens | q_tokens))
        fuzzy_score = fuzz.token_set_ratio(user_norm, norm_q) / 100.0

        # Intent bonus (based on synonyms or partials)
        intent_bonus = 0.0
        if intent:
            if intent in user_lower:
                intent_bonus += 0.15
            else:
                for syn in intent_synonyms.get(intent, []):
                    if syn in user_lower:
                        intent_bonus += 0.12
                        break
        
        score = (0.4 * token_score) + (0.5 * fuzzy_score) + intent_bonus

        if score > best_score:
            best_score, best_answer, best_intent = score, a, intent

    log.info(f"🧠 Best RAG score={best_score:.2f} intent={best_intent} lang={lang}")

    if best_score >= RAG_MIN_SCORE:
        return best_answer

    # Fallback on intent-only match
    for row in lang_rows:
        intent = str(row.get("intent", "")).strip().lower()
        if any(s in user_lower for s in intent_synonyms.get(intent, [])):
            log.info(f"Intent fallback triggered: {intent}")
            return row.get("answer", "")

    log.warning(f"⚠ No confident RAG match for: '{user_message}' [{lang}]")
    return None

# -----------------------------------------------------------
# ✅ TRANSLATION
# -----------------------------------------------------------
@lru_cache(maxsize=TRANSLATION_CACHE_SIZE)
def _translate_cached(text: str, target_lang: str, preload: bool = False) -> str:
    if not text or target_lang == "en":
        return text
    # 🔹 URL/Email Protection: Mask them before translation
    url_pattern = r"(https?://\S+|www\.\S+|[\w\.-]+@[\w\.-]+)"
    urls = []
    
    def mask_match(match):
        urls.append(match.group(0))
        return f"__URL_{len(urls)-1}__"

    masked_text = re.sub(url_pattern, mask_match, text)

    try:
        out = None
        if preload:
            # MyMemory requires specific language pairs (e.g., en-IN|hi-IN)
            # We map generic codes to specific ones for better support
            lang_map = {
                "hi": "hi-IN",
                "mr": "mr-IN",
                "bn": "bn-IN",
                "en": "en-GB"
            }
            src = lang_map.get("en", "en-GB")
            tgt = lang_map.get(target_lang, target_lang)
            
            mm = MyMemoryTranslator(source=src, target=tgt)
            out = mm.translate(masked_text)
        else:
            g = GoogleTranslator(source="auto", target=target_lang)
            out = g.translate(masked_text)
            
        if out:
            # Restore URLs
            for i, url in enumerate(urls):
                # Handle potential translator formatting quirks (spaces, etc.)
                out = out.replace(f"__URL_{i}__", url)
                out = out.replace(f"__ URL_{i} __", url) # Common Google Translate artifact
                out = out.replace(f"__URL_ {i}__", url)
            return out
            
    except Exception as e:
        log.warning(f"⚠ Translator failed ({'preload' if preload else 'runtime'}) for {target_lang}: {e}")
    return text


def translate_text(text: str, target_lang: str, preload: bool = False) -> str:
    if not text or target_lang == "en":
        return text
    with _translation_semaphore:
        return _translate_cached(text, target_lang, preload)

# -----------------------------------------------------------
# ✅ RATE LIMITER
# -----------------------------------------------------------
def _rate_limit_check(ip: str):
    now = time.time()
    with _rate_lock:
        dq = _rate_store[ip]
        while dq and (now - dq[0]) > RATE_LIMIT_WINDOW:
            dq.popleft()
        if len(dq) >= RATE_LIMIT_COUNT:
            return False
        dq.append(now)
        return True

# -----------------------------------------------------------
# ✅ FASTAPI SETUP
# -----------------------------------------------------------
def preload_workload():
    log.info("🚀 Preloading models and cached translations...")
    _fetch_sheet_rows(force_refresh=True)
    preload_all_models()
    rows = _fetch_sheet_rows()
    if not rows:
        return

    common_intents = {"greet", "fee_deadline", "scholarship_info", "office_hours", "admission_status"}
    unique_answers = {r["answer"].strip() for r in rows if r.get("intent") in common_intents and r.get("answer")}

    for ans in unique_answers:
        for tgt in ("hi", "mr", "bn"):
            _bg_executor.submit(translate_text, ans, tgt, True)
    log.info("✅ Preload completed.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    log.info("🔥 Chatbot server starting...")
    threading.Thread(target=preload_workload, daemon=True).start()
    yield
    # Shutdown
    log.info("🛑 Shutdown signal received.")
    _bg_executor.shutdown(wait=False)
    log.info("✅ Clean shutdown complete.")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    lang: str = "en"

@app.post("/chat")
async def chat(request: ChatRequest, raw_request: Request):
    start = time.time()
    message = request.message.strip()
    lang = request.lang.lower()
    ip = raw_request.client.host if raw_request.client else "unknown"

    if not message:
        raise HTTPException(status_code=400, detail="Message required")
    if not _rate_limit_check(ip):
        raise HTTPException(status_code=429, detail="Rate limited")

    try:
        # 1. RAG Search
        rag_answer = rag_search(message, lang)
        if rag_answer:
            translated = translate_text(rag_answer, lang, preload=False)
            return {
                "reply": translated,
                "source": "RAG",
                "lang": lang,
                "time": round(time.time() - start, 3),
            }

        # 2. Rasa Fallback
        agent = load_agent_sync(lang)
        # FastAPI supports async natively, so we await directly
        responses = await agent.handle_text(message)
        reply = " ".join(r.get("text", "") for r in responses if r.get("text"))
        
        if not reply:
             reply = "I'm sorry, I didn't understand that."

        translated = translate_text(reply, lang, preload=False)
        return {
            "reply": translated,
            "source": "RASA",
            "lang": lang,
            "time": round(time.time() - start, 3),
        }

    except Exception as e:
        log.exception("Chat error")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
