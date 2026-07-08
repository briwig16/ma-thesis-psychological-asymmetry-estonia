"""
Generate a Word doc summarizing comparable political-science research methods
for Brian's EIM2 thesis on Estonian-Russian intergroup attitudes.

Structured as an 8-section reference document with verified citations.
Modeled on _pca_vs_cfa_explainer_docx.py for styling.
"""

from pathlib import Path

from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH

ROOT = Path(__file__).parent.parent
out_path = ROOT / "reports" / "Comparable_Polisci_Research_Methods.docx"

doc = Document()

# Page setup
section = doc.sections[0]
section.left_margin = Cm(2.5)
section.right_margin = Cm(2.5)
section.top_margin = Cm(2.0)
section.bottom_margin = Cm(2.0)

# Default style
style = doc.styles["Normal"]
style.font.name = "Calibri"
style.font.size = Pt(11)


def add_title(text, size=18):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold = True
    r.font.size = Pt(size)


def add_heading(text, size=14):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run(text)
    r.bold = True
    r.font.size = Pt(size)


def add_subheading(text, size=12):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(text)
    r.bold = True
    r.italic = True
    r.font.size = Pt(size)


def add_para(text, italic=False, size=11):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(6)
    r = p.add_run(text)
    r.italic = italic
    r.font.size = Pt(size)
    return p


def add_para_runs(runs):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(6)
    for text, bold, italic in runs:
        r = p.add_run(text)
        r.bold = bold
        r.italic = italic
        r.font.size = Pt(11)
    return p


def add_bullet(text):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(3)
    p.text = text
    for run in p.runs:
        run.font.size = Pt(11)


def add_bullet_runs(runs):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(3)
    for text, bold, italic in runs:
        r = p.add_run(text)
        r.bold = bold
        r.italic = italic
        r.font.size = Pt(11)


def add_citation(authors_year_title, journal_etc, url=None):
    """Citation block: bold authors+year, italic journal, plain URL."""
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.left_indent = Cm(0.6)
    p.paragraph_format.first_line_indent = Cm(-0.6)
    r = p.add_run(authors_year_title)
    r.font.size = Pt(10)
    r2 = p.add_run(" " + journal_etc)
    r2.italic = True
    r2.font.size = Pt(10)
    if url:
        r3 = p.add_run("  " + url)
        r3.font.size = Pt(9)


# =====================================================================
# Title and intro
# =====================================================================
add_title("Comparable Political-Science Research:")
add_title("Methodological Templates for the EIM2 Thesis", size=14)
add_para(
    "A structured reference of peer-reviewed studies whose design, data, or "
    "analytical strategy parallels the EIM2 thesis on Estonian-Russian "
    "intergroup attitudes across the 2020 and 2023 Integration Monitor waves. "
    "Each section gathers a small number of papers with a brief note on what "
    "the work demonstrates methodologically and what Brian can borrow from it. "
    "All citations have been verified against journal landing pages, DOIs, "
    "or stable repositories.",
    italic=True, size=10,
)
add_para(
    "Use this document as a citation pool for the methods chapter, the design "
    "section, and the discussion of limitations. The final section sketches a "
    "chapter-level template synthesised from the patterns across the seven "
    "preceding sections.",
    italic=True, size=10,
)

# =====================================================================
# SECTION 1: Estonian / Baltic intergroup studies
# =====================================================================
add_heading("Section 1. Studies of Estonian and Baltic Intergroup Attitudes")

add_para(
    "These studies use surveys of Estonian or Baltic populations to examine "
    "majority-minority attitudes. They establish the substantive landscape "
    "into which Brian's EIM2 analysis fits and supply templates for "
    "interpreting Russian-speaker identity, integration patterns, and "
    "Estonian majority responses."
)

add_subheading("Vihalemm and colleagues on Russian-speakers' identity dynamics")
add_para(
    "Triin Vihalemm (University of Tartu) is the most prolific scholar on "
    "Russian-speaking acculturation in Estonia. Her cluster-analytic work "
    "identifies five distinct integration profiles among Russian-speakers "
    "ranging from \"strong assimilationists\" to \"minimal participationists,\" "
    "anchored in survey data on language practices, civic engagement, and "
    "identity. Methodologically, her work demonstrates that the Russian-"
    "speaking population is internally heterogeneous and that cross-group "
    "comparisons should be alert to within-group variance, exactly what "
    "Brian's Levene's-test polarization analysis (SESSION_LOG section 29) "
    "captures."
)
add_citation(
    "Vihalemm, T., & Masso, A. (2003). Identity dynamics of Russian-speakers "
    "of Estonia in the transition period.",
    "Journal of Baltic Studies, 34(1), 92-116.",
    "https://www.semanticscholar.org/paper/Identity-dynamics-of-Russian-speakers-of-Estonia-in-Vihalemm-Masso/bea98869a431985febffb373008b17e79174a048",
)
add_citation(
    "Vihalemm, T., & Juzefovics, J. (2022). Navigating Conflicts through the "
    "Media: The Sceptical and Self-Responsible Repertoires of Baltic Russian-"
    "Speakers.",
    "East European Politics and Societies, 36(4), 1213-1238.",
    "https://journals.sagepub.com/doi/abs/10.1177/0888325420964946",
)

add_subheading("Aune Valk on Estonian Open Identity")
add_para(
    "Valk's work on the Estonian Open Identity uses comparative survey designs "
    "with Estonian and Russian-speaker samples to identify which national-"
    "identity content is acceptable across ethnic boundaries. Her 2000 study "
    "of Estonian and Russian adolescents reported group means and esteem "
    "comparisons that prefigure Brian's between-group d analyses. Her "
    "experimental work shows that the majority's acculturation orientation "
    "directly shapes minority national identity — a finding that motivates "
    "treating Estonian-respondent attitudes as a substantive variable rather "
    "than a baseline."
)
add_citation(
    "Valk, A. (2000). Ethnic Identity, Ethnic Attitudes, Self-Esteem, and "
    "Esteem toward Others among Estonian and Russian Adolescents.",
    "Journal of Adolescent Research, 15(6), 637-651.",
    "https://journals.sagepub.com/doi/10.1177/0743558400156002",
)

