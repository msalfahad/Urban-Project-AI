# Owner rule: stair count and fit check (owner, main chat, 2026-10-21)

The owner gave this rule in his main chat on 2026-10-21 (Arabic original below, unchanged). It becomes a NEW rule
version in the rule library (never an edit of an existing UP-STAIR file). Three points of its relation to existing rules
are open with the owner (section 3); until he answers, the calculator may be built and tested, but its results are not
integrated into V3.0 lines that UP-STAIR-002 / -003 already govern.

## 1. The rule (English summary by the main chat; the Arabic text governs)

Inputs: floor_height (m); max_riser 0.16 (default); tread 0.30 (default; 0.28-0.30 allowed); stair_width (m);
available_length (horizontal length available, m); landing_depth (mid landing depth, m; default = stair_width).

1. risers = ceil(floor_height / max_riser), always rounded up.
2. actual_riser = floor_height / risers: all risers equal; no last step with the remainder.
3. Single straight flight: treads = risers - 1; required_length = treads x tread.
4. Two flights (U) with a mid landing: flight1 = ceil(risers / 2), flight2 = floor(risers / 2); treads per flight =
   its risers - 1 (total treads = risers - 2); required_length = (flight1 - 1) x tread + landing_depth.
5. Fit check: single flight if its required_length <= available_length; otherwise U if its required_length <=
   available_length; otherwise warning "space is not enough, needs at least X m".
6. Warning if tread < 0.28 or actual_riser > 0.16.
7. The landing is never counted as a tread; the last riser lands on the landing or the upper floor.

BOQ outputs: risers, actual_riser, treads, stair type (single / U), required_length, fit result; tread cladding area =
treads x tread x stair_width; riser cladding area = risers x actual_riser x stair_width; tread pieces = treads; riser
pieces = risers; landing area = landing_depth x (2 x stair_width), its own line.

Acceptance tests (landing 1.00 m), checked by hand by the main chat (all consistent):

| H (m) | available L | risers | actual riser | single: treads / length | U: flights / treads / length | result |
|---|---|---|---|---|---|---|
| 3.20 | 6.0 | 20 | 0.160 | 19 / 5.70 | 10+10 / 18 / 3.70 | single |
| 3.20 | 4.0 | 20 | 0.160 | 19 / 5.70 | 10+10 / 18 / 3.70 | U |
| 3.20 | 3.0 | 20 | 0.160 | 19 / 5.70 | 10+10 / 18 / 3.70 | fails: needs at least 3.70 m |
| 3.00 | - | 19 | 0.158 | 18 / 5.40 | 10+9 / 17 / 3.70 | - |
| 3.50 | - | 22 | 0.159 | 21 / 6.30 | 11+11 / 20 / 4.00 | - |
| 4.00 | - | 25 | 0.160 | 24 / 7.20 | 13+12 / 23 / 4.60 | - |

Implementation note (main chat): plain floating-point division misrounds exact cases, e.g. 4.48 / 0.16 =
28.000000000000004 in Python, so ceil gives 29 instead of 28. Compute with decimals or millimetres (integers), or ceil
with a 1e-9 tolerance; add 4.48 m -> 28 risers to the tests. The actual_riser > 0.16 warning needs the same tolerance.

## 2. Original text (owner)

المطلوب: إضافة قاعدة حساب الدرج (Stairs) في محرك الـ BOQ

الفكرة:
لحساب الدرج نحتاج شغلتين: ارتفاع الدور، والطول الأفقي المتوفر للدرج.
1) عدد الدرج: نقسم ارتفاع الدور على ارتفاع الدرجة (القايم). إذا طلع كسر، نقرّب لفوق دايماً عشان ما تزيد الدرجة عن الحد الأقصى.
2) عدد النوايم دايماً أقل بواحد من عدد القوايم في كل قلبة، لأن آخر قايم يطلعك على البسطة أو أرضية الدور اللي فوق، وهذي ما تنحسب نايم.
3) طول القلبة = عدد نوايمها × عمق النايم. بعدها نقارنه بالطول المتوفر ونشوف ينفع ولا لا.

