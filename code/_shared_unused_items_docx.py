"""
Build a Word doc cataloguing items that appear in BOTH the 2020 and 2023 EIM
surveys with identical or near-identical wording, EXCLUDING items already in
use in the current analysis. Output:
    reports/Shared_Items_2020_2023_Unused.docx

Methodology
-----------
- 2023 source: codebook/EIM23datamap.xlsx (English question text, Q-codes / T-codes).
- 2020 source: data/EIM 2020_20.10.25.sav copy SPSS metadata (Estonian labels,
  K-codes / T-codes). Labels translated to English from the Estonian originals.
- Inclusion criterion: a 2023 item is paired with a 2020 item ONLY if both
  surveys ask the same construct with same/near-same wording, same response
  frame (reference group, time window), and a comparable scale. Items with
  partial wording overlap but substantively different framing are listed in
  the final "Excluded — not directly comparable" section so Brian can see
  they were considered.
- Confidence flag: "(possibly same — verify)" appended where the match is
  plausible but the original-language phrasing differs enough to warrant
  human verification before using cross-year.
- All items already used in the current analysis (per CLAUDE.md) are
  EXCLUDED from this catalogue.

Run from anywhere; uses relative paths only inside the project root.
"""

from pathlib import Path

from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

ROOT = Path(__file__).parent.parent
OUT_PATH = ROOT / "reports" / "Shared_Items_2020_2023_Unused.docx"
OUT_PATH.parent.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Data: catalogue of matched items, grouped by topical area.
# Tuple format: (q23_code, k20_code, english_text, scale, notes)
#   - notes flag confidence; include "(verify)" where wording differs.
# ---------------------------------------------------------------------------

DEMOGRAPHICS = [
    ("T2",  "T2",  "Gender", "Categorical", "Standard demographic; identical wording."),
    ("T3",  "T3",  "Age in full years",  "Continuous (years)", "Identical."),
    ("T4",  "T4",  "Settlement type (urban/rural/...)", "Categorical", "Categories appear consistent."),
    ("T5",  "T5",  "County of residence", "Categorical (15 counties)", "Identical."),
    ("T6",  "T6",  "District of Tallinn (if Tallinn resident)", "Categorical", "Identical."),
    ("T7",  "T7",  "Main language of communication in Estonia", "Categorical (Est / Rus / mixed / other)",
     "Identical wording. Note: used as ethnicity proxy in earlier sessions but replaced by T8/T9. Still useful as IV (communication-language behavior, distinct from self-identified nationality)."),
    ("T10", "T11", "Where were you born? (country)", "Categorical (Estonia / Russia / elsewhere)", "Identical."),
    ("T11", "T12", "When did you come to live in Estonia?", "Categorical year-band / open year", "Identical wording."),
    ("T13", "T14", "Have you lived outside Estonia for more than 10 years during your lifetime?",
     "Yes / No", "Identical."),
    ("T14", "T15", "Number of people in household (including respondent)", "Count 1..10+", "Identical."),
    ("T15_1..T15_4", "(not directly available)", "Children in household by age band (0-6, 7-10, 11-18, none)",
     "Multi-select", "2020 file does not appear to have an exact equivalent (T15 is household size only); consider as 2023-only. (possibly same — verify codebook)"),
    ("T16", "T18", "Household total income last month (band)", "Income band",
     "Bands differ between 2020 and 2023 — direct comparison requires re-banding. (possibly same — verify)"),
    ("T17", "T19", "Subjective household income adequacy / coping",
     "1-4 (live well → very hard to cope)", "Wording identical; same 4-point scale plus DK."),
    ("T18", "T22", "Highest level of education completed", "Categorical 1-7",
     "Categories overlap closely; 2020 has 7 levels, 2023 confirm matching set. (possibly same — verify category alignment)"),
]

BELONGING_IDENTITY = [
    ("Q67_3", "K6X5_4",
     "You feel proud when Estonia is represented at international events by a person of another nationality",
     "1-4 agree-disagree",
     "Same battery as the used items Q67_2/4/5 ↔ K6X5_2/3/4. Verify K6X5 item ordering — 2020 K6X5 has 6 items; only K6X5_1/2/3/4 are in the standard 4-item belonging battery. (possibly same — verify)"),
    ("Q67_6", "K6X5_5 / K6X5_6",
     "You feel proud of Estonia's achievements and opportunities compared to other countries",
     "1-4 agree-disagree",
     "Q67 expanded from 4 items (2020) to 8 items (2023). Q67_6/_7/_8 are 2023 additions — not in 2020. EXCLUDE as 2023-only unless K6X5_5/_6 prove to match (verify Estonian wording)."),
    ("Q64_1", "K6X2_1", "How connected do you feel to your city/municipality/region?",
     "1-4 (very connected → not at all)", "Identical wording, identical scale."),
    ("Q64_2", "K6X2_2", "How connected do you feel to Estonia?",
     "1-4 (very connected → not at all)", "Identical."),
    ("Q64_3", "K6X2_3", "How connected do you feel to Russia?",
     "1-4 (very connected → not at all)", "Identical."),
    ("Q64_4", "K6X2_5", "How connected do you feel to Europe?",
     "1-4 (very connected → not at all)", "K6X2_5 in 2020 = Europe; K6X2_4 = country of origin. Verify order."),
    ("Q64_5", "K6X2_4", "How connected do you feel to (some other / country of origin)?",
     "1-4 (very connected → not at all)",
     "Q64_5 ('some other country') and K6X2_4 ('country of origin') are similar but not identical reference targets. (possibly same — verify)"),
    ("Q610", "K6X8", "To what extent do you see your future tied to Estonia (stay vs leave)?",
     "1-5/6 categorical", "Identical question stem; verify response category alignment."),
    ("Q1115", "K9X12",
     "Attitude if an (Estonian) Russian became Prime Minister of Estonia",
     "1-3/4 categorical", "Wording identical. K9X12 has 4 options including 'nationality irrelevant'; verify 2023 options match."),
]

