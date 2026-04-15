"""
SR-03 False-Positive Review — German bibliographic NER heuristic validation.
Purpose: Read sr03_heuristic_validation_sample.csv, determine which heuristic field flags
         are false positives for each title, and write results back to the file.
         Combines automated regex rules with per-row manual overrides for edge cases.
Usage: python scripts/sr03_fp_review.py
Inputs: data/processed/sr03_heuristic_validation_sample.csv
Outputs: Same file, with fp_fields and notes columns populated.
Dependencies: pandas
Assumptions: CSV has 200 rows (excluding header); columns 1-17 as per SR-03 spec.
"""

import re
import pandas as pd

CSV_PATH = "/Users/mta/Documents/claude/gemea/data/processed/ner/sr03_heuristic_validation_sample.csv"

df = pd.read_csv(CSV_PATH, dtype=str, keep_default_na=False)
df["fp_fields"] = ""
df["notes"] = ""


# ─────────────────────────────────────────────────────────────────────────────
# Per-row manual overrides for cases the heuristics can't handle cleanly.
# Keyed by obj_id; value is (fp_fields_list, notes_str).
# These override the automated logic entirely for that row.
# ─────────────────────────────────────────────────────────────────────────────

MANUAL_OVERRIDES = {
    # "Johann Ludwig Böhner :7. Januar 1787 - 28. März 1860 ; [Katalog]"
    # f_other_title=1 (fires on ' :') → FP: colon precedes life dates, not subtitle
    # f_year=1 → FP: 1787 and 1860 are life dates of Böhner, not publication year
    "THF6HTNRUTSYTYBY377JLKXHCWVHNYQP": (
        ["f_other_title", "f_year"],
        "':' precedes life dates 7. Jan 1787 – 28. März 1860, not ISBD subtitle; "
        "1787 and 1860 are life dates of Johann Ludwig Böhner, not publication year"
    ),

    # "Porträt Georg Philipp Wucherer (1734 - 1805) :Kupferstich ; Radierung"
    # f_other_title=1 → TP: ':Kupferstich' is a valid subtitle (medium/technique)
    # f_year=1 → FP: (1734–1805) are life dates in parentheses, not publication year
    "7EG6MNM55XRFKT63ZIUZN35OZAZMMY2B": (
        ["f_year"],
        "1734–1805 are life dates of Wucherer in parentheses, not publication year"
    ),

    # "Feldmarschall Ludwig Andreas Graf von Khevenhüller-Frankenburg ... :1683-1744 ; eine Lebensskizze"
    # f_other_title=1 → FP: ':1683-1744' are life dates, not a subtitle
    # f_year=1 → FP: 1683–1744 are life dates after the colon, not publication year
    "SKUC2ZDHLCDGXDWQ2NMGSDXZ5U6GLRPC": (
        ["f_other_title", "f_year"],
        "':' precedes life dates 1683–1744, not ISBD subtitle; "
        "1683–1744 are life dates of Khevenhüller-Frankenburg, not publication year"
    ),

    # "...Welche 1656. 10. Hornung im 39. Jahr ihres Alters ...eingeschlaffen ... bereit 1649."
    # f_other_title=1 → TP: ':Welche 1656...' is a genuine subtitle/continuation after ISBD colon
    # f_year=1 → FP: 1649 and 1656 are composition/biographical dates, not publication year
    "KUYEGVHZ7535QJG7V5XM2NU5HW2CTAAG": (
        ["f_year"],
        "1649 is composition date (bereit ... geschrieben) and 1656 is the death date in the title; "
        "neither is the publication year"
    ),

    # "David Beuthers ... von Anno 1514. biß 1582. geschriebenen Buche"
    # f_other_title=1 → TP: ':Darinnen...' is a genuine subtitle
    # f_year=1 → FP: 1514 and 1582 are manuscript date range (von Anno ... biß)
    "KQCJ7APICPYVGBUZ544FKAICNU73FVKH": (
        ["f_year"],
        "1514–1582 is a manuscript date range (von Anno 1514. biß 1582.), not publication year"
    ),

    # "Theaterzettel, 1831 = Stück 1"
    # f_parallel=1 → FP: '= Stück 1' is an enumeration designator, not a parallel title
    # f_year=1 → TP: 1831 is the publication year
    "AHPSBS6GRELK4AEEQSUBS7XO7YWHP72C": (
        ["f_parallel"],
        "'= Stück 1' is an enumeration designator, not a parallel title"
    ),

    # "Zeitschrift für Gerichtspraxis ... 14, 14 = N.S. Bd. 4. 1875"
    # f_parallel=1 → FP: '= N.S. Bd. 4' is an enumeration (New Series vol. 4), not parallel title
    # f_year=1 → TP: 1875 is publication year
    # f_volume=1 → TP: Bd. 4 is a volume designator
    "T73EF76JMJRMN55BDRFWK7OCZ5HYVFUX": (
        ["f_parallel"],
        "'= N.S. Bd. 4' is a new-series enumeration designator, not a parallel title"
    ),

    # "Eine historische Ontologie des Ungeborenen : Rezension zu: Caroline Arni: Pränatale Zeiten.
    #  Das Ungeborene und die Humanwissenschaften (1800-1950). Basel, Berlin: Schwabe Verlag 2018."
    # f_other_title=1 → TP: ':' separates genuine subtitle (Rezension zu:...)
    # f_year=1 → TP: 2018 is the publication year of the book being reviewed;
    #   (1800-1950) is the temporal coverage period of that book's subject matter, not life dates
    #   → the year flag is a TP (2018 is a valid year match)
    # My automated code wrongly flagged f_year as FP here.
    # Also f_publisher=1 → TP: "Schwabe Verlag" is publisher info embedded in the title
    "OQFAODAMPMJMFGMX7YJ7O3CMHCDKVQNA": (
        [],
        ""
    ),

    # "Likörfabrik J. Bansi Bielefeld: 1823 – 1960, Wirtschaft – Werbung – Wohlfahrt
    #  (Schriften der Historischen Museen der Stadt Bielefeld ; 6)"
    # f_year=1 → FP: 1823 is the founding year of the business and 1960 its closure;
    #   neither is the publication year (this is a museum publication about the factory)
    # f_series=1 → TP: '(Schriften der Historischen Museen ... ; 6)' is a legitimate series
    "HSZEUCMSKOA5I2WG2R77UMN6KAABVW7T": (
        ["f_year"],
        "1823–1960 is the business's operational period (founding to closure), not publication year"
    ),

    # "Transnationales Strafrecht / Transnational Criminal Law :: gesammelte Beiträge; collected publications"
    # f_other_title=1 → FP: ' :' is part of ' ::' catalog-field separator, not ISBD subtitle
    # f_person=1 → TP: '/' separates German title from English parallel title (not person SoR,
    #   but actually '/' is between title and SoR in ISBD; here it separates main title
    #   from subtitle continuation — however the flag fires on ' /' which is before
    #   "Transnational Criminal Law". This is actually a case where '/' joins the
    #   German and English titles in a bilingual work. Not a person SoR → FP for f_person.
    # f_person_compound=1 → same reasoning; not a compound SoR
    "XDNVRXBWWZMMHHFOPZBUEVOOJYL6TGDH": (
        ["f_other_title", "f_person", "f_person_compound"],
        "':' is part of '::' catalog-record field separator, not ISBD subtitle; "
        "'/' separates bilingual title elements (German/English), not a person SoR; "
        "no compound person SoR present"
    ),

    # "Matthatia - BSB Mus.ms. 2761 :[title page:] Matthatia // ein Singspiel // in zwei Aufzügen // 1796."
    # f_other_title=1 → TP: ':' introduces the title-page transcription (legitimate ISBD use)
    # f_person=1 → checking: ' /' appears in "[spine title:] Matth. Fischer // Matthatia // 1.2."
    #   The double slashes '//' are separating lines of a spine transcription,
    #   not ISBD person SoR → FP for f_person
    # f_year=1 → TP: 1796 is the composition/publication year of the singspiel
    "TESMJCHDS7J3G74XAGVKMC7JBBD6F4PV": (
        ["f_person"],
        "'//' separates lines of a title-page/spine transcription, not a person SoR separator"
    ),

    # "Reise Montalon / Vorarlberg vom 19.8. bis 4.9.1983"
    # f_person=1 → FP: '/' separates place name from region, not a person SoR
    # f_year=1 → TP: 1983 is the travel/event year — but wait, is this the pub year?
    #   For a travel diary, the trip year may equal the pub year or closely match it.
    #   The year heuristic fires correctly here → TP
    "QCRDA4PYSZP7JB3B57ENIZ7YZUK5NWP7": (
        ["f_person"],
        "'/' separates place name 'Montalon / Vorarlberg' (district/region), not a person SoR"
    ),

    # "12. Wochen / 1701."
    # f_person=1 → FP: '/ 1701' is a date separator (serial enumeration), not person SoR
    # f_year=1 → TP: 1701 is the publication year
    "VMYTGXKFHVZZ2JN4U4FDFKUWLOHKXQHE": (
        ["f_person"],
        "'/ 1701.' is a date/enumeration separator, not a person SoR"
    ),

    # "49. Wochen / 1701."
    # f_person=1 → FP: same pattern as above
    # f_year=1 → TP: 1701 is publication year
    "YFP477BOYD6KDAFMAB3DPGW23TPBUVGN": (
        ["f_person"],
        "'/ 1701.' is a date/enumeration separator, not a person SoR"
    ),

    # "62.1920(1921): Bericht über das ... Vereinsjahr ... // Kaufmännischer Verein von 1858"
    # f_person=1 → FP: '/' in '//' separates lines of an enumeration string, not person SoR
    # f_year=1 → TP: 1920/1921 are publication/report years
    "EK2F4VIWOJKUDIIWN326TL245RQZWMRO": (
        ["f_person"],
        "'//' in the title separates serial-volume enumeration parts, not a person SoR"
    ),

    # "1842/43,3: Mitteilungen ... / 1. Kammer"
    # f_person=1 → FP: '/ 1. Kammer' is a corporate body subdivision, not person SoR
    #   (1. Kammer = First Chamber of the parliament)
    # f_year=1 → TP: 1842/43 is the parliamentary session year
    "NTKDVAT7ZNK2GOS5UG3AJNNYPJE72N2G": (
        ["f_person"],
        "'/ 1. Kammer' indicates a parliamentary chamber subdivision, not a person SoR"
    ),

    # "1988: Statistische Berichte der Freien und Hansestadt Hamburg / K"
    # f_person=1 → FP: '/ K' is a series letter suffix, not a person SoR
    # f_year=1 → TP: 1988 is publication year
    "5VJBG7E7EIOY5VARC2MWNZTKHRKYPPYR": (
        ["f_person"],
        "'/ K' is a series letter suffix, not a person SoR"
    ),

    # "1962: Statistische Berichte der Freien und Hansestadt Hamburg / M"
    # f_person=1 → FP: '/ M' is a series letter suffix, not a person SoR
    # f_year=1 → TP: 1962 is publication year
    "7UFONBIX4RHXMA6RUESFJOMHVRPY4AQ4": (
        ["f_person"],
        "'/ M' is a series letter suffix, not a person SoR"
    ),

    # "1955: Hamburger statistische Informationen / F"
    # f_person=1 → FP: '/ F' is a series letter suffix, not a person SoR
    # f_year=1 → TP: 1955 is publication year
    "DVTEXFWNFMY3KIXT5A3JSP25OUAOROD7": (
        ["f_person"],
        "'/ F' is a series letter suffix, not a person SoR"
    ),

    # "1900,77/150=Apr./Juni: [Amtsblatt der Freien und Hansestadt Hamburg / Beiblatt, Öffentlicher Anzeiger"
    # f_person=1 → FP: '/ Beiblatt' is a serial supplement indicator, not person SoR;
    #   also '77/150' is a numeric issue range
    # f_year=1 → TP: year in enumeration prefix is publication year
    "3UVV5YUNWTGWWHD2X52PQSMMZKLV45RL": (
        ["f_person"],
        "'/ Beiblatt' indicates a serial supplement, not a person SoR; '77/150' is numeric issue range"
    ),

    # Matthatia: already handled above as TESMJCHDS7J3G74XAGVKMC7JBBD6F4PV

    # "Conflagratio Sodomae : Ein Erschröckliche Tragoedia ... Anno Christi 1617."
    # f_other_title=1 → TP: ':' introduces a genuine subtitle (translation/expansion)
    # f_year=1 → TP: 1617 is the performance year of the play; for a play published
    #   contemporaneously, this is essentially the publication year → TP
    # No FPs for this row.

    # "4/5.1876=Nr.167/219: Der Calculator an der Elbe ..."
    # f_other_title=1 → TP: ':' after the enumeration prefix introduces the actual title
    # f_year=1 → TP: 1876 is the publication year
    # f_volume=1 → TP: the '4/5' volume designation is correctly detected
    # No FPs.

    # "Hispanica ... 1729. = Spanien ..."
    # f_other_title=1 → TP: ':' introduces subtitle text (German subtitle of Latin drama)
    # f_parallel=1 → TP: '= Spanien...' is the German parallel title of a Latin drama title → TP
    # f_year=1 → TP: 1729 is the performance year (publication year)
    # No FPs.

    # "Allgemeine Forst- und Jagdzeitung ... = German journal of forest research. 2,6, [6] = N.F. 1837"
    # Two '=' signs: first is a parallel title (German → English journal name) → TP
    # Second '= N.F. 1837' is enumeration → FP
    # The flag fires on any ' ='; since there IS a genuine parallel title here,
    # the flag is a TP overall. But the second '=' is an enumeration. Since the flag
    # fires once but there are mixed cases, we mark as FP only if NO genuine parallel title.
    # Here there IS a genuine parallel title ("= German journal of forest research") → TP.
    # Revert the FP flag I set for DODWVIXPQLMN.
    "DODWVIXPQLMNGCGCXNYBB6GJYFACPA6W": (
        [],
        ""
    ),

    # "Eveille-toi Petit! :Chansonnette = (Erwache, Kind! Wach' auf)"
    # f_other_title=1 → TP: ':Chansonnette' is a subtitle (genre indication)
    # f_parallel=1 → TP: '= (Erwache, Kind! Wach' auf)' is German parallel title → TP
    # No FPs.
    "7RNN3SG6GY7FMOTNFTRQKRSXEQDAV2M2": (
        [],
        ""
    ),

    # "Hispania Auxilio ... Contra Mauros Vindicata :... 1729. = Spanien, ..."
    # f_other_title=1 → TP
    # f_parallel=1 → TP: genuine German parallel title of the Latin original
    # f_year=1 → TP
    "KFO5OD32QF2RLR6C33Y7MROEHYTETPXY": (
        [],
        ""
    ),

    # "Die Erdkunde ... = 3. Buch. West-Asien"
    # f_other_title=1 → TP: genuine subtitle
    # f_parallel=1 → FP or TP? "= 3. Buch. West-Asien" — this is an alternative title
    #   designation for part 3 (Theil 15 = 3. Buch). Not a parallel title in another language.
    #   This is an enumeration equivalence → FP.
    "YHBWG46RKEHYZGS27BUIY4NX53QY2UFK": (
        ["f_parallel"],
        "'= 3. Buch. West-Asien' is a volume/part equivalence designator, not a parallel title in another language"
    ),

    # "Vita Honesta Sive Virtvtis ... = Von einem Ehrlichen vnd Tugenreichen Leben ..."
    # f_other_title=1 → TP: genuine subtitle
    # f_parallel=1 → TP: '=' introduces genuine German parallel title of Latin original
    "D6ZBGQYUHG4ND4PLLP5HUYOZR3OYYUVD": (
        [],
        ""
    ),

    # "Edelstes Kleinod Menschlicher Gesundheit ... 2 = Ander Theil ..."
    # f_other_title=1 → TP: ':' introduces genuine subtitle
    # f_parallel=1 → FP: '= Ander Theil' is a volume/part equivalence label, not parallel title
    "P5BUJGBR5JXI3WNMJO64HSBVIPEGIZYY": (
        ["f_parallel"],
        "'= Ander Theil' is a volume-part equivalence label, not a parallel title in another language"
    ),

    # "Mathilde von Schabran :... = Matilde di Schabran : Dramma per Musica..."
    # f_other_title=1 → TP: ':musikalisches Drama...' is genuine subtitle
    # f_parallel=1 → TP: '= Matilde di Schabran' is genuine Italian parallel title
    "DWKM5VUI5CYSSETEK5WUKTHXWIZ7JXDG": (
        [],
        ""
    ),

    # "Thode, Barbara :: Das Hafen Buch : Hamburg, Schiffahrts-Verlag Hansa, 1984"
    # f_other_title=1 → FP: ' :' fires as part of ' ::' catalog separator
    # f_year=1 → TP: 1984 is publication year
    # f_publisher=1 → TP: "Schiffahrts-Verlag Hansa" is publisher info embedded in title field
    "CK23HEZ2HMLSYS7D3KVHWUDFRUKRWUAK": (
        ["f_other_title"],
        "':' is part of '::' catalog-record field separator, not ISBD subtitle"
    ),

    # "Glagla, Helmut :: Das plattdeutsche Liederbuch ... : 2., verb. Aufl., München, Artemis Verlag, 1982"
    # f_other_title=1 → FP: ' :' fires as part of ' ::' catalog separator
    # f_edition=1 → TP: '2., verb. Aufl.' is a genuine edition statement
    # f_year=1 → TP: 1982 is publication year
    # f_publisher=1 → TP: "Artemis Verlag" is publisher info
    "4MMKR3DGAJOTI572Q4Q42KM6IYP7ZZ67": (
        ["f_other_title"],
        "':' is part of '::' catalog-record field separator, not ISBD subtitle"
    ),

    # "Hagemann, Karen ; Kolossa, Jan :: Gleiche Rechte ... : Hamburg, VSA Verlag, 1990"
    # f_other_title=1 → FP: ' :' fires as part of ' ::' catalog separator
    # f_year=1 → TP: 1990 is publication year
    # f_publisher=1 → TP: "VSA Verlag" is publisher info
    "NLFOLQZ7NDOKZDFRPHZKKAJQKI3HGIBH": (
        ["f_other_title"],
        "':' is part of '::' catalog-record field separator, not ISBD subtitle"
    ),

    # "Wiemann, Harm :: Materialien ... (Abhandlungen und Vorträge ... 58) : Aurich, Verlag ..., 1982"
    # f_other_title=1 → FP: ' :' fires as part of ' ::' catalog separator
    # f_year=1 → TP: 1982 is publication year
    # f_publisher=1 → TP: publisher info embedded
    "I2X6SD4UV43OZ4FRBVI5427PCR4DPIHB": (
        ["f_other_title"],
        "':' is part of '::' catalog-record field separator, not ISBD subtitle"
    ),

    # "Brandis, Tilo :: Katalog ... : Hamburg, Hauswedell, 1967"
    # f_other_title=1 → FP: ' :' fires as part of ' ::' catalog separator
    # f_year=1 → TP: 1967 is publication year
    # f_volume=1 → TP: 'Bd. 4' is a volume designator
    "S52CDLV6S6UR3Z6JXJATBHMNHJDF5AKH": (
        ["f_other_title"],
        "':' is part of '::' catalog-record field separator, not ISBD subtitle"
    ),

    # "Dammrisse III. Grades in der Universitätsfrauenklinik Tübingen 1974 - 1983 :funktionelle..."
    # f_other_title=1 → TP: ':' introduces subtitle
    # f_year=1 → FP: 1974–1983 is the study period (date range of clinical data), not pub year.
    #   The year heuristic fires on 1974 (and 1983), but these are years of the study data.
    "5NCILISXATDS7CIYRB6LDFCNFZDNPMFR": (
        ["f_year"],
        "1974–1983 is the study period of the clinical data, not the publication year"
    ),

    # "Barther Tageblatt :(Barther Wochenblatt) ; Festnummer ; (1848-1928 ; 80 Jahre ...)"
    # f_other_title=1 → TP: ':' introduces parallel title / former title note
    # f_year=1 → FP: 1848 and 1928 are the founding and jubilee years of the newspaper,
    #   not publication year (confirmed by "80 Jahre" — it's an 80th anniversary issue).
    # f_series=1 → TP: the parenthetical content IS a series/note, and it has numbers
    "R253EZYBNYC2O3W7UUJBCMTFYDCR64QQ": (
        ["f_year"],
        "1848–1928 are founding and jubilee years of the newspaper (80-year anniversary), not publication year"
    ),

    # "Modulhandbuch Bachelor Angewandte Medien- und Kommunikationswissenschaft :Studienordnungsversion: 2012"
    # f_other_title=1 → TP: ':Studienordnungsversion: 2012' is a subtitle
    # f_year=1 → TP: 2012 is the version year (effectively publication year of the curriculum)
    # No FPs — TP for both.

    # "Mülheim a. d. Ruhr im April 1874 : (Schulprüfung betreffend)"
    # f_other_title=1 → TP: ':' introduces note "(Schulprüfung betreffend)"
    # f_year=1 → TP: 1874 is the year of the school examination (publication year)
    # No FPs.

    # The "Statistische Berichte / X. Y : ..." series — f_person=1
    # These titles have pattern "Statistische Berichte / Amt-Name. A, ..."
    # where '/' separates the serial title from its issuing body name. This IS the
    # ISBD statement of responsibility separator → TP for f_person.

    # "Mathematik. 1. Studienjahr 1955/56 ... / ausgearb. v. Fritz Krause ; Ernst Franck ..."
    # f_person=1 → TP: '/' separates title from SoR (authors Krause and Franck)
    # f_person_compound=1 → TP: compound SoR with multiple persons after ';'
    # f_year=1 → TP: 1955/56 is publication year
    # f_edition=1 — wait, what triggers this? The title has no edition keyword.
    #   Actually column 12 is f_edition. Let me check: f_edition=1 for this row.
    #   The title "Mathematik. 1. Studienjahr 1955/56, Mathematischer Vorkurs."
    #   No obvious Auflage/Ausgabe. Could trigger on something else?
    #   Actually looking again at col 12 (f_edition): for HLYS4OAISUA5 it's 0, for
    #   Q6QAYFIBXXAC (Mathematik) — let me check from the data:
    #   Row: Q6QAYFIBXXAC: f_other_title=0,f_person=1,f_person_compound=1,f_parallel=0,f_edition=1,f_year=1,...
    #   f_edition=1: the edition keyword must be in the title. Looking at full title:
    #   "Mathematik. 1. Studienjahr 1955/56, Mathematischer Vorkurs. / ausgearb. v. Fritz Krause ;
    #    Ernst Franck überarb. v. Siegbert Fröhlich"
    #   "überarb." could trigger? No, edition keywords are Auflage, Ausgabe, Ausg., etc.
    #   Wait — could "1. Studienjahr" trigger on "1."? Or could "Vorkurs" trigger something?
    #   Actually the flag list is: Auflage, Ausgabe, Ausg. etc. "Vorkurs" isn't one.
    #   Maybe I'm misreading. The full title from the CSV has:
    #   "Mathematik. 1. Studienjahr 1955/56, Mathematischer Vorkurs. / ausgearb. v. Fritz Krause ;
    #    Ernst Franck überarb. v. Siegbert Fröhlich"
    #   No edition keyword visible. Let me trust the data: f_edition=1 is set.
    #   Could be "Ausg." hidden somewhere, or "Aufl." in a column I'm not seeing.
    #   Given "überarb." (überarbeitet = revised) — some implementations count this.
    #   If the flag fires on "überarb." as an edition indicator, this IS a genuine
    #   edition-related term → TP (revised version).
    # No FPs for this row.

    # "Anorganisch-chemisches Praktikum ... Lehrbrief 1. / Bearb. v. W. Adam ; A. Fröde"
    # f_person=1 → TP: '/' before person name (Bearb. = compiler)
    # f_person_compound=1 → TP: compound SoR (Adam ; Fröde)
    # No FPs.

    # "Jahrbuch / Deutsche Shakespeare-Gesellschaft; 3"
    # f_person=1 → TP: '/' after Jahrbuch separates title from issuing body name
    # f_person_compound=1 → FP: the ';3' after the society name is a volume number,
    #   not a compound SoR listing. There is no second person after ';'.
    "BDMEHSHZCBPUG6NL3OKG4FMKKGL4VHMH": (
        ["f_person_compound"],
        "'; 3' is a volume number (issue 3), not a second person in a compound SoR"
    ),

    # "Meister-Holzschnitte aus vier Jahrhunderten / Hrsg. von Georg Hirth ; Richard Muther"
    # f_person=1 → TP: '/' separates title from editors (Hrsg.)
    # f_person_compound=1 → TP: two editors listed after ';'
    # No FPs.

    # "Statistische Berichte / Rheinland-Pfalz ... : Bewässerung ..."
    # f_other_title=1 → TP: ':' after enumeration introduces series note/subtitle → TP
    # f_person=1 → TP: '/' separates title from issuing body name
    # No FPs.

    # "Kosciuszko / Nach der Natur v. Olescynski ; in Stahl gest. v. Fleischmann"
    # f_person=1 → TP: '/' separates subject from artists (Nach der Natur v. = drawn from life by)
    # f_person_compound=1 → TP: compound SoR with two artists
    # No FPs.

    # "Statistische Berichte / Bayerisches Landesamt ... : Einwohnerzahlen ..."
    # f_other_title=1 → TP
    # f_person=1 → TP
    # f_person_compound=1 → FP? Let me check: " / Bayerisches Landesamt ... ; "
    #   The compound fires on ' / … ;' — after '/' there's a corporate body, not persons.
    #   The ';' introduces another topic/subtitle segment, not a second person.
    #   → FP for f_person_compound (corporate body, not person listing)
    # Actually looking at this more carefully: the pattern " / corporate body ; more text"
    # does fire as compound SoR, but it's a corporate body SoR, not person SoR.
    # However the flag name is f_person_compound, specifically for person listings.
    # Corporate body SoR is still a legitimate SoR, so the flag mis-labels it.
    # But whether this counts as an FP depends on the definition:
    # if f_person_compound means "compound person SoR" then corporate body → FP.
    # However the task says "FP if the compound SoR pattern is not actually a person listing."
    # These Statistische Berichte titles have "/ Corporate Body ; subdivision" patterns
    # where ';' separates the subdivision label, not multiple persons → FP.
    "54SBATDZQJGK5KQSFK3Q2RZU7U2RAQBM": (
        ["f_person_compound"],
        "'/ Bayerisches Landesamt ...' is a corporate body SoR, not a person listing; ';' separates a topical subtitle, not persons"
    ),
    "GKSDCS5H4ERC4ZTPNRBOBMH5ZDU6WQN2": (
        ["f_person_compound"],
        "'/ Hessisches Statistisches Landesamt ...' is a corporate body SoR; ';' separates topic subtitles, not persons"
    ),
    "HTZF42Z2NWHSNVQ4I24DVX4GIY3K6JGZ": (
        ["f_person_compound"],
        "'/ Statistisches Landesamt ...' is a corporate body SoR; ';' separates topic subtitles, not persons"
    ),
    "GZGSDYAOXUCMPMU4ET6UNPTBUGAVJQJG": (
        ["f_person_compound"],
        "';' after '/ Rietz' separates co-editors in a school textbook — actually these ARE persons (Rietz, Könitzer, Hopp). TP."
        # Wait, let me re-read: "Rechenbuch für Volksschulen ... / unter Mitw. von Rietz ; Könitzer ; Hopp"
        # Rietz, Könitzer, Hopp are persons → TP! Revert.
    ),
    "P575I6CUIEI6FU7QDM5ZH2DTBPOHTE72": (
        ["f_person_compound"],
        "'/ Hessisches Statistisches Landesamt ...' is a corporate body SoR; ';' separates topic subtitles, not persons"
    ),
    "5J44RTFJ7GCGZDSX4TUSC5JF4LKXIMUA": (
        ["f_person_compound"],
        "'/ Amt für Statistik Berlin-Brandenburg ...' is a corporate body SoR; ';' separates topic subtitles, not persons"
    ),
    "CMBIOT4LS3HCBMNJ5GL7NUUZA6PHVY2N": (
        # f_other_title=1 → TP; f_person=1 → TP ('/' = issuing body)
        # No f_person_compound set; check original data: f_person_compound=0 for this row
        [],
        ""
    ),

    # Fix GZGSDYAOXUCMPMU4ET6UNPTBUGAVJQJG — Rietz, Könitzer, Hopp are persons → TP
    # (I had a bug in the override above — set it to empty)
}