المصطلحات:
- القايم / المراية (Riser): ارتفاع الدرجة. الحد الأقصى 0.16 م
- النايم / الدعسة (Tread): عمق الدرجة. الافتراضي 0.30 م (المسموح 0.28–0.30)
- البسطة (Landing): ما تنحسب نايم

المدخلات:
- floor_height: ارتفاع الدور (م)
- max_riser: الافتراضي 0.16
- tread: الافتراضي 0.30
- stair_width: عرض الدرج (م)
- available_length: الطول الأفقي المتوفر للدرج (م)
- landing_depth: عمق البسطة الوسطية (م)، الافتراضي = stair_width

الحساب:
1) risers = ceil(floor_height / max_riser)   ← التقريب لفوق دايماً
2) actual_riser = floor_height / risers   ← كل الدرجات متساوية، وممنوع درجة أخيرة بالباقي
3) قلبة وحدة (مستقيم):
   treads = risers - 1
   required_length = treads × tread
4) قلبتين (U) وبينهم بسطة:
   flight1 = ceil(risers / 2) ، flight2 = floor(risers / 2)   (مثلاً 10+10 أو 10+9)
   treads لكل قلبة = قوايمها - 1   → مجموع النوايم = risers - 2
   طول القلبة الأطول = (flight1 - 1) × tread
   required_length = طول القلبة الأطول + landing_depth
5) فحص المساحة:
   - إذا required_length للقلبة الوحدة ≤ available_length → قلبة وحدة ✅
   - وإلا إذا required_length للقلبتين ≤ available_length → قلبتين ✅
   - وإلا → ❌ تحذير: "المساحة ما تكفي، تحتاج على الأقل X م"
6) تحذير إذا tread < 0.28 أو actual_riser > 0.16

مثال (ارتفاع الدور 3.20 م):
- 3.20 ÷ 0.16 = 20 قايم ، كل قايم 16 سم
- قلبة وحدة: 19 نايم × 0.30 = 5.70 م
- قلبتين: 10 + 10 ، كل قلبة 9 نوايم = 2.70 م ، + بسطة 1.00 م = 3.70 م

اختبارات لازم تنجح (البسطة 1.00 م):
- H=3.20 ، L=6.0 → 20 قايم ، قلبة وحدة 19 نايم ، الطول 5.70 ✅
- H=3.20 ، L=4.0 → قلبتين 10+10 ، 18 نايم ، الطول 3.70 ✅
- H=3.20 ، L=3.0 → ❌ تحتاج على الأقل 3.70 م
- H=3.00 → ceil(18.75)=19 قايم ، 15.8 سم ، قلبة وحدة 18 نايم = 5.40 ، قلبتين 10+9 → 2.70 + 1.00 = 3.70
- H=3.50 → 22 قايم ، 15.9 سم ، قلبة وحدة 21 نايم = 6.30 ، قلبتين 11+11 → 3.00 + 1.00 = 4.00
- H=4.00 → 25 قايم ، 16.0 سم ، قلبة وحدة 24 نايم = 7.20 ، قلبتين 13+12 → 3.60 + 1.00 = 4.60

مخرجات الـ BOQ:
- عدد القوايم ، القايم الفعلي ، عدد النوايم ، نوع الدرج (قلبة/قلبتين) ، الطول المطلوب ، نتيجة الفحص
- مساحة تكسية النوايم = عدد النوايم × tread × stair_width
- مساحة تكسية القوايم = عدد القوايم × actual_riser × stair_width
- عدد قطع النايم = عدد النوايم ، عدد قطع القايم = عدد القوايم
- مساحة البسطة = landing_depth × (2 × stair_width) ، بند منفصل

## 3. Open with the owner (asked 2026-10-21 by the main chat; agents do not ask again)

- S-1 Precedence with UP-STAIR-002 ("stair geometry comes from the drawing, never from typical values"): when the
  drawing prints the stair, does the drawn count govern and this rule run as a check, or does this rule govern?
- S-2 Riser cladding height with UP-STAIR-003 ("visible marble riser = step rise less the tread build-up"): riser area
  with the full actual_riser, or actual_riser less the tread build-up?
- S-3 floor_height basis: finished floor to finished floor, or structural level to structural level?