PERCEIVED_TREATMENT_RIGHTS = [
    ("Q41_1", "K3X2_2", "You are unable to protect your interests",
     "1-4 agree-disagree", "Identical wording (K3X2 has 4 items; Q41 has 3 items, all retained from 2020 battery)."),
    ("Q41_2", "K3X2_3", "You have no opportunity to influence society",
     "1-4 agree-disagree", "Identical."),
    ("Q41_3", "K3X2_4", "You feel that you are often treated intolerantly because of your nationality",
     "1-4 agree-disagree", "Identical wording. NOTE: this is the discrimination item — high analytical potential as outcome or moderator."),
    ("Q65_1", "K6X3_1",
     "The Estonian state protects your rights and provides public services equally to all",
     "1-4 agree-disagree", "Identical."),
    ("Q65_2", "K6X3_4",
     "You do not feel any pressure to give up your national culture and become Estonianized",
     "1-4 agree-disagree", "Identical wording (K6X3_4 in 2020)."),
    ("(in 2023 Q67 expanded battery)", "K6X3_7",
     "Everyone in Estonia has equal rights and opportunities regardless of nationality and/or native language",
     "1-4 agree-disagree", "K6X3_7 exists in 2020 but does not appear in 2023 in this exact form — could be partially captured by Q65/Q67. EXCLUDED — not directly comparable."),
]

INTEGRATION_VIEWS = [
    ("Q61", "K6X7",
     "How successful has the integration of people from other ethnic groups into Estonian society been so far?",
     "1-5 successful → unsuccessful", "Identical wording. Single-item summary measure of perceived integration success."),
    ("Q62_1", "(no direct 2020 equiv)",
     "Importance: General knowledge and use of the Estonian language as a sign of successful integration",
     "1-4 importance",
     "Q62 (signs of successful integration, 12 items) — searched 2020 codebook; no K-section with this stem found. Likely NEW in 2023. EXCLUDED."),
    ("Q69_1", "(no direct 2020 equiv)",
     "Different attitudes toward Soviet legacy is an obstacle to integration",
     "1-4 agree-disagree",
     "Q69 (3 items on Soviet legacy / monuments / Estonian-language education) — appears to be 2023-only. EXCLUDED."),
]

SOCIAL_DISTANCE_OTHER = [
    ("Q57_3 / Q58_3 / Q59_3", "K4X7_3 / K4X8_3 / K4X9_3",
     "Social distance toward Ukrainian refugees / new immigrants (neighbor / work-study / family marriage)",
     "1-4 + DK",
     "2020 reference = 'new immigrants arrived in last 5 years' (uus-sisserändajad); 2023 reference = 'Ukrainian refugees'. Different target groups — direct comparison NOT recommended for the 'Ukrainian' contrast. EXCLUDED from main matched table; listed here for completeness."),
    ("Q510", "(no direct 2020 equiv)",
     "How would you feel if your children became friends with children from other ethnic groups arrived in recent years?",
     "1-4 + DK",
     "Q510 single item; conceptually adjacent to social distance but not present in 2020 K4X-battery. EXCLUDED."),
]

CONTACT_OTHER = [
    ("Q53_1", "K4X3_1",
     "Contact frequency with residents who speak a third language (not Estonian or Russian): at work or school",
     "1-5 frequency (almost daily → not at all)",
     "Identical battery structure (K4X3 in 2020 has the same 6 contexts as Q53 in 2023). Lower = more contact. Same direction as the used Q51/Q52."),
    ("Q53_2", "K4X3_2", "Contact with third-language speakers: with neighbors", "1-5 frequency", "Identical."),
    ("Q53_3", "K4X3_3", "Contact with third-language speakers: online and on social media", "1-5 frequency", "Identical."),
    ("Q53_4", "K4X3_4", "Contact with third-language speakers: leisure/hobbies/cultural events/sports", "1-5 frequency", "Identical."),
    ("Q53_5", "K4X3_5", "Contact with third-language speakers: within family/relatives", "1-5 frequency", "Identical."),
    ("Q53_6", "K4X3_6", "Contact with third-language speakers: among friends/close acquaintances", "1-5 frequency", "Identical."),
    ("Q54", "(no direct 2020 equiv)",
     "How often participated in same activities/events with Russian-speaking people during last year",
     "Frequency", "Appears 2023-only. EXCLUDED."),
    ("Q55", "(no direct 2020 equiv)",
     "How many people of other ethnicities/cultures/native languages live in your residence area",
     "Few → many",
     "Appears 2023-only (residential composition perception). EXCLUDED."),
]

LANGUAGE_USE_PROFICIENCY = [
    ("Q75_1", "K5X5_1", "Russian proficiency: understand spoken Russian", "1-4 level", "Identical."),
    ("Q75_2", "K5X5_2", "Russian proficiency: can you read", "1-4 level", "Identical."),
    ("Q75_3", "K5X5_3", "Russian proficiency: can you communicate", "1-4 level", "Identical."),
    ("Q75_4", "K5X5_4", "Russian proficiency: can you write", "1-4 level", "Identical."),
    ("Q76_1", "K5X6_1", "Estonian proficiency: understand spoken", "1-4 level", "Identical."),
    ("Q76_2", "K5X6_2", "Estonian proficiency: can you read", "1-4 level", "Identical."),
    ("Q76_3", "K5X6_3", "Estonian proficiency: can you communicate", "1-4 level", "Identical."),
    ("Q76_4", "K5X6_4", "Estonian proficiency: can you write", "1-4 level", "Identical."),
    ("Q77_1..Q77_6", "K5X7_1..K5X7_6", "Languages used at work and/or school (multi-select)",
     "Multi-select (Estonian / Russian / English / Other / Not working-studying / DK)", "Identical."),
    ("Q78_1..Q78_6", "K5X8_1..K5X8_6", "Languages used in free time / with friends/neighbors",
     "Multi-select", "Identical."),
    ("Q79_1..Q79_6", "K5X9_1..K5X9_6", "Languages used at home / with family",
     "Multi-select", "Identical."),
]