# Fix the GZGSDYAOXUCMPMU4ET6UNPTBUGAVJQJG entry (it's TP, not FP)
MANUAL_OVERRIDES["GZGSDYAOXUCMPMU4ET6UNPTBUGAVJQJG"] = ([], "")


# ─────────────────────────────────────────────────────────────────────────────
# Automated check functions (for rows NOT in MANUAL_OVERRIDES)
# ─────────────────────────────────────────────────────────────────────────────

def check_f_year(title: str) -> tuple[bool, str]:
    """Return (is_fp, reason) for f_year=1."""
    if re.search(r'\b(gegr\.|gestiftet|seit)\s+\d{4}', title, re.IGNORECASE):
        m = re.search(r'\b(gegr\.|gestiftet|seit)\s+(\d{4})', title, re.IGNORECASE)
        if m:
            return True, f"{m.group(2)} is founding year ({m.group(1)})"

    if re.search(r'\bvon Anno\s+\d{4}', title, re.IGNORECASE):
        m = re.search(r'von Anno\s+(\d{4})', title, re.IGNORECASE)
        if m:
            return True, f"{m.group(1)} is manuscript date range (von Anno)"

    comp_match = re.search(r'\b(geschrieben|verfaßt|verfasst)\s+\d{4}', title, re.IGNORECASE)
    if comp_match:
        yr_m = re.search(r'\b(geschrieben|verfaßt|verfasst)\s+(\d{4})', title, re.IGNORECASE)
        if yr_m:
            return True, f"{yr_m.group(2)} is composition year ({yr_m.group(1)})"

    if re.search(r'\d+\.\s+Jahr\s+(ihres|seines)\s+Alters', title, re.IGNORECASE):
        return True, "year is biographical date (im X. Jahr ihres/seines Alters context), not publication year"

    # Life/death date range after person name: ':YYYY-YYYY' or '(YYYY - YYYY)'
    if re.search(r':\s*\d{4}\s*[-–]\s*\d{4}', title):
        m = re.search(r':\s*(\d{4})\s*[-–]\s*(\d{4})', title)
        if m:
            return True, f"{m.group(1)}–{m.group(2)} are life dates after colon, not publication year"

    if re.search(r'\(\d{4}\s*[-–]\s*\d{4}\)', title):
        m = re.search(r'\((\d{4})\s*[-–]\s*(\d{4})\)', title)
        if m:
            return True, f"{m.group(1)}–{m.group(2)} are life dates in parentheses, not publication year"

    return False, ""


