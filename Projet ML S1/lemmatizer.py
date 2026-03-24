"""
lemmatizer.py - Lemmatisation pour le malagasy
Stratégie hybride:
  1. Suppression des préfixes verbaux (mi-, ma-, man-, mam-...)
  2. Suppression des suffixes (-ana, -ina, -na, -tra...)
  3. Vérification que la racine existe dans le dictionnaire
  4. Tableau de correspondances manuelles pour les cas irréguliers
"""

import re
from typing import Optional, List

# ─── Tables de transformation ────────────────────────────────────────────────

# Préfixes ordonnés du plus long au plus court (pour éviter les faux positifs)
VERB_PREFIXES = [
    ('mpampian', 'mpampian'),  # mpampianatra -> ?
    ('mpan', ''),
    ('mpam', ''),
    ('mampian', ''),
    ('mampi', ''),
    ('mamp', ''),
    ('man', ''),
    ('mam', ''),
    ('maha', ''),
    ('mian', ''),
    ('miamp', ''),
    ('mia', ''),
    ('mi', ''),
    ('ma', ''),
    ('ha', ''),
    ('an', ''),
    ('am', ''),
    ('in', ''),
    ('im', ''),
    ('fi', ''),
    ('fa', ''),
    ('i', ''),
]

# Suffixes ordonnés du plus long au plus court
NOUN_SUFFIXES = [
    'ntsika', 'ndreo', 'areo', 'andro',
    'ana', 'ina', 'tra', 'ka', 'ny', 'na',
    'ko', 'nao', 'nay',
]

# Mutations consonantiques connues (préfixe + mutation)
# Par ex: man + tosika = manosika (t->os, nasalisation)
CONSONANT_MUTATIONS = {
    ('man', 't'): 'an',  # man + tosika -> manosika => tosika
    ('man', 's'): 'an',  # man + soratra -> manoratra => soratra
    ('man', 'f'): 'an',  # man + fanorona -> manorona => fanorona
    ('mam', 'b'): 'am',  # mam + baiko -> mambaiko => baiko
    ('mam', 'p'): 'am',  # mam + pitia -> mamitia => pitia
    ('mam', 'v'): 'am',  # mam + vidy -> mamidy => vidy
    ('man', 'd'): 'an',  # man + didy -> mandidy => didy
    ('man', 'j'): 'an',  # man + jahy -> manjahy => jahy
}

# Irréguliers connus (verb_form -> root)
IRREGULAR_LEMMAS = {
    'manosika': 'tosika',
    'manoratra': 'soratra',
    'mamaky': 'vakio',
    'mandefa': 'alefa',
    'mianatra': 'fianarana',
    'miasa': 'asa',
    'mihinana': 'hanina',
    'misotro': 'sotro',
    'miteny': 'teny',
    'mihaino': 'haino',
    'mijery': 'jery',
    'matory': 'tory',
    'mandeha': 'deha',
    'mipetraka': 'fipetraka',
    'mifaly': 'hafaliana',
    'mahalala': 'fahalalana',
    'mahafoy': 'foy',
    'matoky': 'toky',
    'mahasoa': 'soa',
    'mahafinaritra': 'finaritra',
    'mitondra': 'entina',
    'manome': 'omena',
}


def strip_prefix(word: str) -> List[str]:
    """
    Essaie de supprimer les préfixes verbaux.
    Retourne une liste de racines candidates.
    """
    candidates = []
    w = word.lower()

    for prefix, replacement in VERB_PREFIXES:
        if w.startswith(prefix):
            root = replacement + w[len(prefix):]
            if len(root) >= 3:  # Racine minimum 3 lettres
                candidates.append(root)

    return candidates


def strip_suffix(word: str) -> List[str]:
    """
    Essaie de supprimer les suffixes nominaux.
    Retourne une liste de racines candidates.
    """
    candidates = []
    w = word.lower()

    for suffix in NOUN_SUFFIXES:
        if w.endswith(suffix) and len(w) - len(suffix) >= 3:
            root = w[:-len(suffix)]
            candidates.append(root)

    return candidates