DISCRIMINATION_TREATMENT = [
    ("Q35", "K3X3",
     "Have you encountered Estonians being preferred over fluent-Estonian-speaking non-Estonians in jobs/promotions/admissions?",
     "Yes / No / DK", "Identical wording (K3X3 in 2020)."),
    ("Q36_1", "K2X9_1",
     "Personally encountered discrimination in: applying for a job (vs other candidates) — last 2 years",
     "Yes/No multi-select",
     "Q36 is a 10-item multi-select; K2X9 is a 13-item multi-select with overlapping options. Items 1-7 align directly. (possibly same — verify K2X9 item ordering)."),
    ("Q36_2", "K2X9_2", "Discrimination in: remuneration for work", "Yes/No", "Identical."),
    ("Q36_3", "K2X9_3", "Discrimination in: promotion / career opportunities", "Yes/No", "Identical."),
    ("Q36_4", "K2X9_4", "Discrimination in: distribution of work tasks", "Yes/No", "Identical."),
    ("Q36_5", "K2X9_5", "Discrimination in: sharing work info / having a say", "Yes/No", "Identical."),
    ("Q36_6", "K2X9_6", "Discrimination in: attitudes of coworkers/managers", "Yes/No", "Identical."),
    ("Q36_7", "K2X9_7", "Discrimination in: recognition of work", "Yes/No", "Identical."),
    ("(2020-only)", "K2X10_1..K2X10_12",
     "Grounds of discrimination experienced (nationality, native language, religion, race, sex, age, disability, ...)",
     "Multi-select",
     "K2X10 exists in 2020 — searched 2023; an equivalent battery does not appear to be in Q-section. (possibly same — verify 2023 codebook)."),
]

SERVICES_SATISFACTION = [
    ("Q42_1", "K3X4_1", "Satisfaction with availability of medical care in city/municipality",
     "1-4 + 'not encountered' + DK", "Identical."),
    ("Q42_2", "K3X4_2", "Satisfaction with public transport", "1-4 + flags", "Identical."),
    ("Q42_3", "K3X4_3", "Satisfaction with hobby groups / hobby education", "1-4 + flags", "Identical."),
    ("Q42_4", "K3X4_4", "Satisfaction with kindergartens / childcare", "1-4 + flags", "Identical."),
    ("Q42_5", "K3X4_5", "Satisfaction with law enforcement / security", "1-4 + flags", "Identical."),
    ("Q42_6", "K3X4_6", "Satisfaction with cultural / entertainment opportunities", "1-4 + flags", "Identical."),
    ("Q42_7", "K3X4_7", "Satisfaction with internet / communications", "1-4 + flags", "Identical."),
    ("Q42_8", "K3X4_8", "Satisfaction with housing-related services (water/electricity/heating/waste)", "1-4 + flags", "Identical."),
    ("Q42_9", "K3X4_9", "Satisfaction with health/sports facilities", "1-4 + flags", "Identical."),
    ("Q42_10", "K3X4_10", "Satisfaction with primary/secondary/vocational education", "1-4 + flags", "Identical."),
    ("Q42_11", "K3X4_11", "Satisfaction with social assistance / care services", "1-4 + flags", "Identical."),
    ("Q42_12", "K3X4_12", "Satisfaction with adult education / retraining", "1-4 + flags", "Identical."),
    ("Q42_13", "K3X4_13", "Satisfaction with official procedures / permits / registrations", "1-4 + flags", "Identical."),
    ("Q42_14", "K3X4_14", "Satisfaction with employment services", "1-4 + flags", "Identical."),
    ("Q42_15", "K3X4_15", "Satisfaction with Estonian-language learning provision", "1-4 + flags", "Identical."),
    ("Q43_1..Q43_4", "K3X5_1..K3X5_4",
     "Reasons for dissatisfaction with services (info not in suitable language; service not provided in suitable language; staff dismissive due to origin/language; unequal treatment due to origin/language)",
     "1-4 importance + DK",
     "Identical 4-item follow-up battery, conditional on dissatisfaction in previous question."),
]

GOVT_PERFORMANCE = [
    ("Q23_1..Q23_10", "(no direct 2020 equiv)",
     "Satisfaction with Estonian government's performance across 10 policy areas",
     "1-4 satisfaction",
     "Q23 (Estonian government performance battery) — no equivalent K-section in 2020 codebook. Likely 2023-only. EXCLUDED."),
    ("Q24_1..Q24_9", "(no direct 2020 equiv)",
     "Preparedness for rapid societal changes (residence, profession, working relations, AI, climate, ...)",
     "1-4 preparedness",
     "Q24 — 2023-only. EXCLUDED."),
    ("Q34", "K2X8",
     "Could you find a suitable job within the next 3 months?",
     "Yes / probably yes / probably no / no / DK",
     "Wording is near-identical. (possibly same — verify category set)."),
]