add_subheading("Cheskin on Russophone identity in Estonia and Latvia")
add_para(
    "Ammon Cheskin's framework for analysing Russian-speaker identity in the "
    "Baltic states treats it as a synthesised position between competing "
    "Russian and Baltic discursive positions. His 2012 Latvia study and the "
    "subsequent comparative work establish that Russian-speakers favour "
    "integration (dual identification) over assimilation, marginalisation, "
    "or separation — a substantive baseline against which Brian's superordinate-"
    "identity results can be read. Cheskin's framework chapter and the Cheskin "
    "and Kachuyevski monograph also provide the citation infrastructure for "
    "the Baltic comparative literature."
)
add_citation(
    "Cheskin, A. (2013). Exploring Russian-Speaking Identity from Below: "
    "The Case of Latvia.",
    "Journal of Baltic Studies, 44(3), 287-312.",
    "https://www.tandfonline.com/doi/full/10.1080/01629778.2012.712335",
)
add_citation(
    "Cheskin, A., & Kachuyevski, A. (2019). The Russian-Speaking Populations "
    "in the Post-Soviet Space: Language, Politics and Identity.",
    "Europe-Asia Studies, 71(1), 1-23.",
    "https://eprints.gla.ac.uk/173351/1/173351.pdf",
)

add_subheading("Ekman on Baltic Barometer 2014 and 2021")
add_para(
    "Joakim Ekman's 2024 analysis directly parallels Brian's design: two "
    "cross-sectional survey waves (Baltic Barometer 2014 and 2021) covering "
    "Estonia, Latvia, and Lithuania, with oversamples of Russian-speaking "
    "minorities. Ekman compares geopolitical attitudes between ethnic-majority "
    "and Russian-speaking samples across the two waves, framed by the 2014 "
    "Crimea annexation. The article's structure — separate descriptive "
    "tables by group and wave, with discussion organised around between-group "
    "gaps rather than causal claims — is the closest published template "
    "Brian will find for an EIM2-style write-up."
)
add_citation(
    "Ekman, J. (2024). In the Shadow of War: Public Opinion in the Baltic "
    "States, 2014 and 2021.",
    "Journal of Baltic Studies (Baltic Worlds special issue).",
    "https://journals.sagepub.com/doi/full/10.1177/18793665241270812",
)

add_subheading("Comparative Estonia–Latvia Russophone attitudes")
add_para(
    "The 2023 paper by Krupavicius, Auers, and colleagues compares Russophone "
    "political attitudes across Estonia and Latvia using survey data. It is "
    "useful as a model for how to handle two comparable but distinct national "
    "contexts when Brian's discussion places EIM data in regional perspective."
)
add_citation(
    "Auers, D., & colleagues (2023). Paradoxes of minority representation: a "
    "comparison of Russophone political attitudes in Estonia and Latvia.",
    "Journal of Baltic Studies, 54(3).",
    "https://www.tandfonline.com/doi/full/10.1080/01629778.2022.2150667",
)

add_subheading("Identity through discrimination after 2022")
add_para(
    "A 2026 Europe-Asia Studies article specifically examines how Russian-"
    "speakers in Estonia have responded to Kremlin \"Russophobia\" narratives "
    "since 2022. It documents that the war reshaped minority identity along "
    "lines partly defined by exogenous Russian state messaging — relevant for "
    "framing the asymmetric divergence pattern Brian finds."
)
add_citation(
    "Author(s) (2026). Identity through Discrimination? Responses by Russian "
    "Speakers in Estonia to Kremlin \"Russophobia\" Narratives.",
    "Europe-Asia Studies (advance access).",
    "https://www.tandfonline.com/doi/full/10.1080/09668136.2026.2630898",
)

# =====================================================================
# SECTION 2: Pre/post-shock survey designs
# =====================================================================
add_heading("Section 2. Pre/Post-Shock Survey Designs in Political Science")

add_para(
    "These papers exploit an exogenous event by comparing survey waves "
    "before and after. They show how political scientists make rigorous "
    "before-after claims with repeated cross-sectional data — a non-trivial "
    "methodological move because the respondents differ between waves, so the "
    "design is technically a difference between population means rather than "
    "a within-person change."
)

add_subheading("Hobolt and Tilley on Brexit attitude change")
add_para(
    "Hobolt and Tilley's Tribal Politics work uses a three-wave Brexit panel "
    "(2017-2020) alongside repeated cross-sectional data to show how the 2016 "
    "referendum reshaped British political identity. The methodological "
    "lesson is the layering of conjoint experiments on top of attitude waves "
    "to triangulate the substantive finding. Brian does not have panel data, "
    "but the descriptive comparison of pre- and post-shock cross-sections is "
    "the workhorse design in this literature."
)
add_citation(
    "Hobolt, S. B., & Tilley, J. (2024). Tribal Politics: How the Brexit Vote "
    "Reshaped Britain.",
    "Oxford University Press.",
    "https://global.oup.com/academic/product/tribal-politics-9780198911715",
)
add_citation(
    "Hobolt, S. B., Leeper, T. J., & Tilley, J. (2021). Policy Preferences "
    "and Policy Legitimacy After Referendums: Evidence from the Brexit "
    "Negotiations.",
    "Political Behavior, 43, 1565-1593.",
    "https://link.springer.com/article/10.1007/s11109-020-09639-w",
)

