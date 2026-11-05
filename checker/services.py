# -*- coding: utf-8 -*-
"""
Telegram Username Checker xizmatlari:
- Faqat bitta toza so'zni (ortiqcha raqam va harflarsiz) ajratib olish
- Tekshirilgan nikneymlarni .txt fayllarda saqlash va 0 soniyada keshdan o'qish
- Telethon orqali Telegram API (`account.checkUsername`) bilan ishlash
- Yuklangan .txt fayl yoki lug'atni fonda (background thread) ketma-ket tekshirish
"""
import asyncio
import os
import re
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from django.conf import settings

try:
    from telethon import TelegramClient
    from telethon.errors import (
        FloodWaitError,
        PhoneCodeExpiredError,
        PhoneCodeInvalidError,
        RPCError,
        SessionPasswordNeededError,
        UsernameInvalidError,
        UsernameOccupiedError,
    )
    from telethon.tl.functions.account import CheckUsernameRequest
    TELETHON_AVAILABLE = True
except ImportError:
    TELETHON_AVAILABLE = False

# ==============================================================================
# FAYL YO'LLARI (.txt ma'lumotlar bazasi)
# ==============================================================================
DATA_DIR: Path = settings.DATA_DIR
CHECKED_TXT_PATH: Path = DATA_DIR / "checked_usernames.txt"
AVAILABLE_TXT_PATH: Path = DATA_DIR / "available_usernames.txt"
TAKEN_TXT_PATH: Path = DATA_DIR / "taken_usernames.txt"
SAMPLE_WORDS_TXT_PATH: Path = DATA_DIR / "sample_words.txt"
ENV_FILE_PATH: Path = settings.BASE_DIR / ".env"

# Faqat 1 ta toza inglizcha so'z qoidasi:
# Uzunligi 5 dan 32 tagacha, faqat lotin harflari (a-z), hech qanday raqam va '_' yo'q!
PURE_SINGLE_WORD_REGEX = re.compile(r"^[a-zA-Z]{5,32}$")