MEDIA_INFORMATION = [
    ("Q91_1", "K7X1_1", "How well informed are you about: your hometown", "1-4 (very well → very poorly)", "Identical."),
    ("Q91_2", "K7X1_2", "How well informed about: Estonia", "1-4", "Identical."),
    ("Q91_3", "K7X1_3", "How well informed about: Russia", "1-4", "Identical."),
    ("Q91_4", "K7X1_4", "How well informed about: European Union", "1-4", "Identical."),
    ("Q91_5", "K7X1_5", "How well informed about: elsewhere in the world", "1-4", "Identical."),
    ("Q91_6", "K7X1_6", "How well informed about: your country of origin", "1-4", "Identical."),
    ("Q92_1..Q92_23", "K7X2_1..K7X2_21",
     "Importance of various media channels as info sources (ETV/ETV2, ETV+, Aktuaalne Kaamera RU, Russian TV, radio, newspapers, news portals, social media, ...)",
     "1-4 importance + DK",
     "Battery overlaps substantially but Q92 was expanded (23 items in 2023 vs. 21 in 2020). The pre-2022 Russian channels (e.g., 'PBK with subtitles', K7X2_5) are mostly retained in Q92. (possibly same — verify item-by-item before pooling.)"),
    ("Q94_1..Q94_11", "K7X3_1..K7X3_10",
     "Social-media channels used for news (Facebook, Odnoklassniki, VKontakte, Twitter, Instagram/TikTok, Reddit, other)",
     "Multi-select",
     "Q94 modernizes the list (adds YouTube, TikTok, Telegram separately). Subset of items (Facebook, Odnoklassniki, VKontakte, Twitter, English forums e.g., Reddit) is directly comparable. (possibly same — verify)."),
    ("Q95_1", "K7X5_1", "Trust in ETV, ETV2", "1-4 trust + 'do not follow' + DK", "Identical."),
    ("Q95_2", "K7X5_2", "Trust in ETV+", "1-4 trust", "Identical."),
    ("Q95_3", "K7X5_4 (Russia TV channels)",
     "Trust in Russian TV channels",
     "1-4 trust",
     "Wording slightly broader in 2023 ('Russian TV channels' aggregate); 2020 K7X5_3 = PBK specifically and K7X5_4 = Russian TV channels. (possibly same — verify)."),
    ("Q95_4", "K7X5_5", "Trust in Vikerraadio", "1-4 trust", "Identical."),
    ("Q95_5", "K7X5_6", "Trust in Radio 4", "1-4 trust", "Identical."),
    ("Q95_6", "K7X5_8", "Trust in Estonian-language newspapers / news portals", "1-4 trust", "Identical."),
    ("Q95_7", "K7X5_7", "Trust in Russian-language newspapers / news portals in Estonia", "1-4 trust", "Identical."),
    ("Q95_9", "K7X5_9", "Trust in Russian newspapers / news portals (from Russia)", "1-4 trust", "Identical."),
    ("Q95_11", "K7X5_10", "Trust in foreign news channels (BBC, CNN, Euronews, ...)", "1-4 trust", "Identical."),
    ("Q95_12", "K7X5_11", "Trust in social media (Facebook, etc.)", "1-4 trust", "Identical."),
    ("(in 2023 trust set)", "K7X4_1..K7X4_4",
     "Proportion of social-media contacts who are Estonian / other-nationality Estonian residents / Russia residents / other",
     "1-5 proportion + DK",
     "K7X4 exists in 2020; no clear equivalent in 2023. EXCLUDED."),
]

EDUCATION_POLICY = [
    ("Q103", "K8X4_1",
     "How would you generally assess children of different nationalities/native languages studying together in one group/class?",
     "1-4 (very good → very bad) + DK", "Identical."),
    ("Q104_1", "K8X5_1",
     "If children of different nationalities studied together: in terms of learning outcomes and subject knowledge",
     "1-4 + DK",
     "K8X5_1 stem may pair with Q104_1 — but K8X5 has 5 items, Q104 has 7. (possibly same — verify item-by-item)."),
    ("Q104_2", "K8X5_2",
     "Mixed classrooms: for the child's overall development", "1-4 + DK",
     "Identical wording. (possibly same — verify K8X5_2 == Q104_2.)"),
    ("Q104_5", "K8X5_3",
     "Mixed classrooms: from the perspective of preserving Estonian language and culture",
     "1-4 + DK", "Wording effectively identical. (possibly same — verify.)"),
    ("Q104_6", "K8X5_4",
     "Mixed classrooms: from the perspective of preserving language and culture of other nationalities",
     "1-4 + DK", "Identical. (possibly same — verify.)"),
    ("Q105_1..Q105_9", "K8X8_1..K8X8_10",
     "Statements about non-Estonian children learning in Estonian (broadens opportunities; prevents acquisition of subject knowledge; psychological stress; threatens native language; threatens cultural identity; ...)",
     "1-4 agree-disagree",
     "K8X8 has 10 items, Q105 has 9; items 2-7 in K8X8 closely match Q105_1-6. (possibly same — verify item alignment)."),
    ("Q108", "K8X6", "Which language of instruction would you like for your children/grandchildren in kindergarten?",
     "Categorical (Estonian / Russian / English / immersion / ...)",
     "Identical wording. K8X6 7-option list; 2023 may differ — (verify)."),
    ("Q109", "K8X7", "Which language of instruction would you like for your children/grandchildren in primary school?",
     "Categorical", "Identical wording. (verify category list)."),
    ("(2020-only)", "K8X1",
     "When should Estonian-language education (not Estonian-language learning) begin in Estonia?",
     "Categorical (immediately / gradual / never / ...)",
     "K8X1 captures pre-policy preference timing in 2020. 2023 instead asks Q101 ('how do you feel about the 2024 transition decision'). EXCLUDED — different framing."),
    ("(2020-only)", "K8X2",
     "Which language of instruction would you want for upper-secondary / vocational?",
     "Categorical (100% Est / 60-40 / 40-60 / 100% Rus / DK)",
     "K8X2 has no direct 2023 equivalent. EXCLUDED."),
    ("(2020-only)", "K8X3",
     "Preferred method to support native language of Russian-speaking children",
     "Categorical",
     "Q107 in 2023 asks a similar question with different category set (multi-select, 6 options). (possibly same — verify)."),
]

