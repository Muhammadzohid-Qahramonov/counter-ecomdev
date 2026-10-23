# O'quv markazi to'lovlari

[Русская версия](README.md)

O'quv markazi uchun to'lovlarni hisobga olish tizimi: o'quvchilar va ularning
oylik to'lov summasi saqlanadi, har bir to'lov yoziladi, tanlangan oy uchun
qarzdorlar ro'yxati (kim, qancha to'lagan, qancha qarz) hisoblanadi.

## Tuzilma

```
backend/    Python API (FastAPI + SQLAlchemy + SQLite)
frontend/   Bitta sahifali veb-interfeys (HTML + CSS + vanilla JS)
```

- **backend/** — barcha ma'lumot va biznes-logika shu yerda: validatsiya,
  bazaga yozish, qarzdorlarni hisoblash. Frontend'siz ham curl/Swagger orqali
  to'liq ishlatish mumkin.
- **frontend/** — build kerak emas, oddiy statik fayllar. Backend'ga `fetch`
  orqali murojaat qiladi; backend manzili `frontend/app.js` boshidagi
  `API_URL` o'zgaruvchisida.

```
backend/
  app/
    main.py            FastAPI ilovasi, CORS, router'larni ulash
    database.py        engine, session, Base, get_db
    models.py          Student, Payment
    schemas.py         Pydantic sxemalari va validatsiya
    errors.py          markazlashgan xato ishlovchi
    timezone.py        Toshkent vaqti (UTC+5) yordamchilari
    routers/           students.py, payments.py, debtors.py
    services/
      debtors.py       qarzdorlarni hisoblash logikasi
  tests/test_debtors.py
  seed.py              boshlang'ich ma'lumot
  requirements.txt
  .env.example
frontend/
  index.html  style.css  app.js
```

## Noldan ishga tushirish

Python 3.11+ kerak. Backend buyruqlari `backend/` papkasi ichida bajariladi.

```bash
cd backend
```

Virtual muhit yaratish:

```bash
python -m venv .venv
```

Uni faollashtirish (Linux/macOS):

```bash
source .venv/bin/activate
```

Uni faollashtirish (Windows):

```bash
.venv\Scripts\activate
```

Kutubxonalarni o'rnatish:

```bash
pip install -r requirements.txt
```

Sozlamalar fayli (Windows'da: `copy .env.example .env`):

```bash
cp .env.example .env
```

Bazani boshlang'ich ma'lumot bilan to'ldirish (bazani tozalab qayta yozadi):

```bash
python seed.py
```

Serverni ishga tushirish:

```bash
uvicorn app.main:app --reload
```

API: http://127.0.0.1:8000, Swagger hujjati: http://127.0.0.1:8000/docs

Frontend'ni ochish — yangi terminalda, repozitoriya ildizidan:

```bash
cd frontend
```

```bash
python -m http.server 5500
```

Brauzerda: http://localhost:5500 (telefonda sinash uchun: `http://<kompyuter-IP>:5500`
va `app.js` dagi `API_URL` ni `http://<kompyuter-IP>:8000` ga o'zgartiring,
uvicorn'ni esa `--host 0.0.0.0` bilan ishga tushiring).
`index.html` ni to'g'ridan-to'g'ri ikki marta bosib ochish ham ishlaydi, chunki CORS `*` ga ruxsat bergan.

Testlar (`backend/` ichida):

```bash
pytest
```

## API

Barcha summalar butun son, so'mda. Sanalar `YYYY-MM-DD`, oy `YYYY-MM`.

| Metod  | Manzil                       | Vazifasi                                 | Muvaffaqiyat |
|--------|------------------------------|------------------------------------------|--------------|
| POST   | `/students`                  | o'quvchi qo'shish                         | 201          |
| GET    | `/students?group=...`        | o'quvchilar ro'yxati (guruh bo'yicha filtr) | 200        |
| GET    | `/students/{id}`             | bitta o'quvchi                            | 200          |
| PATCH  | `/students/{id}`             | o'quvchini qisman o'zgartirish            | 200          |
| DELETE | `/students/{id}`             | o'quvchini (va to'lovlarini) o'chirish    | 204          |
| POST   | `/payments`                  | to'lov qo'shish                           | 201          |
| GET    | `/payments?student_id=X`     | to'lovlar (o'quvchi bo'yicha filtr)       | 200          |
| GET    | `/debtors?month=YYYY-MM`     | shu oy qarzdorlari                        | 200          |

### curl misollari

O'quvchi qo'shish:

```bash
curl -X POST http://127.0.0.1:8000/students -H "Content-Type: application/json" -d '{"name": "Aziz Karimov", "phone": "+998901234567", "group": "Ingliz tili A1", "monthly_fee": 400000}'
```

O'quvchilar ro'yxati, guruh bo'yicha:

```bash
curl "http://127.0.0.1:8000/students?group=Matematika"
```

Bitta o'quvchi:

```bash
curl http://127.0.0.1:8000/students/1
```

O'quvchini o'zgartirish (faqat yuborilgan maydonlar o'zgaradi):

```bash
curl -X PATCH http://127.0.0.1:8000/students/1 -H "Content-Type: application/json" -d '{"monthly_fee": 450000}'
```

O'quvchini o'chirish:

```bash
curl -X DELETE http://127.0.0.1:8000/students/1
```

To'lov qo'shish (`date` berilmasa — bugungi sana, Toshkent vaqti):

```bash
curl -X POST http://127.0.0.1:8000/payments -H "Content-Type: application/json" -d '{"student_id": 2, "amount": 200000, "date": "2026-10-05"}'
```

O'quvchining to'lovlari:

```bash
curl "http://127.0.0.1:8000/payments?student_id=2"
```

Oktyabr qarzdorlari:

```bash
curl "http://127.0.0.1:8000/debtors?month=2026-10"
```

Javob namunasi:

```json
[
  {
    "id": 2,
    "name": "Malika Yusupova",
    "phone": "+998911112233",
    "group": "Ingliz tili A1",
    "monthly_fee": 400000,
    "paid": 200000,
    "debt": 200000
  }
]
```

### Xatolar

Har qanday xato bir xil ko'rinishda qaytadi:

```json
{"error": {"code": "not_found", "message": "ID=999 bo'lgan o'quvchi topilmadi"}}
```

| Status | code               | Qachon                                                                 |
|--------|--------------------|------------------------------------------------------------------------|
| 400    | `invalid_month`    | `month` `YYYY-MM` formatida emas                                       |
| 400    | `empty_update`     | PATCH tanasi bo'sh (`{}`)                                              |
| 404    | `not_found`        | o'quvchi topilmadi (shu jumladan mavjud bo'lmagan `student_id` ga to'lov) yoki noma'lum manzil |
| 405    | `method_not_allowed` | manzil bu HTTP metodni qo'llamaydi                                   |
| 422    | `validation_error` | Pydantic validatsiyasi: summa <= 0, telefon formati, sana ISO emas, majburiy maydon yo'q, noto'g'ri JSON |
| 500    | `internal_error`   | kutilmagan server xatosi (tafsilot logga yoziladi, mijozga ko'rsatilmaydi) |

## Qabul qilingan qarorlar va chegaraviy holatlar

**Qarzdor kim.** Tanlangan oyda to'lagan summasi o'z oylik summasidan kam
bo'lgan o'quvchi. `debt = monthly_fee - paid`.

- **Oy davomida umuman to'lamagan o'quvchi** — qarzdor, `paid = 0`,
  `debt = monthly_fee`. Ro'yxatga LEFT JOIN bilan barcha o'quvchilar olinadi,
  shuning uchun to'lovi yo'qlar tushib qolmaydi.
- **Oylikdan ko'p to'lagan o'quvchi** — qarzdor emas (qarz manfiy bo'lmaydi,
  `max(fee - paid, 0)`). Ortiqcha summa keyingi oyga o'tkazilmaydi: har oy
  mustaqil hisoblanadi. Sabab: balans/avans yuritish alohida hisob jadvali
  talab qiladi, sodda variant esa tushunarli va testlash oson.
- **Bir oyda bir necha marta to'lov** — shu oydagi barcha to'lovlar qo'shiladi
  (`SUM(amount)`), keyin oylik bilan solishtiriladi.
- **`month` noto'g'ri formatda** (`2026-13`, `2026/10`, `abc`) — `400 invalid_month`.
  Bu Pydantic tana validatsiyasi emas, balki query parametrning ma'nosini
  tekshirish, shuning uchun 422 emas, 400.
- **`month` berilmasa** — joriy oy olinadi (Toshkent vaqti bo'yicha). Bu
  frontend'siz tez tekshirish uchun qulay.
- **Vaqt zonasi** — barcha "bugun" va "joriy oy" Asia/Tashkent (UTC+5)
  bo'yicha. To'lov sanasi vaqtsiz kalendar kuni (`DATE`) sifatida saqlanadi va
  Toshkent sanasi deb qabul qilinadi; oy chegarasi `[1-kun, keyingi oyning 1-kuni)`.
  O'zbekistonda yozgi vaqt yo'q, shuning uchun `zoneinfo` + `tzdata` o'rniga
  qat'iy `+5` siljish ishlatildi (bitta kutubxona kam). Frontend ham joriy oy va
  bugungi sanani `Intl` orqali Toshkent vaqtida hisoblaydi — foydalanuvchi
  brauzeri boshqa zonada bo'lsa ham natija bir xil.
- **O'quvchi o'chirilganda** — uning to'lovlari ham o'chadi (`ON DELETE CASCADE`
  + ORM `cascade`). Sabab: egasiz to'lovlar qarzdorlar hisobida va ro'yxatlarda
  ishlatilmaydi, "soft delete" esa har bir so'rovga qo'shimcha filtr talab
  qiladi — topshiriq uchun soddarog'i tanlandi (kamchiligi pastdagi
  "yaxshilash" bo'limida).
- **Yangi qo'shilgan o'quvchi** — o'quvchi qo'shilgan sana (`created_on`)
  avtomatik saqlanadi; u qo'shilishidan oldingi oylar uchun qarzdor
  hisoblanmaydi (aks holda oktyabrda kelgan o'quvchi mart oyi qarzdori bo'lib
  chiqardi). Qo'shilgan oyning o'zida esa to'liq oylik talab qilinadi.
- **Pul** — butun son (so'm), `float` emas: yaxlitlash xatolari bo'lmaydi.
  Summa `0 < x <= 100 000 000`; `"50000"` (matn) yoki `true` qabul qilinmaydi.
- **Sana** — faqat `YYYY-MM-DD` matni (unix timestamp va boshqa formatlar
  rad etiladi), `2026-02-30` kabi mavjud bo'lmagan sana va kelajakdagi sana
  qabul qilinmaydi. Berilmasa — bugun.
- **Telefon** — `+998XXXXXXXXX`. Bo'sh joy, `-` va qavslar olib tashlanadi,
  `998...` boshiga `+` qo'shiladi. Telefon unikal emas: aka-uka bitta ota-ona
  raqamini yozishi mumkin.
- **PATCH** — faqat yuborilgan maydonlar o'zgaradi; `{}` → 400,
  `{"name": null}` → 422, noma'lum maydon → 422.
- **Oylik summa o'zgartirilsa** — o'tgan oylar ham yangi summa bilan
  hisoblanadi (summa tarixi saqlanmaydi; quyida yaxshilash sifatida).
- **Qarzdorlar tartibi** — eng katta qarz tepada, teng bo'lsa ism bo'yicha.
- **Jadvallar** — ilova ishga tushganda `create_all` bilan yaratiladi
  (Alembic o'rniga — sodda).

## Yana bir hafta vaqt bo'lsa nimani yaxshilardim

1. **Alembic migratsiyalari** — hozirgi `create_all` mavjud jadvalga yangi
   ustun qo'shmaydi, ya'ni modelni o'zgartirsam ishlab turgan bazani qo'lda
   o'chirishga to'g'ri keladi.
2. **Oylik summa tarixi (`student_fees` jadvali: summa + amal qilish sanasi)** —
   hozir PATCH bilan summa oshirilsa, o'tgan oylar qarzi ham yangi summa
   bilan qayta hisoblanib, eski hisobotlar o'zgarib ketadi.
3. **O'quvchini arxivlash (soft delete, `archived_at`)** — hozir o'quvchi
   o'chirilsa uning to'lovlari ham yo'qoladi va o'tgan oylar tushumi
   hisobotda kamayib qoladi.
4. **Admin autentifikatsiyasi (login + token)** — hozir API manzilini bilgan
   har kim to'lov qo'shishi yoki o'quvchini o'chirishi mumkin.
5. **To'lovni ikki marta yozilishdan himoya (`Idempotency-Key` sarlavhasi)** —
   sekin internetda so'rov qayta yuborilsa bir xil to'lov ikki marta saqlanadi
   va o'quvchi ortiqcha to'lagan bo'lib ko'rinadi.
