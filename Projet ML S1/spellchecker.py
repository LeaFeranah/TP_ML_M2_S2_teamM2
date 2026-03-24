"""
spellchecker.py - Correcteur orthographique malagasy
Techniques:
  1. Distance de Levenshtein (via rapidfuzz)
  2. Règles phonotactiques malagasy (combinaisons interdites)
  3. Vérification de préfixes/suffixes valides
"""

import re
from typing import List, Tuple

# Try rapidfuzz first (faster), fallback to pure Python
try:
    from rapidfuzz.distance import Levenshtein
    def levenshtein_distance(a: str, b: str) -> int:
        return Levenshtein.distance(a, b)
except ImportError:
    def levenshtein_distance(a: str, b: str) -> int:
        """Pure Python Levenshtein - no dependencies needed."""
        m, n = len(a), len(b)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                cost = 0 if a[i-1] == b[j-1] else 1
                dp[i][j] = min(dp[i-1][j] + 1, dp[i][j-1] + 1, dp[i-1][j-1] + cost)
        return dp[m][n]


# ─── Règles phonotactiques malagasy ─────────────────────────────────────────

# Combinaisons de consonnes INTERDITES en malagasy
FORBIDDEN_CLUSTERS = [
    r'\bnb', r'\bmk', r'\bnk',   # Début de mot interdit
    r'dt', r'bp', r'sz',          # Partout interdit
    r'[bcdfghjklmnpqrstvwxyz]{4,}',  # 4 consonnes de suite (impossible)
]

# Voyelles en malagasy : a, e, i, o, y (y est voyelle !)
MALAGASY_VOWELS = set('aeiouy')

# Préfixes valides en malagasy
VALID_PREFIXES = [
    'mi', 'ma', 'man', 'mam', 'maha', 'mpan', 'mpam',
    'fi', 'fan', 'fam', 'an', 'am', 'i', 'o', 'ha', 'ka',
    'tsy', 'sy', 'no', 'dia', 'ka', 'fa'
]

# Suffixes valides
VALID_SUFFIXES = ['ana', 'ina', 'na', 'tra', 'ka', 'ny', 'ko', 'nao', 'nay', 'ntsika']


def check_phonotactics(word: str) -> List[str]:
    """
    Vérifie les règles phonotactiques malagasy.
    Retourne une liste d'erreurs trouvées (liste vide = OK).
    """
    errors = []
    w = word.lower()

    for pattern in FORBIDDEN_CLUSTERS:
        if re.search(pattern, w):
            errors.append(f"Combinaison interdite détectée: '{pattern}' dans '{word}'")

    # Un mot malagasy ne peut pas se terminer par certaines consonnes
    if w and w[-1] in 'bcdfgjklmpqrstvwxz':
        # Exception: certains mots empruntés (bus, taxi...)
        # On signale mais sans bloquer
        if len(w) > 3:  # Mots courts peuvent être des abbréviations
            errors.append(f"Le mot '{word}' se termine par une consonne inhabituelle en malagasy")

    return errors


def is_valid_word(word: str, dictionary: dict) -> bool:
    """Vérifie si un mot existe dans le dictionnaire."""
    return word.lower() in dictionary


def suggest_corrections(word: str, dictionary: dict, max_suggestions: int = 5, max_distance: int = 2) -> List[Tuple[str, int]]:
    """
    Propose des corrections pour un mot mal orthographié.
    Utilise Levenshtein avec optimisations:
    - Ne cherche que les mots de longueur similaire (±2)
    - Limite au top N suggestions
    Retourne: liste de (mot_suggéré, distance) triée par distance croissante
    """
    word_lower = word.lower()
    word_len = len(word_lower)
    suggestions = []

    for candidate in dictionary.keys():
        # Optimisation: ignorer les mots trop différents en longueur
        if abs(len(candidate) - word_len) > max_distance + 1:
            continue

        dist = levenshtein_distance(word_lower, candidate)
        if dist <= max_distance:
            suggestions.append((candidate, dist))

    # Trier par distance, puis alphabétiquement
    suggestions.sort(key=lambda x: (x[1], x[0]))
    return suggestions[:max_suggestions]


def check_text(text: str, dictionary: dict) -> List[dict]:
    """
    Analyse un texte complet et retourne les erreurs trouvées.
    Retourne une liste de dicts:
    {
        'word': mot_original,
        'position': (start, end),
        'type': 'spelling' | 'phonotactics',
        'message': description,
        'suggestions': [liste de corrections]
    }
    """
    errors = []

    # Tokenisation simple (mots séparés par espaces/ponctuation)
    word_pattern = re.compile(r'\b[a-zA-ZàâäéèêëîïôùûüÿçÀÂÄÉÈÊËÎÏÔÙÛÜŸÇ]+\b')

    for match in word_pattern.finditer(text):
        word = match.group()
        start, end = match.span()
        word_lower = word.lower()

        # 1. Vérification phonotactique
        phonotactic_errors = check_phonotactics(word)
        for err in phonotactic_errors:
            errors.append({
                'word': word,
                'position': (start, end),
                'type': 'phonotactics',
                'message': err,
                'suggestions': []
            })

        # 2. Vérification orthographique
        if not is_valid_word(word, dictionary):
            suggestions = suggest_corrections(word, dictionary)
            errors.append({
                'word': word,
                'position': (start, end),
                'type': 'spelling',
                'message': f"'{word}' n'est pas dans le dictionnaire malagasy",
                'suggestions': [s[0] for s in suggestions]
            })

    return errors


def get_word_info(word: str, dictionary: dict) -> dict:
    """
    Retourne les informations complètes sur un mot.
    """
    word_lower = word.lower()
    in_dict = word_lower in dictionary
    phonotactic_issues = check_phonotactics(word)

    result = {
        'word': word,
        'valid': in_dict and len(phonotactic_issues) == 0,
        'in_dictionary': in_dict,
        'definition': dictionary.get(word_lower, ''),
        'phonotactic_issues': phonotactic_issues,
    }

    if not in_dict:
        result['suggestions'] = suggest_corrections(word, dictionary)
    else:
        result['suggestions'] = []

    return result