CITIZENSHIP_POLITICAL = [
    ("Q111_1..Q111_4", "K9X1_1..K9X1_4", "What citizenship(s) do you hold? (multi-select)",
     "Multi-select (Estonian / Russian / other / undefined)", "Identical."),
    ("Q112", "K9X2", "How did you acquire Estonian citizenship?",
     "Categorical (by birth / naturalization / special services / DK)", "Identical."),
    ("Q113_1..Q113_6", "K9X3_1..K9X3_7", "Which citizenship would you like to have?",
     "Multi-select", "Identical battery; K9X3 has one extra category ('no opinion'). (possibly same — verify.)"),
    ("Q114_1..Q114_6 (subset)", "K9X4_1..K9X4_5",
     "Reasons that could influence your wish to acquire Estonian citizenship (easier job; self-realization; political participation; sense of belonging; visa-free travel)",
     "1-4 influence + DK",
     "K9X4 has 5 items, Q114 has 6. The first 5 items align directly; Q114_6 ('Russia's reputation decline due to Ukraine war') is 2023-only. (possibly same — verify.)"),
    ("Q115_1..Q115_11 (subset)", "K9X5_1..K9X5_10",
     "Reasons that could influence your decision not to acquire Estonian citizenship",
     "1-4 influence + DK",
     "K9X5 has 10 items, Q115 has 11; most items align directly except Q115_11 (renouncing Russian citizenship). (possibly same — verify.)"),
    ("Q116_1", "K9X6_1", "Did you participate in the most recent Riigikogu (parliament) elections?",
     "Categorical (voted in person / electronically / did not vote / not eligible / DK)",
     "Same wording; reference year differs (2023 elections vs. 2019). Treat as period-equivalent vote-turnout indicator, NOT identical content."),
    ("Q116_2", "K9X6_2", "Did you participate in the previous European Parliament / local elections?",
     "Categorical",
     "2020 K9X6_2 = 2019 European Parliament; 2023 Q116_2 = 2021 local government council. NOT directly comparable — different election. EXCLUDED."),
    ("Q117_1 / Q117_2", "(not found)",
     "Self-placement on Left-Right and other ideological scales",
     "Continuous / Likert",
     "Q117 is the worldview-scale battery. No K-section equivalent found in 2020. EXCLUDED."),
    ("Q118_1..Q118_11", "K9X7_1..K9X7_13", "Which political party is closest to your views/interests?",
     "Single-select (party list + 'none' + DK)",
     "Party list overlaps but K9X7 has 13 options vs. Q118's 11 (parties dissolved or renamed). (possibly same — verify subset)."),
    ("Q119", "K9X8", "Have you participated in voluntary activities in the last 12 months?",
     "Yes / No (and optionally areas)", "Identical."),
    ("(2020-only)", "K9X9",
     "Have you participated in civic organizations (clubs, societies, congregations, ...) in the last 12 months?",
     "Yes / No / DK",
     "Q11 in 2023 asks a similar question with 8 categories. (possibly same — verify framing.)"),
    ("Q1112_1", "K9X10_1", "Trust in: Government", "1-4 trust + DK", "Identical."),
    ("Q1112_2", "K9X10_2", "Trust in: Parliament (Riigikogu)", "1-4 trust + DK", "Identical."),
    ("Q1112_3", "K9X10_3", "Trust in: President", "1-4 trust + DK", "Identical."),
    ("Q1112_4", "K9X10_4", "Trust in: Police", "1-4 trust + DK", "Identical."),
    ("Q1112_5", "K9X10_5", "Trust in: Court system", "1-4 trust + DK", "Identical."),
    ("Q1112_6", "K9X10_6", "Trust in: Defense forces", "1-4 trust + DK", "Identical."),
    ("Q1112_7", "K9X10_7", "Trust in: Local government", "1-4 trust + DK", "Identical."),
    ("Q1112_8", "K9X10_8", "Trust in: Education system", "1-4 trust + DK", "Identical."),
    ("Q1112_9", "K9X10_9", "Trust in: Healthcare system", "1-4 trust + DK", "Identical."),
    ("Q1112_10", "K9X10_10", "Trust in: Civil society", "1-4 trust + DK",
     "Identical. NOTE: very high DK rate among Russians — see CLAUDE.md Institutional Trust DK Problem."),
    ("Q1112_11..Q1112_15", "(no direct 2020 equiv)",
     "Trust in: Political parties, Banks, Church, European Union, NATO",
     "1-4 trust + DK",
     "2023 trust battery expanded from 10 (2020) to 15 items. Items 11-15 are 2023-only. EXCLUDED."),
    ("Q1113_1", "K9X11_1",
     "Recent political activity: taken part in a public meeting to discuss political/social issues",
     "1-3 (never / sometimes / repeatedly) + DK",
     "Identical wording. Scale = 3-point in 2020 — verify 2023 scale matches before pooling."),
    ("Q1113_3", "K9X11_2", "Political activity: protests, demonstrations, pickets", "1-3 frequency + DK", "Identical."),
    ("Q1113_4", "K9X11_3", "Political activity: signed an appeal, protest statement, petition", "1-3 frequency + DK", "Identical."),
    ("Q1113_5", "K9X11_4",
     "Political activity: worn a badge/ribbon/shirt etc. with political message; used political-message sticker",
     "1-3 frequency + DK", "Identical."),
    ("Q1113_6", "K9X11_5",
     "Political activity: approached a politician/official personally with ideas",
     "1-3 frequency + DK", "Identical."),
    ("Q1113_7", "K9X11_6",
     "Political activity: participated in political discussion in media (article/email/comment)",
     "1-3 frequency + DK", "Identical."),
    ("Q1113_8", "K9X11_7",
     "Political activity: joined a political advocacy or protest campaign on Facebook etc.",
     "1-3 frequency + DK", "Identical."),
    ("Q1113_9", "K9X11_8", "Political activity: did NOT participate in elections as a sign of protest",
     "1-3 frequency + DK", "Identical."),
]

HEALTH_WELLBEING = [
    ("(no direct 2023 equiv found)", "K10X1",
     "How would you rate your health overall?",
     "1-5 (very good → very bad) + DK",
     "K10X1 is a single self-rated health item. 2023 codebook does not appear to contain a direct equivalent. EXCLUDED (but flag in case 2023 has it under a different code — verify)."),
    ("(no direct 2023 equiv found)", "K10X2",
     "Extent to which everyday activities have been disturbed in the last 6 months (disability/limitations)",
     "1-? scale", "EXCLUDED — no 2023 equivalent located."),
    ("(no direct 2023 equiv found)", "K10X3_1..K10X3_4",
     "Mental health in the last 4 weeks: nervous; depressed; calm/peaceful; happy",
     "1-5 frequency + DK",
     "Classic MHI-4 / SF-36 subset. EXCLUDED — appears 2020-only, but could be very valuable if a parallel item exists in 2023 under a different code (verify before discarding)."),
    ("(2020-only)", "K6X8 + K6X8X1..X3",
     "Future ties to Estonia: open-text reasons for wanting to leave (categorized)",
     "Open-text categorical", "EXCLUDED."),
]