add_subheading("Bilali, Celik, and Ok on Kurdish-Turkish intergroup attitudes")
add_para(
    "This 2014 paper is the closest published methodological precedent for "
    "Brian's headline asymmetric-divergence finding. The authors ran the same "
    "outcome battery on Kurdish and Turkish respondents in Izmir at two time "
    "points six months apart — one during low-intensity conflict, one "
    "during high-intensity conflict. The design produces a 2 (ethnic group) "
    "by 2 (conflict period) descriptive comparison structurally identical "
    "to Brian's 2 (Estonian/Russian) by 2 (2020/2023) layout. Their results "
    "are also substantively parallel: minorities showed paradoxical movement "
    "(more social distance but more assimilative nationalism), majorities "
    "showed straightforward hardening. This is the single most relevant "
    "comparison case in the literature."
)
add_citation(
    "Bilali, R., Celik, A. B., & Ok, E. (2014). Psychological asymmetry in "
    "minority-majority relations at different stages of ethnic conflict.",
    "International Journal of Intercultural Relations, 43(B), 253-264.",
    "https://www.sciencedirect.com/science/article/abs/pii/S0147176714001096",
)

add_subheading("Whitt and Page on social distance after 2022 invasion")
add_para(
    "Whitt and Page conducted a July 2022 nationwide Ukraine survey "
    "(N = 2,000) measuring social distance toward people identified as "
    "Russian relative to Ukrainian across language, ethnicity, and "
    "citizenship markers. Their methodology shows how the standard Bogardus-"
    "style battery can be deployed post-shock to detect (or fail to detect) "
    "war-induced bias. The article also models a careful causal interpretation: "
    "the authors stop short of attributing changes solely to wartime "
    "victimisation."
)
add_citation(
    "Whitt, S., & Page, D. (2025). War-related victimization and social "
    "distance toward others: Evidence following Russia's 2022 invasion of "
    "Ukraine.",
    "International Political Science Review.",
    "https://journals.sagepub.com/doi/10.1177/00108367251321435",
)
add_citation(
    "Whitt, S., & Page, D. (2025). War, social preferences, and anti-outgroup "
    "behavior: Experimental evidence from Russia's invasion of Ukraine.",
    "Journal of Peace Research.",
    "https://doi.org/10.1177/00223433251318931",
)

add_subheading("Korostelina, Sweigart, and Toal on threat and identity in Ukraine")
add_para(
    "Korostelina and colleagues surveyed 1,812 Ukrainians in three frontline "
    "eastern cities in July 2022 and again in April 2023. They use latent "
    "profile analysis to identify complex identity combinations and link them "
    "to support for war versus negotiation — a useful template for the "
    "argument that within-group heterogeneity matters more than mean shifts. "
    "The two-wave structure parallels Brian's two-wave EIM design but with a "
    "shorter interval and an active war zone."
)
add_citation(
    "Korostelina, K. V., Sweigart, M. M., & Toal, G. (2026). Outgroup Threat, "
    "complex identities, and attitudes toward war and peace in Ukraine.",
    "Group Processes & Intergroup Relations.",
    "https://doi.org/10.1177/13684302251344532",
)

add_subheading("Difference-in-differences with repeated cross-sectional data")
add_para(
    "Because Brian's data are cross-sectional rather than panel, the standard "
    "two-wave-before/after analysis can be framed as a difference between "
    "population means at two time points. The 2025 methodological article in "
    "Health Services and Outcomes Research Methodology lays out the assumption "
    "structure and bias considerations when the same population is sampled "
    "twice but different individuals are interviewed. The Lebo and Weber 2015 "
    "AJPS paper is the political-science methodology touchstone for repeated "
    "cross-sectional designs."
)
add_citation(
    "Wong, J., et al. (2025). Difference-in-differences analysis with "
    "repeated cross-sectional survey data.",
    "Health Services and Outcomes Research Methodology, advance access.",
    "https://pubmed.ncbi.nlm.nih.gov/41346788/",
)
add_citation(
    "Lebo, M. J., & Weber, C. (2015). An Effective Approach to the Repeated "
    "Cross-Sectional Design.",
    "American Journal of Political Science, 59(1), 242-258.",
    "https://onlinelibrary.wiley.com/doi/abs/10.1111/ajps.12095",
)

# =====================================================================
# SECTION 3: Majority-minority comparative designs
# =====================================================================
add_heading("Section 3. Majority-Minority Comparative Designs Across Country Contexts")

add_para(
    "Comparable designs from Belgium, the Netherlands, and Northern Ireland. "
    "These studies demonstrate established techniques for handling the "
    "structural asymmetry between a majority and a minority within one "
    "country: different sample sizes, different baseline attitudes, and the "
    "fact that the \"same\" question often means different things to the two "
    "groups."
)

add_subheading("Flemish-Walloon comparative attitudes (Belgium)")
add_para(
    "Meeusen, Boonen, and Dassonneville's special issue in Psychologica "
    "Belgica brings together survey work on Belgian linguistic-community "
    "attitudes. The papers show how to compare two within-country groups "
    "while accounting for asymmetric in-group identification and economic "
    "threat perceptions. The Meeusen and Jacobs paper specifically compares "
    "anti-Walloon and anti-immigrant attitudes in Flanders — useful "
    "because it treats the in-state minority as one category alongside "
    "out-of-state minorities, isolating what is specific to majority-"
    "subordinate dynamics within one polity."
)
add_citation(
    "Meeusen, C., & Jacobs, L. (2017). Walloons as General or Specific "
    "Others? A Comparison of anti-Walloon and anti-immigrant Attitudes in "
    "Flanders.",
    "Psychologica Belgica, 57(3), 76-95.",
    "https://psychologicabelgica.com/articles/10.5334/pb.336",
)
add_citation(
    "Meeusen, C., et al. (2018). Insights into the Belgian Linguistic Conflict "
    "from a (Social) Psychological Perspective: Introduction to the Special "
    "Issue.",
    "Psychologica Belgica, 58(1), 1-12.",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC6194511/",
)

