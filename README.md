# Telegram Bo'sh Nikneymlarni Tekshiruvchi Sayt (Django + .txt Kesh + .env)

Ushbu loyiha **Django** va **Django Templates** yordamida qurilgan to'liq veb-sayt bo'lib, Telegramda hali ishlatilmagan **faqat bitta toza so'zli** (ortiqcha raqamlar va ortiqcha harflarsiz) inglizcha hamda anime nikneymlarini (`naruto`, `lucky`, `uchiha`, `halcyon` va h.k.) profilga saqlamasdan (`account.checkUsername` orqali) tekshiradi.

## Asosiy imkoniyatlari

1. **`.txt` faylga saqlash va 0 soniyada keshdan o'qish:**
   - Har bir tekshirilgan nikneym `data/checked_usernames.txt` va (agar bo'sh bo'lsa) `data/available_usernames.txt` fayliga yozib boriladi.
   - Agar biror nikneym avval tekshirilgan bo'lsa (bitta so'z kiritganda ham, `.txt` fayl yuklaganda ham), dastur **4 soniya kutmasdan (0.00 soniyada)** natijani `.txt` fayldan chiqarib beradi!
   - Faqatgina hali tekshirilmagan yangi so'zlar uchun Telegram API ga murojaat qilinadi.
2. **Istalgan paytda `.txt` fayllarni yuklab olish:**
   - Saytning yuqori qismidagi tugmalar orqali istalgan vaqtda `available_usernames.txt` (bo'sh nikneymlar), `checked_usernames.txt` (barcha tekshirilganlar) va `sample_words.txt` fayllarini yuklab olish mumkin.
3. **`.txt` fayl yuklab tekshirish (`txt kiritish`):**
   - Saytga o'zingizning `.txt` faylingizni yuklashingiz yoki matn maydoniga so'zlar ro'yxatini tashlashingiz mumkin.
   - Dastur avtomatik ravishda faqat **bitta toza so'zlarni** (`^[a-zA-Z]{5,32}$` — raqamlarsiz va qo'shimcha belgilarsiz) ajratib oladi va tekshiradi.
4. **`.env` fayl va Veb-brauzer orqali Telegram ulash:**
   - Barcha maxfiy kalitlar `.env` faylida saqlanadi, shuningdek ularni saytning **"Telegram & .env Sozlamalari"** sahifasidan turib tahrirlash va Telegram SMS kodini brauzerning o'zida kiritish mumkin.

## O'rnatish va ishga tushirish

1. ZIP arxivni oching va papka ichiga kiring:
   ```bash
   cd telegram_username_checker_django
   ```
2. Kerakli kutubxonalarni o'rnating:
   ```bash
   pip install -r requirements.txt
   ```
3. `.env` faylini ochib, `my.telegram.org` sahifasidan olingan `TG_API_ID`, `TG_API_HASH` va `TG_PHONE` qiymatlarini yozing (yoki serverni yoqqach, brauzerning o'zidan kiriting).
   *(Maslahat: Agar sizda avvalgi skriptdan qolgan `username_checker_session.session` fayli bo'lsa, uni shu papka ichiga nusxalab qo'ying — shunda qayta SMS kod kiritish shart bo'lmaydi!)*
4. Django serverni ishga tushiring:
   ```bash
   python manage.py runserver
   ```
5. Brauzerda `http://127.0.0.1:8000` manzilini oching.