TOPIC_AREAS_2023_ONLY = [
    ("Q1010", "—", "How do you feel about the establishment and operation of Russian-language private schools?",
     "1-? attitude", "2023-only (post-policy item). EXCLUDED."),
    ("Q1011", "—", "Willingness to contribute (financially/time/expertise) to a Russian-language private school",
     "1-? willingness", "2023-only. EXCLUDED."),
    ("Q1012", "—", "Self-rated skills using digital solutions (web/apps)", "1-? skill", "2023-only. EXCLUDED."),
    ("Q1114_1..Q1114_3", "—",
     "If Estonia were attacked: support armed resistance / willing to participate / willing to contribute non-militarily",
     "1-4 agree-disagree", "Post-Feb-2022 item set; no 2020 equivalent located. EXCLUDED."),
    ("Q1116_*", "—", "Participation in Song & Dance Festival, county festivals, Estonian Republic birthday, ...",
     "1-3 participation",
     "K9X13_*_* items in 2020 use the same 3-point participated/followed/neither scale across 5 events. The events overlap (Song & Dance Festival, Republic birthday, etc.), so this is actually MATCHED. See note below — moved to OTHER section."),
    ("Q1117_1..Q1117_10", "—",
     "Cultural participation frequency (theater, concerts, cinema, library, exhibitions, reading fiction, parties, outdoor events, cultural TV/radio, streaming)",
     "Frequency",
     "No 2020 equivalent located. EXCLUDED."),
    ("Q611_*", "—", "Greatest values of living in Estonia (multi-select)",
     "Multi-select", "No 2020 equivalent located. EXCLUDED."),
    ("Q612_*", "—", "Biggest disadvantages of living in Estonia (multi-select)",
     "Multi-select", "No 2020 equivalent located. EXCLUDED."),
    ("Q710_*", "—", "Why is the Estonian language important to you (instrumental vs identity reasons)",
     "1-4 agree-disagree", "No 2020 equivalent located in K5X10 (which has different framing — reasons people may need to use Estonian). (possibly same — verify K5X10 mapping)."),
    ("Q121..Q123_*", "—",
     "Russia–Ukraine war impact battery (direct life impact; severed contacts with Russia; relationship strain; ...)",
     "1-4 / multi-select",
     "Post-Feb-2022 items. 2020 surveyed before the full-scale invasion — no equivalent. EXCLUDED."),
    ("Q96..Q98", "—",
     "Following Estonian media on the war in Ukraine; satisfaction with coverage; increased English-language media use",
     "Frequency / satisfaction / Yes-No",
     "2023-only. EXCLUDED."),
    ("Q81_*", "—",
     "Connections to Latvia/Lithuania/Finland/Sweden/Nordic countries (lived/worked/studied)",
     "Multi-select", "2023-only. EXCLUDED."),
    ("Q82_*", "—",
     "Frequency of following news on countries of interest (international / Russian / popular-science / social-media channels)",
     "Frequency",
     "2020 K7X-section asks about media use but with different stem ('how important as info source'). EXCLUDED."),
    ("Q31..Q33", "—",
     "Current main activity / occupation / employer (with multiple specifics)",
     "Categorical",
     "2020 K2X1/K2X3 cover similar ground. (possibly same — verify category alignment)."),
]

CULTURE_PARTICIPATION = [
    ("Q1116_1_1", "K9X13_1_1", "Song & Dance Festival: participated myself",
     "Yes/No (3-option: participated / followed in media / neither)", "Identical."),
    ("Q1116_1_2", "K9X13_1_2", "Song & Dance Festival: followed in media", "Yes/No", "Identical."),
    ("Q1116_1_3", "K9X13_1_3", "Song & Dance Festival: neither", "Yes/No", "Identical."),
    ("Q1116_2_1..2_3", "K9X13_2_1..2_3", "County song and dance festivals: participated / followed / neither",
     "3-option", "Identical."),
    ("Q1116_3_1..3_3", "K9X13_3_1..3_3", "Estonian Republic birthday celebrations: participated / followed / neither",
     "3-option", "Identical."),
    ("Q1116_4_1..4_3", "K9X13_4_1..4_3", "Other major cultural events (concerts, folk festivals): participated / followed / neither",
     "3-option", "Identical."),
    ("Q1116_5_1..5_3", "K9X13_5_1..5_3", "Popular sports events (marathons, rallies, ski marathons): participated / followed / neither",
     "3-option", "Identical."),
]

# ---------------------------------------------------------------------------
# Build the Word doc.
# ---------------------------------------------------------------------------

doc = Document()
section = doc.sections[0]
section.left_margin = Cm(2.0)
section.right_margin = Cm(2.0)
section.top_margin = Cm(2.0)
section.bottom_margin = Cm(2.0)

style = doc.styles["Normal"]
style.font.name = "Calibri"
style.font.size = Pt(10)


def add_title(text, size=16):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold = True
    r.font.size = Pt(size)


def add_heading(text, size=13):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run(text)
    r.bold = True
    r.font.size = Pt(size)


def add_subheading(text, size=11):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(text)
    r.bold = True
    r.italic = True
    r.font.size = Pt(size)


def add_para(text, italic=False, size=10):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run(text)
    r.italic = italic
    r.font.size = Pt(size)
    return p


def set_cell_bg(cell, color_hex):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color_hex)
    tc_pr.append(shd)