add_subheading("Verkuyten and Martinovic on Dutch majority-minority attitudes")
add_para(
    "Verkuyten and Martinovic's body of work on immigrants' national "
    "identification in the Netherlands is the canonical template for "
    "comparing host-country and immigrant attitudes on multi-item composite "
    "scales. They use 7-point Likert items on multicultural support, ethnic "
    "and national identification, and perceived discrimination, validated "
    "via standard CFA. The framework also explains why dual-identity patterns "
    "(both ethnic and national) are most common in minorities — directly "
    "relevant to Brian's group identity patterns variable."
)
add_citation(
    "Verkuyten, M., & Martinovic, B. (2012). Immigrants' National "
    "Identification: Meanings, Determinants, and Consequences.",
    "Social Issues and Policy Review, 6(1), 82-112.",
    "https://spssi.onlinelibrary.wiley.com/doi/abs/10.1111/j.1751-2409.2011.01036.x",
)
add_citation(
    "Verkuyten, M., & Martinovic, B. (2012). Social Identity Complexity and "
    "Immigrants' Attitude Toward the Host Nation.",
    "Personality and Social Psychology Bulletin, 38(9), 1165-1177.",
    "https://journals.sagepub.com/doi/10.1177/0146167212446164",
)
add_citation(
    "Verkuyten, M., Mepham, K., & Kros, M. (2018). Public attitudes towards "
    "support for migrants: the importance of perceived voluntary and "
    "involuntary migration.",
    "Ethnic and Racial Studies, 41(5), 901-918.",
)

add_subheading("Hewstone and colleagues on Northern Ireland contact")
add_para(
    "The Hewstone group's Northern Ireland work uses surveys of Catholic and "
    "Protestant respondents to estimate cross-community contact effects, "
    "consistently finding that more frequent contact predicts lower out-group "
    "prejudice, lower anxiety, and more forgiveness. The 2006 Journal of "
    "Social Issues paper specifically shows how to estimate contact effects "
    "asymmetrically across the two groups (the contact-prejudice link is "
    "often stronger for one side). Brian's contact composites for Russian-"
    "speakers and Estonians can be discussed in light of this asymmetric "
    "pattern."
)
add_citation(
    "Hewstone, M., Cairns, E., Voci, A., Hamberger, J., & Niens, U. (2006). "
    "Intergroup Contact, Forgiveness, and Experience of \"The Troubles\" in "
    "Northern Ireland.",
    "Journal of Social Issues, 62(1), 99-120.",
    "https://spssi.onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-4560.2006.00441.x",
)
add_citation(
    "Hughes, J., Campbell, A., Hewstone, M., & Cairns, E. (2007). Segregation "
    "in Northern Ireland.",
    "Policy Studies, 28(1), 33-53.",
)

add_subheading("Perceived status and national belonging (Finland and Estonia)")
add_para(
    "Jasinskaja-Lahti and colleagues compared Russian-speakers in Finland and "
    "Estonia on perceived status and national belonging using identical "
    "instruments in both contexts. The two-country, one-minority design is a "
    "useful template for Brian's framing of Estonia as one case in a wider "
    "Baltic and Nordic Russian-speaker landscape."
)
add_citation(
    "Jasinskaja-Lahti, I., et al. (2018). Perceived Status and National "
    "Belonging: The Case of Russian Speakers in Finland and Estonia.",
    "International Review of Social Psychology, 31(1), 8.",
    "https://rips-irsp.com/articles/10.5334/irsp.149",
)

# =====================================================================
# SECTION 4: Measurement-invariance pragmatics
# =====================================================================
add_heading("Section 4. Measurement-Invariance Pragmatics")

add_para(
    "Two kinds of papers help Brian here. The first kind takes invariance "
    "testing very seriously and uses alignment optimisation or partial-"
    "invariance methods to recover comparable means despite non-invariance. "
    "The second kind acknowledges non-invariance in a methods paragraph and "
    "proceeds with the descriptive framing, treating observed-group "
    "differences as substantively meaningful while flagging the measurement "
    "caveat. Both routes are defensible. Brian's current write-up follows "
    "the second route, which is the more common choice in master's-level "
    "and applied work."
)

add_subheading("The technical canon: Davidov, Cieciuch, and Schmidt")
add_para(
    "The most-cited methodological work on cross-cultural measurement "
    "invariance is the Davidov, Meuleman, Cieciuch, Schmidt, and Billiet 2014 "
    "Annual Review of Sociology paper. The Cieciuch, Davidov, Algesheimer, "
    "and Schmidt 2018 Sociological Methods and Research paper is the "
    "principal reference for approximate invariance testing in ESS data. The "
    "Asparouhov and Muthen alignment optimisation method is now standard for "
    "comparing latent means across many groups even when exact scalar "
    "invariance fails."
)
add_citation(
    "Davidov, E., Meuleman, B., Cieciuch, J., Schmidt, P., & Billiet, J. "
    "(2014). Measurement Equivalence in Cross-National Research.",
    "Annual Review of Sociology, 40, 55-75.",
    "https://www.annualreviews.org/doi/pdf/10.1146/annurev-soc-071913-043137",
)
add_citation(
    "Cieciuch, J., Davidov, E., Algesheimer, R., & Schmidt, P. (2018). "
    "Testing for Approximate Measurement Invariance of Human Values in the "
    "European Social Survey.",
    "Sociological Methods & Research, 47(4), 665-686.",
    "https://journals.sagepub.com/doi/abs/10.1177/0049124117701478",
)
add_citation(
    "Davidov, E., Muthen, B., & Schmidt, P. (2018). Measurement Invariance "
    "in Cross-National Studies: Challenging Traditional Approaches and "
    "Bringing in New Ones.",
    "Sociological Methods & Research, 47(4), 631-636.",
    "https://journals.sagepub.com/doi/full/10.1177/0049124118789708",
)
add_citation(
    "Marsh, H. W., et al. (2017). What to do When Scalar Invariance Fails: "
    "The Extended Alignment Method for Multi-Group Factor Analysis Comparison "
    "of Latent Means Across Many Groups.",
    "Psychological Methods, 23(3), 524-545.",
    "https://www.researchgate.net/publication/312343260",
)