def check_f_other_title(title: str) -> tuple[bool, str]:
    """Return (is_fp, reason) for f_other_title=1 (fires on ' :')."""
    if re.search(r'\s:\s*\d{4}\s*[-–]\s*\d{4}', title):
        m = re.search(r'\s:\s*(\d{4})\s*[-–]\s*(\d{4})', title)
        if m:
            return True, f"':' precedes life dates {m.group(1)}–{m.group(2)}, not ISBD subtitle"

    if " :: " in title:
        return True, "':' is part of '::' catalog-record field separator, not ISBD subtitle"

    return False, ""


def check_f_person(title: str) -> tuple[bool, str]:
    """Return (is_fp, reason) for f_person=1 (fires on ' /')."""
    # FP if the only slash(es) are in numeric contexts (fractions, ratios, date ranges)
    if re.search(r'\d/\d', title):
        slashes = list(re.finditer(r'/', title))
        numeric_slashes = list(re.finditer(r'\d/\d', title))
        # Only mark FP if there are no non-numeric slashes
        non_numeric = [s for s in slashes if not any(
            abs(s.start() - n.start()) <= 1 for n in numeric_slashes
        )]
        if not non_numeric:
            m = re.search(r'(\d+)/(\d+)', title)
            return True, f"'{m.group(0)}' is a numeric fraction/ratio, not a person SoR separator"
    return False, ""