def add_items_table(rows, header_bg="2C3E50"):
    """rows = list of (q23, k20, text, scale, notes) tuples."""
    table = doc.add_table(rows=1 + len(rows), cols=5)
    table.style = "Light Grid Accent 1"
    table.autofit = False

    # Column widths (rough): 2023 code, 2020 code, English text, Scale, Notes
    widths = [Cm(2.2), Cm(2.2), Cm(7.0), Cm(3.0), Cm(3.0)]
    for i, w in enumerate(widths):
        for cell in table.columns[i].cells:
            cell.width = w

    # Header
    hdr = table.rows[0].cells
    headers = ["2023 code", "2020 code", "English question text", "Scale", "Notes"]
    for i, h in enumerate(headers):
        hdr[i].text = ""
        p = hdr[i].paragraphs[0]
        r = p.add_run(h)
        r.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        r.font.size = Pt(10)
        set_cell_bg(hdr[i], header_bg)

    # Rows
    for ri, row in enumerate(rows, start=1):
        cells = table.rows[ri].cells
        for ci, val in enumerate(row):
            cells[ci].text = ""
            p = cells[ci].paragraphs[0]
            r = p.add_run(str(val))
            r.font.size = Pt(9)
            if ci in (0, 1):  # codes
                r.font.name = "Consolas"
                r.font.size = Pt(9)


# -----------------------------------------------------------------
# Title and intro
# -----------------------------------------------------------------
add_title("Shared 2020–2023 EIM Items — Not Yet Used in Current Analysis")

add_para(
    "This catalogue lists every Estonian Integration Monitor item that appears "
    "in BOTH the 2020 and 2023 waves with identical or near-identical question "
    "wording, and that is NOT already used in the existing thesis analysis. "
    "It is intended as a menu of additional cross-year comparisons Brian could "
    "run.",
)
add_para(
    "Method. 2023 codes and English text are drawn from "
    "codebook/EIM23datamap.xlsx. 2020 codes and labels are drawn from the SPSS "
    "metadata of data/EIM 2020_20.10.25.sav copy and translated from Estonian. "
    "An item pair is included when (a) both surveys ask the same construct, "
    "(b) the question stem and item wording correspond closely, and (c) the "
    "response frame (reference group, time window, response options) is "
    "comparable. Pairs flagged '(possibly same — verify)' are plausible but "
    "require a side-by-side wording check before pooling. Items already in "
    "the analysis (per CLAUDE.md) are EXCLUDED: the eight composites and "
    "their constituent items, the two single-item variables Q66/K6X4 and "
    "Q67_1/K6X5_1, and the demographic / IV columns currently in use.",
)
add_para(
    "Caveats. (1) Some 2023 batteries were expanded relative to 2020 (e.g., "
    "Q67 grew from 4 to 8 items; Q1112 grew from 10 to 15; Q92 grew from 21 "
    "to 23). Only the overlapping subset is comparable. (2) The 2020 codebook "
    "labels are SPSS variable labels in Estonian; English translations here "
    "preserve the substantive content but minor phrasing differences may "
    "exist — flag '(possibly same — verify)' calls these out. (3) Several "
    "items are post-Feb-2022 additions (Q121–Q123, Q96–Q98, the Q1114 defense-"
    "preparedness battery) and have no 2020 equivalent.",
    italic=True,
)

# -----------------------------------------------------------------
# Section: Demographics
# -----------------------------------------------------------------
add_heading("1. Demographics & background")
add_para(
    "Demographic and household-level items. Most are identical across the two "
    "waves. Use these as covariates / IVs / sample-composition checks. T-codes "
    "that ARE currently in use (T8 ethnicity, T12 parents' birthplace, T19 "
    "education language) are excluded.",
)
add_items_table(DEMOGRAPHICS)

# -----------------------------------------------------------------
# Section: Belonging & Identity (non-composite)
# -----------------------------------------------------------------
add_heading("2. Belonging & identity (non-composite single items)")
add_para(
    "Items from the belonging / connectedness batteries that are NOT in the "
    "current 3-item Superordinate Identity composite (Q67_2/Q67_4_inv/Q67_5). "
    "Q64 (connectedness to places) is fully matched K6X2 in 2020.",
)
add_items_table(BELONGING_IDENTITY)

# -----------------------------------------------------------------
# Section: Perceived Treatment & Rights
# -----------------------------------------------------------------
add_heading("3. Perceived treatment, rights, and discrimination experience")
add_para(
    "Items from Q41 (subjective political efficacy / perceived intolerance) "
    "and Q65 (equal protection, cultural pressure). Q41_3 (intolerance "
    "treatment) is particularly notable as a potential outcome or mediator.",
)
add_items_table(PERCEIVED_TREATMENT_RIGHTS)

# -----------------------------------------------------------------
# Section: Integration views
# -----------------------------------------------------------------
add_heading("4. Integration: perceived success and views")
add_items_table(INTEGRATION_VIEWS)

# -----------------------------------------------------------------
# Section: Social Distance — other targets
# -----------------------------------------------------------------
add_heading("5. Social distance — other target groups (Ukrainians / new immigrants)")
add_para(
    "These items belong to the same Q57/Q58/Q59 family already used in the "
    "Primary and General Out-group composites, but they target Ukrainians "
    "(2023) or new immigrants (2020) — not the same group. The 2020-2023 "
    "comparison is therefore NOT clean. Documented here so they aren't "
    "mistakenly added to the existing SD composite.",
)
add_items_table(SOCIAL_DISTANCE_OTHER)

# -----------------------------------------------------------------
# Section: Contact — third-language speakers
# -----------------------------------------------------------------
add_heading("6. Contact — third-language speakers (English / other)")
add_para(
    "Q53 (2023) ↔ K4X3 (2020). Same six-context structure as Q51/Q52 "
    "already in use. Could be added as a third Contact composite measuring "
    "exposure to non-Russian non-Estonian residents.",
)
add_items_table(CONTACT_OTHER)

# -----------------------------------------------------------------
# Section: Language proficiency and use
# -----------------------------------------------------------------
add_heading("7. Language proficiency and use")
add_para(
    "Russian and Estonian self-rated proficiency, and language use across "
    "contexts (work/school, free time, home). Q71 (currently used) covers "
    "general proficiency in 3 languages; the items below add domain-specific "
    "detail (understand/read/communicate/write) plus contextual use.",
)
add_items_table(LANGUAGE_USE_PROFICIENCY)