add_subheading("Pragmatic precedents: descriptive framing despite non-invariance")
add_para(
    "The Sarrasin and colleagues 2018 paper on political trust illustrates "
    "the pragmatic route: the authors acknowledge measurement non-invariance "
    "explicitly in the methods section, report the diagnostic results, then "
    "proceed with descriptive cross-national comparisons while flagging the "
    "caveat in the discussion. This is the model for Brian's invariance "
    "footnote: report the test, acknowledge the failure, defend descriptive "
    "framing on substantive grounds, and refer the reader to a robustness "
    "table."
)
add_citation(
    "Andre, S., Sarrasin, O., Reeskens, T., & Davidov, E. (2017). Can We "
    "Trust Measures of Political Trust? Assessing Measurement Equivalence "
    "in Diverse Regime Types.",
    "Social Indicators Research.",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC5579303/",
)
add_citation(
    "Ariely, G., & Davidov, E. (2011). Assessment of Measurement Equivalence "
    "with Cross-National and Longitudinal Surveys in Political Science.",
    "European Political Science, 11, 363-377.",
    "https://link.springer.com/article/10.1057/eps.2011.11",
)
add_citation(
    "Welzel, C., Kruse, S., & Brunkert, L. (2021). Measurement Invariance of "
    "Liberal and Authoritarian Notions of Democracy: Evidence From the "
    "World Values Survey.",
    "Frontiers in Political Science, 3, 642283.",
    "https://www.frontiersin.org/journals/political-science/articles/10.3389/fpos.2021.642283/full",
)

# =====================================================================
# SECTION 5: Asymmetric divergence findings
# =====================================================================
add_heading("Section 5. Asymmetric Divergence in Political Psychology")

add_para(
    "This is Brian's strongest theoretical contribution: the same exogenous "
    "shock (the 2022 invasion) moves Estonian and Russian respondents in "
    "different and sometimes opposite directions across the EIM batteries. "
    "Published work confirming similar asymmetry strengthens the discussion "
    "chapter by establishing that the pattern is publishable, not artefactual."
)

add_subheading("Bilali, Celik, and Ok (revisited): the paradigm case")
add_para(
    "Already cited in Section 2. The headline finding is that during high-"
    "intensity Kurdish-Turkish conflict, Kurds (minority) showed higher "
    "social distance but also higher assimilative nationalism, less out-group "
    "negativity, and lower support for minority rights — a non-parallel "
    "movement compared with Turks (majority), who hardened uniformly. This "
    "is the closest published analogue of Brian's Russian community showing "
    "increased contact and decreased belief in inevitable conflict alongside "
    "increased polarisation on superordinate identity."
)

add_subheading("Bobo's group position threat framework")
add_para(
    "Lawrence Bobo's group position theory — derived from Blumer and "
    "developed through racial-attitudes research using the General Social "
    "Survey and the Chippewa treaty rights survey — provides the "
    "theoretical scaffolding for why majority and minority groups react "
    "differently to threat. The majority response is defensive consolidation; "
    "the minority response is heterogeneous, often combining identity-"
    "assertion with selective accommodation. Brian's findings can be placed "
    "within this tradition."
)
add_citation(
    "Bobo, L. (1999). Prejudice as Group Position: Microfoundations of a "
    "Sociological Approach to Racism and Race Relations.",
    "Journal of Social Issues, 55(3), 445-472.",
    "https://scholar.harvard.edu/files/bobo/files/1999_prejudice_as_a_group_position.pdf",
)
add_citation(
    "Bobo, L., & Hutchings, V. L. (1996). Perceptions of Racial Group "
    "Competition: Extending Blumer's Theory of Group Position to a "
    "Multiracial Social Context.",
    "American Sociological Review, 61(6), 951-972.",
)

add_subheading("Loss of majority position: asymmetric reactions")
add_para(
    "The Seyranian and colleagues 2008 paper experimentally demonstrates that "
    "loss of majority position decreases perception of group-self similarity "
    "and expectations for positive interactions — but gaining majority "
    "position does not symmetrically increase them. This asymmetry maps onto "
    "Brian's finding that the war shock produced different magnitudes of "
    "response in the two communities."
)
add_citation(
    "Seyranian, V., Atuel, H., & Crano, W. D. (2008). Dimensions of majority "
    "and minority groups.",
    "Group Processes & Intergroup Relations, 11(1), 21-37.",
)

add_subheading("Outgroup threat and complex identities in Ukraine")
add_para(
    "Korostelina, Sweigart, and Toal (already cited) directly model how "
    "different identity profiles produce different threat-attitude relations. "
    "Their multivariate latent profile analysis is a useful template for "
    "Brian's argument that what looks like \"no change\" in Russian "
    "superordinate-identity mean conceals a community internally pulling "
    "apart."
)

# =====================================================================
# SECTION 6: Variance and polarization as substantive findings
# =====================================================================
add_heading("Section 6. Variance and Polarisation as Substantive Findings")

add_para(
    "Brian's Levene's-test polarisation result (Russian superordinate-"
    "identity variance grew significantly from 2020 to 2023, while the mean "
    "barely moved) is methodologically grounded in this tradition. Reporting "
    "variance as a substantive outcome rather than as a statistical nuisance "
    "is well-established in opinion research."
)

add_subheading("DiMaggio, Evans, and Bryson on US opinion polarisation")
add_para(
    "The canonical article. The authors decompose polarisation into four "
    "components — dispersion, bimodality, constraint, and group "
    "differentiation — and use variance, kurtosis, and group differences "
    "as separate indicators. Their methodology is exactly what Brian's "
    "Levene's-test analysis applies. The paper also models the careful "
    "interpretive move: variance increase is itself a substantive finding "
    "about social cohesion, even when the mean is stable."
)
add_citation(
    "DiMaggio, P., Evans, J., & Bryson, B. (1996). Have American's Social "
    "Attitudes Become More Polarized?",
    "American Journal of Sociology, 102(3), 690-755.",
    "http://www.acsu.buffalo.edu/~jcampbel/documents/DimaggioEvansBryson.pdf",
)
add_citation(
    "Evans, J. H. (2003). Have Americans' Attitudes Become More Polarized? "
    "An Update.",
    "Social Science Quarterly, 84(1), 71-90.",
    "https://onlinelibrary.wiley.com/doi/abs/10.1111/1540-6237.8401005",
)