# ==============================================================================
# TAYYOR TOZA INGLIZCHA VA ANIME SO'ZLARI BAZASI (Barchasi 1 ta so'z, raqamsiz)
# ==============================================================================
BUILT_IN_SINGLE_WORDS: list[str] = [
    # Anime & Manga (faqat asl toza so'zlar)
    "naruto", "sasuke", "itachi", "uchiha", "kakashi", "minato", "madara",
    "obito", "jiraiya", "tsunade", "orochimaru", "kurama", "hokage", "shinobi",
    "akatsuki", "sharingan", "rinnegan", "byakugan", "rasengan", "chidori",
    "susanoo", "amaterasu", "tsukuyomi", "kamui", "konoha", "uzumaki", "hyuga",
    "gaara", "temari", "kankuro", "shikamaru", "choji", "inuzuka", "aburame",
    "hidan", "kakuzu", "deidara", "sasori", "kisame", "nagato", "konan",
    "kabuto", "kimimaro", "zabuza", "haku", "hashirama", "tobirama", "hiruzen",
    "kushina", "boruto", "sarada", "mitsuki", "kawaki", "ishiki", "momoshiki",
    "sukuna", "megumi", "nobara", "nanami", "mahito", "geto", "choso",
    "hakari", "yuta", "maki", "inumaki", "tanjiro", "zenitsu", "inosuke",
    "nezuko", "rengoku", "tengen", "muichiro", "mitsuri", "obanai", "gyomei",
    "sanemi", "giyuu", "shinobu", "kanao", "muzan", "kokushibo", "akaza",
    "douma", "kaigaku", "hashira", "nichirin", "luffy", "sanji", "shanks",
    "usopp", "chopper", "robin", "franky", "brook", "jinbe", "yamato",
    "kaido", "katakuri", "doflamingo", "crocodile", "mihawk", "ancock",
    "sabo", "garps", "roger", "rayleigh", "whitebeard", "blackbeard",
    "ichigo", "rukia", "renji", "byakuya", "toshiro", "kenpachi", "zaraki",
    "ulquiorra", "grimmjow", "aizen", "urahara", "yoruichi", "zanpakuto",
    "bankai", "espada", "quincy", "mikasa", "armin", "reiner", "bertholdt",
    "annie", "historia", "ackerman", "yeager", "erwin", "hange", "floch",
    "vegeta", "gohan", "trunks", "piccolo", "frieza", "cell", "broly",
    "beerus", "whis", "saitama", "genos", "tatsumaki", "fubuki", "garou",
    "kaneki", "touka", "juuzou", "arima", "elric", "mustang", "alphonse",
    "thorfinn", "askeladd", "thors", "guts", "griffith", "casca", "kurapika",
    "killua", "gonfreecss", "hisoka", "chrollo", "meruem", "netero",
    "ronin", "samurai", "shogun", "katana", "kitsune", "senpai", "sensei",
    "bushido", "ninjutsu", "genjutsu", "taijutsu",
    # Omad, Status va Chiroyli Inglizcha So'zlar (faqat 1 ta toza so'z)
    "lucky", "fortune", "miracle", "destiny", "karma", "legend", "mythic",
    "royal", "supreme", "divine", "golden", "diamond", "emerald", "sapphire",
    "crimson", "velvet", "shadow", "phantom", "spirit", "ghost", "angel",
    "seraph", "valkyrie", "phoenix", "dragon", "knight", "prince", "monarch",
    "emperor", "winner", "victory", "champion", "infinity", "eternity",
    "eclipse", "aurora", "cosmos", "galaxy", "stellar", "serenity", "harmony",
    "whisper", "enigma", "paradox", "dreamer", "wanderer", "freedom", "valor",
    "wisdom", "genius", "luxury", "velour", "halcyon", "solitude", "oblivion",
    "ethereal", "celestial", "luminous", "radiant", "obsidian", "alabaster",
    "amethyst", "zenith", "horizon", "nebula", "quasar", "pulsar", "vortex",
    "tempest", "blizzard", "avalanche", "glacier", "cascade", "mirage", "oasis",
    "sanctuary", "citadel", "bastion", "fortress", "labyrinth", "odyssey",
    "chronicle", "legacy", "dynasty", "empire", "kingdom", "dominion",
    "sovereign", "paladin", "crusader", "sentinel", "guardian", "warden",
    "ranger", "hunter", "stalker", "assassin", "warlock", "sorcerer",
    "alchemist", "oracle", "prophet", "mystic", "nomad", "pilgrim", "voyager",
    "pioneer", "maverick", "outlaw", "rebel", "renegade", "specter", "wraith",
    "banshee", "chimera", "hydra", "kraken", "leviathan", "behemoth", "goliath",
    "colossus", "titan", "atlas", "apollo", "artemis", "athena", "hermes",
    "poseidon", "chronos", "helios", "selene", "tartarus", "elysium",
    "valhalla", "asgard", "midgard", "ragnarok", "fenrir", "gungnir", "mjolnir",
    "excalibur", "durandal", "muramasa", "masamune", "timeless", "endless",
    "fearless", "flawless", "boundless", "limitless", "priceless", "peerless",
    "matchless", "spotless", "restless", "weightless", "breathless",
    "effortless", "relentless", "dauntless", "tranquil", "peaceful", "graceful",
    "faithful", "hopeful", "joyful", "cheerful", "grateful", "blessed",
    "beloved", "precious", "courage", "kindness", "loyalty", "honesty",
    "humility", "patience", "silence", "sunlight", "moonlight", "starlight",
    "twilight", "midnight", "daybreak", "nightfall", "evergreen", "wildfire",
    "thunder", "lightning", "whirlwind", "hurricane", "cyclone", "monsoon",
    "meadow", "canyon", "summit", "valley", "harbor", "beacon", "compass",
    "anchor", "voyage", "journey", "destiny", "triumph", "glory", "majesty",
]