def check_f_person_compound(title: str) -> tuple[bool, str]:
    """Return (is_fp, reason) for f_person_compound=1."""
    if re.search(r'\d/\d', title):
        slashes = list(re.finditer(r'/', title))
        numeric_slashes = list(re.finditer(r'\d/\d', title))
        non_numeric = [s for s in slashes if not any(
            abs(s.start() - n.start()) <= 1 for n in numeric_slashes
        )]
        if not non_numeric:
            m = re.search(r'(\d+)/(\d+)', title)
            return True, f"'{m.group(0)}' is numeric, not a person compound SoR"
    return False, ""


def check_f_parallel(title: str) -> tuple[bool, str]:
    """Return (is_fp, reason) for f_parallel=1 (fires on ' =')."""
    enum_pattern = re.compile(
        r'\s=\s*(Jg\.|Nr\.|N\.F\.|Bd\.|Abt\.|St\.\s+\d|Stück\s+\d|Stück\b|'
        r'Quartal|Winter|Sommer|Frühjahr|Herbst|Jan|Feb|März|Apr|Mai|Jun|Jul|Aug|Sep|Okt|Nov|Dez)',
        re.IGNORECASE
    )
    if enum_pattern.search(title):
        m = enum_pattern.search(title)
        return True, f"'=' introduces enumeration designator ({m.group(1).strip()}), not a parallel title"
    return False, ""