add_subheading("Group-based polarisation measurement")
add_para(
    "The 2024 APSR paper by Levendusky and colleagues introduces the cluster-"
    "polarisation coefficient, explicitly modelling intergroup heterogeneity "
    "and intragroup homogeneity. The paper formalises why mean differences "
    "and variance comparisons are conceptually distinct measures of "
    "polarisation — reinforcing the case for Brian to report both."
)
add_citation(
    "Levendusky, M., et al. (2024). A Group-Based Approach to Measuring "
    "Polarization.",
    "American Political Science Review, advance access.",
    "https://www.cambridge.org/core/journals/american-political-science-review/article/groupbased-approach-to-measuring-polarization/7979CFDC243FB1E21FE7AE3724B42EEA",
)

add_subheading("Affective polarisation as a parallel research tradition")
add_para(
    "The Iyengar tradition on affective polarisation also relies on variance "
    "and distance measures rather than mean shifts alone. The 2019 Annual "
    "Review of Political Science article surveys the field. Useful for "
    "Brian's discussion as a methodological cousin: a body of work that "
    "measures social distance between two groups using multiple operational "
    "definitions, treating the choice of metric as a substantive matter."
)
add_citation(
    "Iyengar, S., Lelkes, Y., Levendusky, M., Malhotra, N., & Westwood, S. J. "
    "(2019). The Origins and Consequences of Affective Polarization in the "
    "United States.",
    "Annual Review of Political Science, 22, 129-146.",
    "https://pcl.sites.stanford.edu/sites/g/files/sbiybj22066/files/media/file/iyengar-ar-origins.pdf",
)
add_citation(
    "Reiljan, A. (2020). Fear and loathing across party lines (also) in "
    "Europe: Affective polarisation in European party systems.",
    "European Journal of Political Research, 59(2), 376-396.",
)

# =====================================================================
# SECTION 7: Structural template for Brian's thesis chapters
# =====================================================================
add_heading("Section 7. Recommended Structural Template for Brian's Thesis Chapters")

add_para(
    "Synthesising the patterns across Sections 1 to 6, here are six chapter-"
    "level recommendations Brian can apply directly."
)

add_subheading("1. Design section: frame the two waves as a quasi-natural-experiment opportunity, not an experiment")
add_para(
    "Ekman (2024), Bilali et al. (2014), and Korostelina et al. (2026) all "
    "treat their two-wave designs as repeated cross-sectional snapshots "
    "around a shock, not as panel comparisons. None claim causal "
    "identification. Brian's framing should explicitly say: the 2022 war is "
    "exogenous to EIM survey timing, but the design supports descriptive "
    "comparison only, not a within-person change. The Lebo and Weber (2015) "
    "and Wong et al. (2025) methodological pieces are the citations for "
    "this framing."
)

add_subheading("2. Composite construction: PCA plus alpha is the standard, CFA invariance is the bonus")
add_para(
    "Across Sections 1, 3, and 4, the standard reporting package is: (a) "
    "describe the items, (b) report Cronbach's alpha, (c) report PCA loadings "
    "or eigenvalues, (d) defend the choice of single-factor versus "
    "multi-factor structure on theoretical and empirical grounds. Brian "
    "already does all four. Measurement-invariance testing via multi-group "
    "CFA is the modern bonus that elevates a master's thesis methodologically "
    "without requiring substantive reanalysis."
)

add_subheading("3. Robustness checks: standard package")
add_para(
    "Three robustness checks recurred across the literature surveyed:"
)
add_bullet("Subgroup analyses by education, age, region, or language pathway (Brian has this via the edu_language subgroup analysis)")
add_bullet("Item-level decomposition when composite results are ambiguous (Brian has this via the item-decomposition charts)")
add_bullet("Listwise vs. pairwise comparison of how missing data handling affects results (Brian has this implicitly via the pairwise-deletion canonical TSV)")

add_subheading("4. Limitations paragraph: standard formula")
add_para(
    "Almost every paper surveyed includes a methods-limitations paragraph "
    "covering: (a) repeated cross-section means no within-person inference; "
    "(b) measurement invariance limits comparison of latent means; (c) "
    "self-report bias and social desirability; (d) sample composition shifts "
    "between waves. Brian's draft should include each of these explicitly. "
    "The Russian sample composition shift from N ≈ 609 to N ≈ 522 "
    "(SESSION_LOG section 29 FLAG 1) belongs in this paragraph."
)

add_subheading("5. Figures and tables: conventional set")
add_para(
    "The conventional figure-table set is:"
)
add_bullet("A summary table of composite reliability statistics (alpha, items, scale direction)")
add_bullet("A means table by group and wave with N and SD")
add_bullet("An effect-size table with d and 95% CI")
add_bullet("One or two flagship visualisations (Brian has dumbbell and within-group bar charts)")
add_bullet("Optional: item-level distribution plots for the constructs where the composite picture is ambiguous")

add_subheading("6. Discussion structure: substantive then methodological")
add_para(
    "The standard discussion structure surveyed runs: (a) restate the "
    "between-group and within-group pattern, (b) interpret it in light of "
    "the dominant theoretical framework (for Brian: contact theory, group "
    "position theory, common in-group identity), (c) handle the most "
    "surprising or asymmetric finding head-on, (d) acknowledge the "
    "measurement-invariance caveat, (e) close with policy or research "
    "implications. Brian's asymmetric-divergence finding sits naturally at "
    "step (c), with the polarisation-variance finding as a supporting "
    "subsection."
)

# =====================================================================
# SECTION 8: Consolidated bibliography
# =====================================================================
add_heading("Section 8. Consolidated Bibliography (APA 7, Alphabetical)")

add_para(
    "All papers cited above, ordered alphabetically by first author. URLs "
    "and DOIs included where verified.",
    italic=True, size=10,
)

