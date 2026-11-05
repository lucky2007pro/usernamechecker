# -*- coding: utf-8 -*-
"""
Django Views:
- Asosiy sahifa (Dashboard): bitta so'z tekshirish, .txt fayl yuklab tekshirish,
  tayyor toza so'zlar bazasini tekshirish, va natijalarni ko'rish
- .txt fayllarni istalgan payt yuklab olish (available, checked, taken, sample)
- Jonli holat API (/api/status/)
- Telegram veb-avtorizatsiya va .env sozlamalarini tahrirlash
"""
from django.contrib import messages
from django.http import FileResponse, Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .services import (
    AVAILABLE_TXT_PATH,
    BATCH_MANAGER,
    BUILT_IN_SINGLE_WORDS,
    CHECKED_TXT_PATH,
    SAMPLE_WORDS_TXT_PATH,
    TAKEN_TXT_PATH,
    check_single_word_smart,
    check_telegram_authorization,
    clear_all_txt_caches,
    ensure_data_files_exist,
    extract_pure_words_from_text,
    get_env_config,
    load_checked_cache,
    send_telegram_login_code,
    update_env_config,
    verify_telegram_login_code,
)


def index_view(request: HttpRequest) -> HttpResponse:
    """Asosiy boshqaruv paneli (Django Template)."""
    ensure_data_files_exist()
    cache = load_checked_cache()
    env_cfg = get_env_config()
    batch_status = BATCH_MANAGER.get_status()

    # Statistikani hisoblash
    all_checked = list(cache.values())
    all_checked.reverse()  # Eng oxirgi tekshirilganlar yuqorida ko'rinadi
    available_list = [item for item in all_checked if item["status"] == "BOSH"]
    taken_list = [item for item in all_checked if item["status"] != "BOSH"]

    single_result = request.session.pop("single_result", None)

    context = {
        "env_cfg": env_cfg,
        "batch_status": batch_status,
        "total_checked_count": len(all_checked),
        "available_count": len(available_list),
        "taken_count": len(taken_list),
        "available_list": available_list[:100],
        "checked_list": all_checked[:100],
        "built_in_word_count": len(set(BUILT_IN_SINGLE_WORDS)),
        "single_result": single_result,
    }
    return render(request, "checker/index.html", context)


@csrf_exempt
@require_POST
def check_single_view(request: HttpRequest) -> HttpResponse:
    """Bitta toza so'zni tekshirish (agar .txt keshda bo'lsa 0 soniyada!)."""
    word = request.POST.get("username", "").strip()
    force_refresh = request.POST.get("force_refresh") == "on"

    result = check_single_word_smart(word, force_refresh=force_refresh)
    if not result.get("ok"):
        messages.error(request, result.get("error", "Noma'lum xatolik yuz berdi."))
    else:
        request.session["single_result"] = result
        if result["from_cache"]:
            messages.success(
                request,
                f"@{result['username']} — .txt fayl keshidan 0 soniyada olindi! "
                f"Holati: {result['status']} (4 soniya kutilmadi).",
            )
        else:
            messages.info(
                request,
                f"@{result['username']} — Telegram orqali tekshirildi va .txt faylga saqlandi! "
                f"Holati: {result['status']}.",
            )
    return redirect("checker:index")