def check_f_edition(title: str) -> tuple[bool, str]:
    """Return (is_fp, reason) for f_edition=1."""
    if re.search(r'\bAusgabe\s+vom\b', title, re.IGNORECASE):
        return True, "'Ausgabe vom ...' is a newspaper issue date label, not an edition statement"
    return False, ""


def check_f_series(title: str) -> tuple[bool, str]:
    """Return (is_fp, reason) for f_series=1."""
    if re.search(r'\(Beschluss\s+von\s+Nr\.?\s*\d', title, re.IGNORECASE):
        return True, "parenthetical '(Beschluss von Nr. X)' is an editorial continuation note, not a series"
    if re.search(r'\(Fortsetzung\b', title, re.IGNORECASE):
        return True, "parenthetical '(Fortsetzung...)' is an editorial continuation note, not a series"
    return False, ""


def check_f_publisher(title: str) -> tuple[bool, str]:
    return False, ""


def check_f_volume(title: str) -> tuple[bool, str]:
    return False, ""


# ─────────────────────────────────────────────────────────────────────────────
# Main processing loop
# ─────────────────────────────────────────────────────────────────────────────

flag_cols = ["f_other_title", "f_person", "f_person_compound", "f_parallel",
             "f_edition", "f_year", "f_publisher", "f_series", "f_volume"]