# -----------------------------------------------------------------
# Section: Discrimination / treatment
# -----------------------------------------------------------------
add_heading("8. Discrimination — experience and grounds")
add_items_table(DISCRIMINATION_TREATMENT)

# -----------------------------------------------------------------
# Section: Service satisfaction
# -----------------------------------------------------------------
add_heading("9. Satisfaction with local services")
add_para(
    "Q42 (15 services) ↔ K3X4 (15 services). Identical battery. Q43 follow-up "
    "(reasons for dissatisfaction, conditional) ↔ K3X5 likewise identical.",
)
add_items_table(SERVICES_SATISFACTION)

# -----------------------------------------------------------------
# Section: Government performance and job market
# -----------------------------------------------------------------
add_heading("10. Government performance and labor market")
add_items_table(GOVT_PERFORMANCE)

# -----------------------------------------------------------------
# Section: Media and information
# -----------------------------------------------------------------
add_heading("11. Media use, sources, and trust")
add_para(
    "Q91 (informedness across regions) ↔ K7X1 — identical. Q92/Q94/Q95 media "
    "batteries overlap with 2020 K7X2/K7X3/K7X5 but with item-list changes "
    "(modernization). The directly comparable subset is large; verify item-"
    "by-item before pooling.",
)
add_items_table(MEDIA_INFORMATION)

# -----------------------------------------------------------------
# Section: Education policy (transition to Estonian-language education)
# -----------------------------------------------------------------
add_heading("12. Education policy — mixed classrooms, language of instruction")
add_para(
    "The 2024 policy transition reshaped some items, but the core battery on "
    "mixed-classroom assessment (Q103/Q104 ↔ K8X4/K8X5) and language of "
    "instruction preference (Q108/Q109 ↔ K8X6/K8X7) is preserved.",
)
add_items_table(EDUCATION_POLICY)

# -----------------------------------------------------------------
# Section: Citizenship and political participation
# -----------------------------------------------------------------
add_heading("13. Citizenship, voting, political participation, institutional trust")
add_para(
    "Strong overlap. Institutional trust battery (Q1112 ↔ K9X10) provides 10 "
    "directly comparable items (the 2023-only items 11-15 are excluded). "
    "Political activity (Q1113 ↔ K9X11) provides 8 directly comparable items "
    "on a 3-point frequency scale.",
)
add_items_table(CITIZENSHIP_POLITICAL)

# -----------------------------------------------------------------
# Section: Cultural participation
# -----------------------------------------------------------------
add_heading("14. Cultural-event participation (Q1116 ↔ K9X13)")
add_para(
    "Same 5 cultural events × 3 response categories in both years.",
)
add_items_table(CULTURE_PARTICIPATION)

# -----------------------------------------------------------------
# Section: Health & wellbeing
# -----------------------------------------------------------------
add_heading("15. Health and mental wellbeing")
add_para(
    "These items appear ONLY in the 2020 codebook based on the scan. They are "
    "listed here in case a 2023 equivalent exists under a different code that "
    "the codebook scan missed; verify by searching the EIM23.csv columns "
    "directly.",
)
add_items_table(HEALTH_WELLBEING)

# -----------------------------------------------------------------
# Section: Excluded — 2023-only / not comparable
# -----------------------------------------------------------------
add_heading("16. Excluded — 2023-only items or substantively different wording")
add_para(
    "These 2023 items were examined and found to have no comparable 2020 "
    "counterpart, or the counterpart asks something materially different. "
    "Listed so Brian knows they were considered.",
)
add_items_table(TOPIC_AREAS_2023_ONLY)

# -----------------------------------------------------------------
# Final notes
# -----------------------------------------------------------------
add_heading("Summary and recommendations")
add_para(
    "(1) The largest blocks of clean, identical-wording cross-year items are: "
    "service satisfaction (Q42 ↔ K3X4, 15 items), institutional trust "
    "(Q1112 ↔ K9X10, 10 items), political activity (Q1113 ↔ K9X11, 8 items), "
    "media trust (Q95 ↔ K7X5, ~10 items), informedness (Q91 ↔ K7X1, 6 items), "
    "third-language contact (Q53 ↔ K4X3, 6 items), language proficiency (Q75/Q76 "
    "↔ K5X5/K5X6, 8 items), and cultural participation (Q1116 ↔ K9X13, 15 items).",
)
add_para(
    "(2) Survey sections where 2020-2023 structure changed enough to limit "
    "comparison: (a) Q67 belonging battery grew from 4 to 8 items — only 3 "
    "are already used; the 5 new items have no 2020 equivalent. (b) Q1112 "
    "institutional trust grew from 10 to 15 items — political parties, banks, "
    "church, EU, NATO are 2023-only. (c) Q92 media-channels list was "
    "modernized (TikTok / Telegram / VKontakte / Meduza / Dožd added). "
    "(d) Education-policy items reframed pre-transition (K8X1, K8X2) vs. "
    "post-transition (Q101).",
)
add_para(
    "(3) Survey sections that are entirely post-Feb-2022 and have NO 2020 "
    "equivalent: Q96–Q98 (Estonian media on Ukraine war), Q121–Q123 (war "
    "personal impact / relationship strain), Q1114 (defense preparedness), "
    "Q1010/Q1011 (Russian-language private schools), Q510 (children "
    "befriending newcomer children).",
)
add_para(
    "(4) For any item flagged '(possibly same — verify)' the recommended "
    "verification step is: read the full Estonian K-label in the SPSS "
    "metadata side-by-side with the English Q-text in EIM23datamap.xlsx, "
    "and confirm response-option counts match. Most flags reflect either "
    "item-ordering changes within a battery or one-side category expansion.",
)

doc.save(OUT_PATH)
print(f"Wrote {OUT_PATH}")