@csrf_exempt
@require_POST
def upload_txt_view(request: HttpRequest) -> HttpResponse:
    """
    Foydalanuvchi yuklagan .txt faylni (yoki matn maydoniga tashlangan ro'yxatni)
    qabul qilib, ichidan faqat bitta toza so'zlarni ajratib tekshirishga qo'yadi.
    """
    uploaded_file = request.FILES.get("txt_file")
    pasted_text = request.POST.get("pasted_words", "").strip()

    raw_content = ""
    source_label = "Yuklangan .txt fayl"

    if uploaded_file:
        if not uploaded_file.name.lower().endswith(".txt"):
            messages.error(request, "Iltimos, faqat .txt formatidagi fayl yuklang!")
            return redirect("checker:index")
        try:
            raw_content = uploaded_file.read().decode("utf-8", errors="ignore")
            source_label = f"Fayl: {uploaded_file.name}"
        except Exception as exc:
            messages.error(request, f"Faylni o'qishda xatolik: {exc}")
            return redirect("checker:index")
    elif pasted_text:
        raw_content = pasted_text
        source_label = "Kiritilgan so'zlar ro'yxati"
    else:
        messages.warning(request, "Iltimos, .txt fayl tanlang yoki so'zlar ro'yxatini kiriting.")
        return redirect("checker:index")

    pure_words, skipped_count = extract_pure_words_from_text(raw_content)
    if not pure_words:
        messages.error(
            request,
            "Yuklangan ma'lumot ichidan birorta ham toza bitta so'zli nikneym (5–32 ta harf, "
            "raqamlarsiz va qo'shimcha belgilarsiz) topilmadi!",
        )
        return redirect("checker:index")

    res = BATCH_MANAGER.start_batch(pure_words, source_name=source_label)
    if not res.get("ok"):
        messages.error(request, res.get("error", "Jarayonni boshlab bo'lmadi."))
    else:
        skip_msg = f" ({skipped_count} ta raqamli/yaroqsiz so'z filtrlandi)" if skipped_count else ""
        messages.success(
            request,
            f"{source_label} qabul qilindi: {len(pure_words)} ta toza bitta so'zli nikneym "
            f"tekshiruvga qo'yildi{skip_msg}. Avval .txt faylga tushganlari 0 soniyada o'tadi!",
        )
    return redirect("checker:index")


@csrf_exempt
@require_POST
def start_builtin_scan_view(request: HttpRequest) -> HttpResponse:
    """Dastur ichidagi tayyor toza inglizcha va anime so'zlar lug'atini tekshirish."""
    unique_words = list(dict.fromkeys(w.lower() for w in BUILT_IN_SINGLE_WORDS if len(w) >= 5))
    res = BATCH_MANAGER.start_batch(unique_words, source_name="Ichki Anime & Lucky toza so'zlar lug'ati")
    if not res.get("ok"):
        messages.error(request, res.get("error", "Jarayonni boshlab bo'lmadi."))
    else:
        messages.success(
            request,
            f"Ichki lug'atdagi {len(unique_words)} ta toza (raqamsiz, bitta so'zli) nikneym "
            "tekshiruvi boshlandi! Avval tekshirilganlari 0 soniyada keshdan olinadi.",
        )
    return redirect("checker:index")


@csrf_exempt
@require_POST
def stop_scan_view(request: HttpRequest) -> HttpResponse:
    """Fonda ishlayotgan tekshiruvni to'xtatish."""
    BATCH_MANAGER.request_stop()
    messages.warning(request, "Tekshiruv jarayoni to'xtatildi. Barcha natijalar .txt faylga saqlangan.")
    return redirect("checker:index")


@csrf_exempt
@require_POST
def clear_cache_view(request: HttpRequest) -> HttpResponse:
    """Barcha .txt kesh fayllarini tozalash."""
    if BATCH_MANAGER.is_running:
        messages.error(request, "Avval joriy tekshiruv jarayonini to'xtating!")
        return redirect("checker:index")
    clear_all_txt_caches()
    messages.info(request, "Barcha .txt fayllar tozalandi.")
    return redirect("checker:index")


@require_GET
def download_txt_view(request: HttpRequest, file_kind: str) -> FileResponse:
    """
    Foydalanuvchi xohlagan paytda .txt faylni yuklab olishi uchun endpoint:
    - available -> available_usernames.txt
    - checked   -> checked_usernames.txt
    - taken     -> taken_usernames.txt
    - sample    -> sample_words.txt
    """
    ensure_data_files_exist()
    mapping = {
        "available": (AVAILABLE_TXT_PATH, "available_usernames.txt"),
        "checked": (CHECKED_TXT_PATH, "checked_usernames.txt"),
        "taken": (TAKEN_TXT_PATH, "taken_usernames.txt"),
        "sample": (SAMPLE_WORDS_TXT_PATH, "sample_words.txt"),
    }
    if file_kind not in mapping:
        raise Http404("Bunday fayl turi mavjud emas.")

    file_path, download_name = mapping[file_kind]
    return FileResponse(
        file_path.open("rb"),
        as_attachment=True,
        filename=download_name,
        content_type="text/plain; charset=utf-8",
    )