_FILE_LOCK = threading.Lock()


def ensure_data_files_exist() -> None:
    """Barcha .txt fayllar mavjudligini ta'minlaydi."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for path in (CHECKED_TXT_PATH, AVAILABLE_TXT_PATH, TAKEN_TXT_PATH):
        if not path.exists():
            path.write_text("", encoding="utf-8")
    if not SAMPLE_WORDS_TXT_PATH.exists():
        unique_words = list(dict.fromkeys(BUILT_IN_SINGLE_WORDS))
        SAMPLE_WORDS_TXT_PATH.write_text("\n".join(unique_words) + "\n", encoding="utf-8")


def get_env_config() -> dict[str, Any]:
    """Joriy .env sozlamalarini o'qiydi."""
    env_values: dict[str, str] = {}
    if ENV_FILE_PATH.exists():
        for line in ENV_FILE_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env_values[k.strip()] = v.strip().strip('"').strip("'")

    api_id_str = env_values.get("TG_API_ID") or os.getenv("TG_API_ID", "1234567")
    try:
        api_id = int(api_id_str)
    except ValueError:
        api_id = 1234567

    api_hash = env_values.get("TG_API_HASH") or os.getenv("TG_API_HASH", "sizning_api_hash_kodingiz")
    phone = env_values.get("TG_PHONE") or os.getenv("TG_PHONE", "+998901234567")
    session_name = env_values.get("TG_SESSION_NAME") or os.getenv("TG_SESSION_NAME", "username_checker_session")
    delay_str = env_values.get("CHECK_DELAY_SECONDS") or os.getenv("CHECK_DELAY_SECONDS", "4.0")
    try:
        delay_seconds = max(1.0, float(delay_str))
    except ValueError:
        delay_seconds = 4.0

    is_configured = (
        api_id != 1234567
        and api_hash not in ("", "sizning_api_hash_kodingiz")
        and len(api_hash) >= 16
    )

    session_file = settings.BASE_DIR / f"{session_name}.session"

    return {
        "api_id": api_id,
        "api_hash": api_hash,
        "phone": phone,
        "session_name": session_name,
        "session_path": str(settings.BASE_DIR / session_name),
        "session_file_exists": session_file.exists(),
        "delay_seconds": delay_seconds,
        "is_configured": is_configured,
    }


def update_env_config(api_id: str, api_hash: str, phone: str, delay_seconds: str) -> None:
    """Foydalanuvchi veb-sahifadan kiritgan API sozlamalarini .env faylga saqlaydi."""
    existing_secret = os.getenv("DJANGO_SECRET_KEY", "django-insecure-tg-username-checker-secret-key-2026")
    content = (
        "# ==============================================================================\n"
        "# TELEGRAM API VA DJANGO SOZLAMALARI (.env)\n"
        "# ==============================================================================\n"
        f"TG_API_ID={api_id.strip()}\n"
        f"TG_API_HASH={api_hash.strip()}\n"
        f"TG_PHONE={phone.strip()}\n"
        "TG_SESSION_NAME=username_checker_session\n\n"
        "# Yangi nikneymlarni tekshirish orasidagi kutish vaqti (soniyada)\n"
        f"CHECK_DELAY_SECONDS={delay_seconds.strip()}\n\n"
        "# Django xavfsizlik sozlamalari\n"
        f"DJANGO_SECRET_KEY={existing_secret}\n"
        "DJANGO_DEBUG=True\n"
        "DJANGO_ALLOWED_HOSTS=*\n"
    )
    ENV_FILE_PATH.write_text(content, encoding="utf-8")
    os.environ["TG_API_ID"] = api_id.strip()
    os.environ["TG_API_HASH"] = api_hash.strip()
    os.environ["TG_PHONE"] = phone.strip()
    os.environ["CHECK_DELAY_SECONDS"] = delay_seconds.strip()