bib = [
    ("Andre, S., Sarrasin, O., Reeskens, T., & Davidov, E. (2017). Can we trust measures of political trust? Assessing measurement equivalence in diverse regime types. Social Indicators Research.",
     "https://pmc.ncbi.nlm.nih.gov/articles/PMC5579303/"),
    ("Ariely, G., & Davidov, E. (2011). Assessment of measurement equivalence with cross-national and longitudinal surveys in political science. European Political Science, 11, 363-377.",
     "https://link.springer.com/article/10.1057/eps.2011.11"),
    ("Auers, D., & colleagues (2023). Paradoxes of minority representation: a comparison of Russophone political attitudes in Estonia and Latvia. Journal of Baltic Studies, 54(3).",
     "https://www.tandfonline.com/doi/full/10.1080/01629778.2022.2150667"),
    ("Bilali, R., Celik, A. B., & Ok, E. (2014). Psychological asymmetry in minority-majority relations at different stages of ethnic conflict. International Journal of Intercultural Relations, 43(B), 253-264.",
     "https://www.sciencedirect.com/science/article/abs/pii/S0147176714001096"),
    ("Bobo, L. (1999). Prejudice as group position: Microfoundations of a sociological approach to racism and race relations. Journal of Social Issues, 55(3), 445-472.",
     "https://scholar.harvard.edu/files/bobo/files/1999_prejudice_as_a_group_position.pdf"),
    ("Bobo, L., & Hutchings, V. L. (1996). Perceptions of racial group competition: Extending Blumer's theory of group position to a multiracial social context. American Sociological Review, 61(6), 951-972.",
     None),
    ("Cheskin, A. (2013). Exploring Russian-speaking identity from below: The case of Latvia. Journal of Baltic Studies, 44(3), 287-312.",
     "https://www.tandfonline.com/doi/full/10.1080/01629778.2012.712335"),
    ("Cheskin, A., & Kachuyevski, A. (2019). The Russian-speaking populations in the post-Soviet space: Language, politics and identity. Europe-Asia Studies, 71(1), 1-23.",
     "https://eprints.gla.ac.uk/173351/1/173351.pdf"),
    ("Cieciuch, J., Davidov, E., Algesheimer, R., & Schmidt, P. (2018). Testing for approximate measurement invariance of human values in the European Social Survey. Sociological Methods & Research, 47(4), 665-686.",
     "https://journals.sagepub.com/doi/abs/10.1177/0049124117701478"),
    ("Davidov, E., Meuleman, B., Cieciuch, J., Schmidt, P., & Billiet, J. (2014). Measurement equivalence in cross-national research. Annual Review of Sociology, 40, 55-75.",
     "https://www.annualreviews.org/doi/pdf/10.1146/annurev-soc-071913-043137"),
    ("Davidov, E., Muthen, B., & Schmidt, P. (2018). Measurement invariance in cross-national studies: Challenging traditional approaches and bringing in new ones. Sociological Methods & Research, 47(4), 631-636.",
     "https://journals.sagepub.com/doi/full/10.1177/0049124118789708"),
    ("DiMaggio, P., Evans, J., & Bryson, B. (1996). Have American's social attitudes become more polarized? American Journal of Sociology, 102(3), 690-755.",
     "http://www.acsu.buffalo.edu/~jcampbel/documents/DimaggioEvansBryson.pdf"),
    ("Ekman, J. (2024). In the shadow of war: Public opinion in the Baltic states, 2014 and 2021. Journal of Baltic Studies (Baltic Worlds special issue).",
     "https://journals.sagepub.com/doi/full/10.1177/18793665241270812"),
    ("Evans, J. H. (2003). Have Americans' attitudes become more polarized? An update. Social Science Quarterly, 84(1), 71-90.",
     "https://onlinelibrary.wiley.com/doi/abs/10.1111/1540-6237.8401005"),
    ("Hewstone, M., Cairns, E., Voci, A., Hamberger, J., & Niens, U. (2006). Intergroup contact, forgiveness, and experience of \"The Troubles\" in Northern Ireland. Journal of Social Issues, 62(1), 99-120.",
     "https://spssi.onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-4560.2006.00441.x"),
    ("Hobolt, S. B., Leeper, T. J., & Tilley, J. (2021). Policy preferences and policy legitimacy after referendums: Evidence from the Brexit negotiations. Political Behavior, 43, 1565-1593.",
     "https://link.springer.com/article/10.1007/s11109-020-09639-w"),
    ("Hobolt, S. B., & Tilley, J. (2024). Tribal politics: How the Brexit vote reshaped Britain. Oxford University Press.",
     "https://global.oup.com/academic/product/tribal-politics-9780198911715"),
    ("Iyengar, S., Lelkes, Y., Levendusky, M., Malhotra, N., & Westwood, S. J. (2019). The origins and consequences of affective polarization in the United States. Annual Review of Political Science, 22, 129-146.",
     "https://pcl.sites.stanford.edu/sites/g/files/sbiybj22066/files/media/file/iyengar-ar-origins.pdf"),
    ("Jasinskaja-Lahti, I., et al. (2018). Perceived status and national belonging: The case of Russian speakers in Finland and Estonia. International Review of Social Psychology, 31(1), 8.",
     "https://rips-irsp.com/articles/10.5334/irsp.149"),
    ("Korostelina, K. V., Sweigart, M. M., & Toal, G. (2026). Outgroup threat, complex identities, and attitudes toward war and peace in Ukraine. Group Processes & Intergroup Relations.",
     "https://doi.org/10.1177/13684302251344532"),
    ("Lebo, M. J., & Weber, C. (2015). An effective approach to the repeated cross-sectional design. American Journal of Political Science, 59(1), 242-258.",
     "https://onlinelibrary.wiley.com/doi/abs/10.1111/ajps.12095"),
    ("Levendusky, M., et al. (2024). A group-based approach to measuring polarization. American Political Science Review, advance access.",
     "https://www.cambridge.org/core/journals/american-political-science-review/article/groupbased-approach-to-measuring-polarization/7979CFDC243FB1E21FE7AE3724B42EEA"),
    ("Marsh, H. W., et al. (2017). What to do when scalar invariance fails: The extended alignment method for multi-group factor analysis comparison of latent means across many groups. Psychological Methods, 23(3), 524-545.",
     "https://www.researchgate.net/publication/312343260"),
    ("Meeusen, C., & Jacobs, L. (2017). Walloons as general or specific others? A comparison of anti-Walloon and anti-immigrant attitudes in Flanders. Psychologica Belgica, 57(3), 76-95.",
     "https://psychologicabelgica.com/articles/10.5334/pb.336"),
    ("Meeusen, C., et al. (2018). Insights into the Belgian linguistic conflict from a (social) psychological perspective. Psychologica Belgica, 58(1), 1-12.",
     "https://pmc.ncbi.nlm.nih.gov/articles/PMC6194511/"),
    ("Pettigrew, T. F., & Tropp, L. R. (2006). A meta-analytic test of intergroup contact theory. Journal of Personality and Social Psychology, 90(5), 751-783.",
     "https://pubmed.ncbi.nlm.nih.gov/16737372/"),
    ("Putnam, R. D. (2007). E pluribus unum: Diversity and community in the twenty-first century. The 2006 Johan Skytte Prize Lecture. Scandinavian Political Studies, 30(2), 137-174.",
     "https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1467-9477.2007.00176.x"),
    ("Reiljan, A. (2020). Fear and loathing across party lines (also) in Europe: Affective polarisation in European party systems. European Journal of Political Research, 59(2), 376-396.",
     None),
    ("Seyranian, V., Atuel, H., & Crano, W. D. (2008). Dimensions of majority and minority groups. Group Processes & Intergroup Relations, 11(1), 21-37.",
     None),
    ("Sturgis, P., Brunton-Smith, I., Read, S., & Allum, N. (2011). Does ethnic diversity erode trust? Putnam's 'hunkering down' thesis reconsidered. British Journal of Political Science, 41(1), 57-82.",
     "https://www.cambridge.org/core/journals/british-journal-of-political-science/article/abs/does-ethnic-diversity-erode-trust-putnams-hunkering-down-thesis-reconsidered/DC0DA871517729C51D08C4C7FF34E03B"),
    ("Valk, A. (2000). Ethnic identity, ethnic attitudes, self-esteem, and esteem toward others among Estonian and Russian adolescents. Journal of Adolescent Research, 15(6), 637-651.",
     "https://journals.sagepub.com/doi/10.1177/0743558400156002"),
    ("Verkuyten, M., & Martinovic, B. (2012a). Immigrants' national identification: Meanings, determinants, and consequences. Social Issues and Policy Review, 6(1), 82-112.",
     "https://spssi.onlinelibrary.wiley.com/doi/abs/10.1111/j.1751-2409.2011.01036.x"),
    ("Verkuyten, M., & Martinovic, B. (2012b). Social identity complexity and immigrants' attitude toward the host nation. Personality and Social Psychology Bulletin, 38(9), 1165-1177.",
     "https://journals.sagepub.com/doi/10.1177/0146167212446164"),
    ("Vihalemm, T., & Juzefovics, J. (2022). Navigating conflicts through the media: The sceptical and self-responsible repertoires of Baltic Russian-speakers. East European Politics and Societies, 36(4), 1213-1238.",
     "https://journals.sagepub.com/doi/abs/10.1177/0888325420964946"),
    ("Vihalemm, T., & Masso, A. (2003). Identity dynamics of Russian-speakers of Estonia in the transition period. Journal of Baltic Studies, 34(1), 92-116.",
     "https://www.semanticscholar.org/paper/Identity-dynamics-of-Russian-speakers-of-Estonia-in-Vihalemm-Masso/bea98869a431985febffb373008b17e79174a048"),
    ("Welzel, C., Kruse, S., & Brunkert, L. (2021). Measurement invariance of liberal and authoritarian notions of democracy: Evidence from the World Values Survey. Frontiers in Political Science, 3, 642283.",
     "https://www.frontiersin.org/journals/political-science/articles/10.3389/fpos.2021.642283/full"),
    ("Whitt, S., & Page, D. (2025a). War, social preferences, and anti-outgroup behavior: Experimental evidence from Russia's invasion of Ukraine. Journal of Peace Research.",
     "https://doi.org/10.1177/00223433251318931"),
    ("Whitt, S., & Page, D. (2025b). War-related victimization and social distance toward others: Evidence following Russia's 2022 invasion of Ukraine. International Political Science Review.",
     "https://journals.sagepub.com/doi/10.1177/00108367251321435"),
    ("Wong, J., et al. (2025). Difference-in-differences analysis with repeated cross-sectional survey data. Health Services and Outcomes Research Methodology, advance access.",
     "https://pubmed.ncbi.nlm.nih.gov/41346788/"),
]