@require_GET
def api_status_view(request: HttpRequest) -> JsonResponse:
    """Django shabloni jonli ravishda progress va yangi topilgan nikneymlarni yangilashi uchun JSON API."""
    cache = load_checked_cache()
    all_checked = list(cache.values())
    all_checked.reverse()
    available_list = [item for item in all_checked if item["status"] == "BOSH"]

    status_data = BATCH_MANAGER.get_status()
    status_data["total_checked_in_txt"] = len(all_checked)
    status_data["total_available_in_txt"] = len(available_list)
    status_data["total_taken_in_txt"] = len(all_checked) - len(available_list)
    status_data["latest_available"] = available_list[:30]
    return JsonResponse(status_data)


@csrf_exempt
def telegram_auth_view(request: HttpRequest) -> HttpResponse:
    """
    .env sozlamalarini kiritish va Telegram akkauntga veb-brauzerning o'zidan
    kod orqali ulanish sahifasi.
    """
    env_cfg = get_env_config()
    auth_state = check_telegram_authorization() if env_cfg["is_configured"] else {
        "authorized": False,
        "reason": ".env faylida API_ID va API_HASH hali sozlanmagan.",
    }

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "save_env":
            api_id = request.POST.get("api_id", "").strip()
            api_hash = request.POST.get("api_hash", "").strip()
            phone = request.POST.get("phone", "").strip()
            delay_seconds = request.POST.get("delay_seconds", "4.0").strip()
            update_env_config(api_id, api_hash, phone, delay_seconds)
            messages.success(request, ".env fayli muvaffaqiyatli yangilandi!")
            return redirect("checker:telegram_auth")

        if action == "send_code":
            phone = request.POST.get("phone", env_cfg["phone"]).strip()
            res = send_telegram_login_code(phone)
            if res.get("ok"):
                request.session["tg_login_phone"] = phone
                request.session["tg_phone_code_hash"] = res["phone_code_hash"]
                messages.success(
                    request,
                    f"{phone} raqamiga Telegram orqali tasdiqlash kodi yuborildi! Uni quyidagi maydonga kiriting.",
                )
            else:
                messages.error(request, f"Kod yuborishda xatolik: {res.get('error')}")
            return redirect("checker:telegram_auth")

        if action == "verify_code":
            phone = request.session.get("tg_login_phone") or request.POST.get("phone", env_cfg["phone"]).strip()
            code = request.POST.get("code", "").strip()
            password = request.POST.get("password", "").strip()
            phone_code_hash = request.session.get("tg_phone_code_hash", "")
            if not phone_code_hash:
                messages.error(request, "Avval 'Tasdiqlash kodini yuborish' tugmasini bosing.")
                return redirect("checker:telegram_auth")

            res = verify_telegram_login_code(phone, code, phone_code_hash, password=password)
            if res.get("ok"):
                request.session.pop("tg_phone_code_hash", None)
                messages.success(request, "Telegram akkauntingiz muvaffaqiyatli ulandi! Endi nikneymlarni tekshirishingiz mumkin.")
                return redirect("checker:index")
            else:
                messages.error(request, res.get("error", "Tasdiqlashda xatolik."))
                return redirect("checker:telegram_auth")

    context = {
        "env_cfg": get_env_config(),
        "auth_state": auth_state,
        "pending_phone": request.session.get("tg_login_phone", env_cfg["phone"]),
        "code_sent": bool(request.session.get("tg_phone_code_hash")),
    }
    return render(request, "checker/login_tg.html", context)