# ==============================================================================
# FAQAT BITTA TOZA SO'ZNI AJRATISH (RAQAMSIZ VA QO'SHIMCHA HARFLARSIZ)
# ==============================================================================
def clean_pure_single_word(raw_text: str) -> str | None:
    """
    Matndan faqat bitta toza inglizcha so'zni ajratib oladi.
    Agar ichida raqam, '_' yoki 5 tadan kam / 32 tadan ko'p harf bo'lsa, None qaytaradi.
    Hech qanday ortiqcha harf yoki raqam qo'shmaydi!
    """
    word = raw_text.strip().lstrip("@").lower()
    # Agar "username | STATUS | time" formatida bo'lsa, birinchi qismini olamiz
    if "|" in word:
        word = word.split("|", 1)[0].strip().lstrip("@")
    if " " in word:
        word = word.split()[0].strip().lstrip("@")
    if PURE_SINGLE_WORD_REGEX.match(word):
        return word
    return None


def extract_pure_words_from_text(text: str) -> tuple[list[str], int]:
    """
    .txt fayl yoki ko'p qatorli matndan barcha toza (faqat harflardan iborat bitta so'zli)
    takrorlanmas nikneymlarni ajratib oladi.
    Qaytaradi: (toza_sozlar_royxati, tashlab_ketilgan_yaroqsiz_qatorlar_soni)
    """
    seen: set[str] = set()
    valid_words: list[str] = []
    skipped_count = 0

    # Har bir qator yoki vergul/bo'shliq bilan ajratilgan so'zlarni ko'rib chiqamiz
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        tokens = [t.strip() for t in re.split(r"[,;\s]+", line) if t.strip()]
        for token in tokens:
            cleaned = clean_pure_single_word(token)
            if cleaned:
                if cleaned not in seen:
                    seen.add(cleaned)
                    valid_words.append(cleaned)
            else:
                skipped_count += 1

    return valid_words, skipped_count


# ==============================================================================
# .TXT FAYL KESH TIZIMI (0 SONIYADA TEKSHIRISH UCHUN)
# ==============================================================================
def load_checked_cache() -> dict[str, dict[str, str]]:
    """
    checked_usernames.txt va available_usernames.txt fayllaridan barcha avval
    tekshirilgan nikneymlarni o'qiydi.
    Qaytaradi: { "naruto": {"username": "naruto", "status": "BAND", "timestamp": "..."} }
    """
    ensure_data_files_exist()
    cache: dict[str, dict[str, str]] = {}

    with _FILE_LOCK:
        # 1. available_usernames.txt dan o'qish
        for line in AVAILABLE_TXT_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            word = line.split()[0].lstrip("@").lower()
            if PURE_SINGLE_WORD_REGEX.match(word):
                cache[word] = {
                    "username": word,
                    "status": "BOSH",
                    "timestamp": "Saqlangan (.txt)",
                }

        # 2. taken_usernames.txt dan o'qish
        for line in TAKEN_TXT_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            word = line.split()[0].lstrip("@").lower()
            if PURE_SINGLE_WORD_REGEX.match(word) and word not in cache:
                cache[word] = {
                    "username": word,
                    "status": "BAND",
                    "timestamp": "Saqlangan (.txt)",
                }

        # 3. checked_usernames.txt dan batafsil o'qish (eng asosiy baza)
        for line in CHECKED_TXT_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split("|")]
            word = parts[0].lstrip("@").lower()
            if not word:
                continue
            status = parts[1].upper() if len(parts) > 1 else ("BOSH" if word in cache and cache[word]["status"] == "BOSH" else "BAND")
            timestamp = parts[2] if len(parts) > 2 else "Saqlangan (.txt)"
            cache[word] = {
                "username": word,
                "status": status,
                "timestamp": timestamp,
            }

    return cache


