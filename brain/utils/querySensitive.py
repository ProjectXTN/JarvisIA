import re

def is_query_time_sensitive(query):
    query = query.lower().strip()

    patterns = [
        # PRESIDENT / GOVERNOR / LEADER (pt/en/fr)
        r"presidente|president|président",
        r"governador|governor|gouverneur",
        r"primeiro[- ]ministro|prime minister|premier ministre",
        r"quem é o|who is|qui est",
        r"atual|current|actuel(le)?",
        r"novo|new|nouveau|nouvelle",
        r"elei[cç]([ãa]o|ões|on|ons)|election|élection",
        r"líder|leader|chef(fe)?",
        r"\b(202[3-9]|202\d|203\d)\b",

        # Temporal terms
        r"hoje|today|aujourd'hui",
        r"agora|now|maintenant",
        r"atualmente|currently|actuellement",
        r"recente|recent|récent",
        r"últim[oa]|latest|dernier|dernière|last",
        r"mudou|change[ds]?|changé|changement",
        r"not[ií]cia|news|nouvell(es)?|updates?|mise à jour",

        # PRICE / QUOTATION / VALUE / CURRENCY
        r"pre[cç]o|price|prix",
        r"cotação|quotation|quote|cours",
        r"d[óo]lar|dollar|euro|bitcoin|btc|real|usd|eur|coin",
        r"quanto custa|how much|combien (ça|cela)? coûte",

        # RESULT / WINNER / COMPETITION
        r"resultado|result|résultat",
        r"ganhou|venceu|won|gagné|victoire|winner",
        r"campe[aã]o|champion|champion(ne)?",
        r"finalista|finalist|finaliste",
        r"placar|score|score",
        r"p[oó]dio|podium",

        # RELEASES / NEW PRODUCTS
        r"lançamento|launch|lancement|sortie",
        r"quando sai|when does it (come|release)|quand (sort|sortira|sortie)",
        r"novo modelo|new model|nouveau modèle",
        r"dispon[ií]vel|available|disponible",

        # POLITICS, ECONOMY, REFORMS
        r"reforma|reform|réforme",
        r"lei|law|loi",
        r"pol[eê]mica|controversy|polémique",

        # GENERAL
        r"\bhoje\b|\bnow\b|\baujourd'hui\b|\bactuel(le)?\b|\bcurrent\b|\bactual\b",
        r"\búltim[oa]\b|\blatest\b|\bdernier|dernière\b|\blast\b|\brecent\b|\brécente?\b",
    ]

    for pat in patterns:
        if re.search(pat, query):
            return True

    return False