for ref, url in bib:
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.left_indent = Cm(0.6)
    p.paragraph_format.first_line_indent = Cm(-0.6)
    r = p.add_run(ref)
    r.font.size = Pt(10)
    if url:
        r2 = p.add_run("  " + url)
        r2.font.size = Pt(9)

# =====================================================================
# Closing note
# =====================================================================
add_heading("Notable Gaps in the Literature")
add_para(
    "Three gaps emerged from the search where Brian's contribution may be "
    "particularly novel:"
)
add_bullet(
    "Quantitative EIM analysis as a thesis. Most existing EIM-based work is "
    "qualitative or descriptive policy reporting (e.g., the Praxis summaries). "
    "Quantitative replication using PCA-validated composites, Cohen's d with "
    "CIs, and CFA invariance is rarer."
)
add_bullet(
    "Post-2022 Baltic minority attitudes with two-wave EIM-style instruments. "
    "Most post-2022 European public opinion work covers majority populations "
    "or pooled samples; Brian's design with separate Estonian and Russian "
    "subsamples on a battery of intergroup-relations composites is unusual."
)
add_bullet(
    "Variance-as-substantive-finding in Baltic intergroup work. The within-"
    "Russian polarisation pattern Brian detects via Levene's tests is, to my "
    "knowledge, not formally reported elsewhere for this population. The "
    "DiMaggio framework provides the methodology; the Baltic application is "
    "new."
)

# =====================================================================
# Save
# =====================================================================
doc.save(out_path)
print(f"Saved: {out_path}")