def record_check_result(username: str, status: str) -> dict[str, str]:
    """
    Yangi tekshirilgan nikneym natijasini .txt fayllarga yozadi.
    status: 'BOSH', 'BAND', 'AUKSION', yoki 'YAROQSIZ'
    """
    ensure_data_files_exist()
    word = username.strip().lstrip("@").lower()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status_upper = status.upper()

    with _FILE_LOCK:
        # 1. checked_usernames.txt ni yangilash (takrorlanmas qilib)
        existing_lines = CHECKED_TXT_PATH.read_text(encoding="utf-8").splitlines()
        new_lines = []
        replaced = False
        formatted_entry = f"{word} | {status_upper} | {timestamp}"

        for line in existing_lines:
            if not line.strip():
                continue
            existing_word = line.split("|")[0].strip().lstrip("@").lower()
            if existing_word == word:
                new_lines.append(formatted_entry)
                replaced = True
            else:
                new_lines.append(line)

        if not replaced:
            new_lines.append(formatted_entry)

        CHECKED_TXT_PATH.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

        # 2. Agar BO'SH bo'lsa available_usernames.txt ga yozish
        if status_upper == "BOSH":
            avail_words = {
                l.strip().split()[0].lstrip("@").lower()
                for l in AVAILABLE_TXT_PATH.read_text(encoding="utf-8").splitlines()
                if l.strip()
            }
            if word not in avail_words:
                with AVAILABLE_TXT_PATH.open("a", encoding="utf-8") as f:
                    f.write(f"@{word}\n")
        else:
            taken_words = {
                l.strip().split()[0].lstrip("@").lower()
                for l in TAKEN_TXT_PATH.read_text(encoding="utf-8").splitlines()
                if l.strip()
            }
            if word not in taken_words:
                with TAKEN_TXT_PATH.open("a", encoding="utf-8") as f:
                    f.write(f"@{word}\n")

    return {
        "username": word,
        "status": status_upper,
        "timestamp": timestamp,
    }


def clear_all_txt_caches() -> None:
    """Barcha .txt kesh fayllarini tozalaydi (foydalanuvchi xohlasa)."""
    with _FILE_LOCK:
        CHECKED_TXT_PATH.write_text("", encoding="utf-8")
        AVAILABLE_TXT_PATH.write_text("", encoding="utf-8")
        TAKEN_TXT_PATH.write_text("", encoding="utf-8")


# ==============================================================================
# TELETHON API VA VEB AVTORIZATSIYA YORDAMCHISI
# ==============================================================================
_TELETHON_LOCK = threading.Lock()


def check_telegram_authorization() -> dict[str, Any]:
    """Seans fayli Telegramga ulangan-ulanmaganini tekshiradi."""
    cfg = get_env_config()
    if not TELETHON_AVAILABLE:
        return {"authorized": False, "reason": "Telethon kutubxonasi o'rnatilmagan (pip install telethon)."}
    if not cfg["is_configured"]:
        return {"authorized": False, "reason": ".env faylida TG_API_ID va TG_API_HASH kiritilmagan."}

    async def _check() -> dict[str, Any]:
        client = TelegramClient(cfg["session_path"], cfg["api_id"], cfg["api_hash"])
        try:
            await client.connect()
            is_auth = await client.is_user_authorized()
            user_info = None
            if is_auth:
                me = await client.get_me()
                if me:
                    user_info = f"{me.first_name or ''} (@{me.username or 'no_username'})".strip()
            return {"authorized": is_auth, "user": user_info, "reason": None if is_auth else "Telegram akkauntga kirilmagan."}
        except Exception as exc:
            return {"authorized": False, "reason": str(exc)}
        finally:
            await client.disconnect()

    with _TELETHON_LOCK:
        return asyncio.run(_check())