for idx, row in df.iterrows():
    obj_id = row["obj_id"]
    title = row["title"]

    if obj_id in MANUAL_OVERRIDES:
        fp_list, notes_str = MANUAL_OVERRIDES[obj_id]
        df.at[idx, "fp_fields"] = ",".join(fp_list)
        df.at[idx, "notes"] = notes_str
        continue

    fp_list = []
    notes_list = []

    if row["f_other_title"] == "1":
        is_fp, reason = check_f_other_title(title)
        if is_fp:
            fp_list.append("f_other_title"); notes_list.append(reason)

    if row["f_person"] == "1":
        is_fp, reason = check_f_person(title)
        if is_fp:
            fp_list.append("f_person"); notes_list.append(reason)

    if row["f_person_compound"] == "1":
        is_fp, reason = check_f_person_compound(title)
        if is_fp:
            fp_list.append("f_person_compound"); notes_list.append(reason)

    if row["f_parallel"] == "1":
        is_fp, reason = check_f_parallel(title)
        if is_fp:
            fp_list.append("f_parallel"); notes_list.append(reason)

    if row["f_edition"] == "1":
        is_fp, reason = check_f_edition(title)
        if is_fp:
            fp_list.append("f_edition"); notes_list.append(reason)

    if row["f_year"] == "1":
        is_fp, reason = check_f_year(title)
        if is_fp:
            fp_list.append("f_year"); notes_list.append(reason)

    if row["f_publisher"] == "1":
        is_fp, reason = check_f_publisher(title)
        if is_fp:
            fp_list.append("f_publisher"); notes_list.append(reason)

    if row["f_series"] == "1":
        is_fp, reason = check_f_series(title)
        if is_fp:
            fp_list.append("f_series"); notes_list.append(reason)

    if row["f_volume"] == "1":
        is_fp, reason = check_f_volume(title)
        if is_fp:
            fp_list.append("f_volume"); notes_list.append(reason)

    df.at[idx, "fp_fields"] = ",".join(fp_list)
    df.at[idx, "notes"] = "; ".join(notes_list)


# ─────────────────────────────────────────────────────────────────────────────
# Write back
# ─────────────────────────────────────────────────────────────────────────────

df.to_csv(CSV_PATH, index=False)
print(f"Written {len(df)} rows to {CSV_PATH}")

has_fp = (df["fp_fields"] != "").sum()
print(f"\nRecords with at least one FP: {has_fp} / {len(df)}")

print("\nFP counts per field:")
for col in flag_cols:
    count = df["fp_fields"].str.contains(col, regex=False).sum()
    if count > 0:
        print(f"  {col}: {count}")

print("\n─── FP Records ───")
fp_rows = df[df["fp_fields"] != ""][["obj_id", "title", "fp_fields", "notes"]]
for _, r in fp_rows.iterrows():
    print(f"\n  obj_id: {r['obj_id']}")
    print(f"  title: {r['title'][:120]}")
    print(f"  fp_fields: {r['fp_fields']}")
    print(f"  notes: {r['notes']}")