def lemmatize(word: str, dictionary: dict = None) -> dict:
    """
    Lemmatise un mot malagasy.
    Retourne: {
        'original': mot_original,
        'lemma': racine_trouvée,
        'method': méthode_utilisée,
        'definition': définition_si_trouvée
    }
    """
    word_lower = word.lower()

    # 1. Vérifier les irréguliers
    if word_lower in IRREGULAR_LEMMAS:
        root = IRREGULAR_LEMMAS[word_lower]
        definition = dictionary.get(root, '') if dictionary else ''
        return {
            'original': word,
            'lemma': root,
            'method': 'irregular_table',
            'definition': definition
        }

    # 2. Si le mot est déjà dans le dictionnaire, c'est lui-même la racine
    if dictionary and word_lower in dictionary:
        return {
            'original': word,
            'lemma': word_lower,
            'method': 'already_root',
            'definition': dictionary[word_lower]
        }

    # 3. Essai suppression de préfixe
    prefix_candidates = strip_prefix(word_lower)
    if dictionary:
        for candidate in prefix_candidates:
            if candidate in dictionary:
                return {
                    'original': word,
                    'lemma': candidate,
                    'method': 'prefix_stripping',
                    'definition': dictionary[candidate]
                }

    # 4. Essai suppression de suffixe
    suffix_candidates = strip_suffix(word_lower)
    if dictionary:
        for candidate in suffix_candidates:
            if candidate in dictionary:
                return {
                    'original': word,
                    'lemma': candidate,
                    'method': 'suffix_stripping',
                    'definition': dictionary[candidate]
                }

    # 5. Combinaison préfixe + suffixe
    for pre_cand in prefix_candidates:
        for suf in NOUN_SUFFIXES:
            if pre_cand.endswith(suf) and len(pre_cand) - len(suf) >= 3:
                combined = pre_cand[:-len(suf)]
                if dictionary and combined in dictionary:
                    return {
                        'original': word,
                        'lemma': combined,
                        'method': 'prefix_and_suffix_stripping',
                        'definition': dictionary[combined]
                    }

    # 6. Meilleur candidat sans vérification dict
    best = prefix_candidates[0] if prefix_candidates else word_lower
    return {
        'original': word,
        'lemma': best,
        'method': 'best_guess',
        'definition': ''
    }


def get_word_family(root: str, dictionary: dict) -> List[str]:
    """
    Trouve la famille de mots (mots partageant la même racine).
    Utile pour le chatbot assistant.
    """
    root_lower = root.lower()
    family = []

    for word in dictionary.keys():
        if root_lower in word and word != root_lower:
            family.append(word)
        elif len(root_lower) >= 4:
            lemma_result = lemmatize(word, dictionary)
            if lemma_result['lemma'] == root_lower:
                family.append(word)

    return family[:10]  # Limiter à 10 résultats


def get_verb_forms(root: str) -> List[dict]:
    """
    Génère les formes verbales probables d'une racine.
    Très utile pour le chatbot (demande de conjugaisons).
    """
    forms = []
    r = root.lower()

    # Active (mi-/man-/ma-)
    if r[0] in 'aeiou':
        forms.append({'form': f'mi{r}', 'type': 'actif', 'note': 'verbe actif (mi-)'})
    else:
        forms.append({'form': f'mi{r}', 'type': 'actif', 'note': 'verbe actif (mi-)'})
        forms.append({'form': f'ma{r}', 'type': 'actif_ma', 'note': 'verbe actif (ma-)'})

    # Passif (-ana, -ina)
    if r[-1] in 'aeiou':
        forms.append({'form': f'{r}na', 'type': 'passif', 'note': 'passif (-na)'})
    else:
        forms.append({'form': f'{r}ina', 'type': 'passif', 'note': 'passif (-ina)'})
        forms.append({'form': f'{r}ana', 'type': 'passif_circonstanciel', 'note': 'passif circonstanciel (-ana)'})

    # Nominalisé (fi-)
    forms.append({'form': f'fi{r}ana', 'type': 'nominal', 'note': 'nominalisation (fi-...ana)'})

    return forms