def send_telegram_login_code(phone: str) -> dict[str, Any]:
    """Veb-interfeys orqali Telegramga SMS/ilova tasdiqlash kodini yuboradi."""
    cfg = get_env_config()
    if not cfg["is_configured"]:
        return {"ok": False, "error": "Avval API_ID va API_HASH sozlamalarini saqlang."}

    async def _send() -> dict[str, Any]:
        client = TelegramClient(cfg["session_path"], cfg["api_id"], cfg["api_hash"])
        try:
            await client.connect()
            sent = await client.send_code_request(phone)
            return {"ok": True, "phone_code_hash": sent.phone_code_hash}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}
        finally:
            await client.disconnect()

    with _TELETHON_LOCK:
        return asyncio.run(_send())


def verify_telegram_login_code(
    phone: str,
    code: str,
    phone_code_hash: str,
    password: str = "",
) -> dict[str, Any]:
    """Veb-interfeysda kiritilgan 5 xonali kod (va 2FA parol) orqali seansni faollashtiradi."""
    cfg = get_env_config()

    async def _verify() -> dict[str, Any]:
        client = TelegramClient(cfg["session_path"], cfg["api_id"], cfg["api_hash"])
        try:
            await client.connect()
            try:
                await client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
            except SessionPasswordNeededError:
                if not password:
                    return {
                        "ok": False,
                        "needs_2fa": True,
                        "error": "Akkauntingizda ikki bosqichli parol (2FA) yoqilgan. Parolni ham kiriting.",
                    }
                await client.sign_in(password=password)
            return {"ok": True}
        except (PhoneCodeInvalidError, PhoneCodeExpiredError) as exc:
            return {"ok": False, "error": f"Kod xato yoki muddati o'tgan: {exc}"}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}
        finally:
            await client.disconnect()

    with _TELETHON_LOCK:
        return asyncio.run(_verify())


def query_telegram_username_api(username: str) -> tuple[str, int]:
    """
    Telegramning rasmiy `account.checkUsername` metodini chaqiradi.
    Nikneymni profilga saqlamaydi, faqat bo'sh-bandligini tekshiradi.
    Qaytaradi: (status, flood_wait_seconds)
    status: 'BOSH', 'BAND', 'AUKSION', 'YAROQSIZ', yoki 'XATO: ...'
    """
    cfg = get_env_config()
    if not TELETHON_AVAILABLE:
        return ("XATO: Telethon o'rnatilmagan", 0)
    if not cfg["is_configured"]:
        return ("XATO: API_ID va API_HASH kiritilmagan", 0)

    async def _query() -> tuple[str, int]:
        client = TelegramClient(cfg["session_path"], cfg["api_id"], cfg["api_hash"])
        try:
            await client.connect()
            if not await client.is_user_authorized():
                return ("XATO: Telegram akkauntga kirilmagan", 0)
            is_free = await client(CheckUsernameRequest(username=username))
            return ("BOSH" if is_free else "BAND", 0)
        except UsernameOccupiedError:
            return ("BAND", 0)
        except UsernameInvalidError:
            return ("YAROQSIZ", 0)
        except FloodWaitError as e:
            return ("FLOOD_WAIT", int(e.seconds) + 5)
        except RPCError as e:
            err_name = e.__class__.__name__.upper()
            if "PURCHASE" in err_name or "FRAGMENT" in str(e).upper():
                return ("AUKSION", 0)
            return ("BAND", 0)
        except Exception as exc:
            return (f"XATO: {exc}", 0)
        finally:
            await client.disconnect()

    with _TELETHON_LOCK:
        return asyncio.run(_query())


def check_single_word_smart(word: str, force_refresh: bool = False) -> dict[str, Any]:
    """
    Bitta toza so'zni tekshiradi:
    1. Agar force_refresh=False bo'lsa va so'z `checked_usernames.txt` da mavjud bo'lsa,
       4 soniya kutmasdan DARHOL (0.00 soniyada) natijani qaytaradi!
    2. Agar yangi so'z bo'lsa, Telegram API orqali tekshirib, .txt faylga saqlaydi.
    """
    cleaned = clean_pure_single_word(word)
    if not cleaned:
        return {
            "ok": False,
            "error": (
                "Faqat bitta toza inglizcha so'z kiriting (5–32 ta harf, "
                "raqamlarsiz va ortiqcha belgilarsiz, masalan: naruto yoki lucky)."
            ),
        }

    start_t = time.perf_counter()
    cache = load_checked_cache()

    if not force_refresh and cleaned in cache:
        cached_item = cache[cleaned]
        elapsed = round(time.perf_counter() - start_t, 4)
        return {
            "ok": True,
            "username": cleaned,
            "status": cached_item["status"],
            "timestamp": cached_item["timestamp"],
            "from_cache": True,
            "elapsed_seconds": elapsed,
        }

    status, wait_sec = query_telegram_username_api(cleaned)
    if status == "FLOOD_WAIT":
        return {
            "ok": False,
            "error": f"Telegram cheklovi (FloodWait): {wait_sec} soniya kutish kerak.",
        }
    if status.startswith("XATO:"):
        return {
            "ok": False,
            "error": status,
        }

    saved = record_check_result(cleaned, status)
    elapsed = round(time.perf_counter() - start_t, 2)
    return {
        "ok": True,
        "username": cleaned,
        "status": saved["status"],
        "timestamp": saved["timestamp"],
        "from_cache": False,
        "elapsed_seconds": elapsed,
    }


# ==============================================================================
# FONDA (.TXT FAYL YOKI LUG'ATNI) KETMA-KET TEKSHIRUVCHI MENEJER
# ==============================================================================
class BatchScanManager:
    """
    Yuklangan .txt fayl yoki ichki lug'atdagi so'zlarni tekshiradi:
    - Avval .txt keshda borlarini 0 soniyada (kutmasdan) ajratib oladi.
    - Faqat yangi (hali tekshirilmagan) so'zlarni 4 soniya oraliq bilan tekshiradi.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.is_running: bool = False
        self.stop_requested: bool = False
        self.source_name: str = ""
        self.total_words: int = 0
        self.processed_words: int = 0
        self.instant_cache_hits: int = 0
        self.api_checked_count: int = 0
        self.available_found_in_run: int = 0
        self.current_word: str = ""
        self.last_message: str = "Tayyor"
        self.recent_results: list[dict[str, Any]] = []

    def get_status(self) -> dict[str, Any]:
        with self._lock:
            percent = (
                int((self.processed_words / self.total_words) * 100)
                if self.total_words > 0
                else 0
            )
            return {
                "is_running": self.is_running,
                "source_name": self.source_name,
                "total_words": self.total_words,
                "processed_words": self.processed_words,
                "instant_cache_hits": self.instant_cache_hits,
                "api_checked_count": self.api_checked_count,
                "available_found_in_run": self.available_found_in_run,
                "current_word": self.current_word,
                "last_message": self.last_message,
                "progress_percent": percent,
                "recent_results": list(self.recent_results[:25]),
            }

    def request_stop(self) -> None:
        with self._lock:
            if self.is_running:
                self.stop_requested = True
                self.last_message = "To'xtatilmoqda..."

    def start_batch(self, words: list[str], source_name: str = "Yuklangan .txt") -> dict[str, Any]:
        with self._lock:
            if self.is_running:
                return {"ok": False, "error": "Hozirda tekshiruv jarayoni ketmoqda. Avval uni to'xtating."}
            self.is_running = True
            self.stop_requested = False
            self.source_name = source_name
            self.total_words = len(words)
            self.processed_words = 0
            self.instant_cache_hits = 0
            self.api_checked_count = 0
            self.available_found_in_run = 0
            self.current_word = ""
            self.last_message = f"{source_name}: tekshiruv boshlandi..."
            self.recent_results = []

        worker = threading.Thread(
            target=self._run_worker,
            args=(words,),
            daemon=True,
        )
        worker.start()
        return {"ok": True}

    def _push_recent(self, item: dict[str, Any]) -> None:
        self.recent_results.insert(0, item)
        if len(self.recent_results) > 40:
            self.recent_results = self.recent_results[:40]

    def _run_worker(self, words: list[str]) -> None:
        try:
            cache = load_checked_cache()
            unchecked_words: list[str] = []

            # 1-QADAM: .txt faylda avvaldan bor so'zlarni 0 soniyada (kutmasdan!) o'tkazamiz
            for word in words:
                if self.stop_requested:
                    break
                if word in cache:
                    cached_entry = cache[word]
                    with self._lock:
                        self.processed_words += 1
                        self.instant_cache_hits += 1
                        if cached_entry["status"] == "BOSH":
                            self.available_found_in_run += 1
                        self._push_recent({
                            "username": word,
                            "status": cached_entry["status"],
                            "from_cache": True,
                            "timestamp": cached_entry["timestamp"],
                        })
                else:
                    unchecked_words.append(word)

            if self.instant_cache_hits > 0 and not unchecked_words:
                with self._lock:
                    self.last_message = (
                        f"Barcha {self.instant_cache_hits} ta so'z avval tekshirilgan ekan — "
                        "0 soniyada .txt keshdan olindi!"
                    )
                return

            # 2-QADAM: Faqat yangi (hali tekshirilmagan) so'zlarni Telegram API orqali tekshiramiz
            cfg = get_env_config()
            delay_seconds = cfg["delay_seconds"]

            for idx, word in enumerate(unchecked_words):
                if self.stop_requested:
                    with self._lock:
                        self.last_message = "Foydalanuvchi tomonidan to'xtatildi."
                    break

                with self._lock:
                    self.current_word = word
                    self.last_message = f"Telegram orqali tekshirilmoqda: @{word}..."

                status, wait_sec = query_telegram_username_api(word)

                if status == "FLOOD_WAIT":
                    with self._lock:
                        self.last_message = f"FloodWait cheklovi: {wait_sec} soniya kutilmoqda..."
                    for _ in range(wait_sec):
                        if self.stop_requested:
                            break
                        time.sleep(1)
                    if self.stop_requested:
                        break
                    status, _ = query_telegram_username_api(word)

                if status.startswith("XATO:"):
                    with self._lock:
                        self.last_message = status
                        self.stop_requested = True
                    break

                saved = record_check_result(word, status)
                with self._lock:
                    self.processed_words += 1
                    self.api_checked_count += 1
                    if saved["status"] == "BOSH":
                        self.available_found_in_run += 1
                    self._push_recent({
                        "username": word,
                        "status": saved["status"],
                        "from_cache": False,
                        "timestamp": saved["timestamp"],
                    })
                    self.last_message = (
                        f"Oxirgi tekshirilgan: @{word} ({saved['status']}). "
                        f"Keshdan (0s): {self.instant_cache_hits} ta | Yangi API: {self.api_checked_count} ta."
                    )

                # Keyingi yangi so'z bo'lsa, FloodWait tushmaslik uchun belgilangan vaqt kutamiz
                if idx < len(unchecked_words) - 1 and not self.stop_requested:
                    steps = max(1, int(delay_seconds * 2))
                    for _ in range(steps):
                        if self.stop_requested:
                            break
                        time.sleep(delay_seconds / steps)

            with self._lock:
                if not self.stop_requested:
                    self.current_word = ""
                    self.last_message = (
                        f"Yakunlandi! Jami: {self.processed_words}/{self.total_words} "
                        f"(Keshdan 0 soniyada: {self.instant_cache_hits} ta, "
                        f"Yangi tekshirildi: {self.api_checked_count} ta)."
                    )
        finally:
            with self._lock:
                self.is_running = False
                self.current_word = ""


BATCH_MANAGER = BatchScanManager()
