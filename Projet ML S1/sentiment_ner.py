"""
sentiment.py - Analyse de sentiment malagasy (Bag of Words)
ner.py - Reconnaissance d'entités nommées (villes, personnalités)
"""

import re
from typing import List, Dict

# ─── SENTIMENT ───────────────────────────────────────────────────────────────

POSITIVE_WORDS = {
    # Émotions positives
    'tsara', 'soa', 'mahafinaritra', 'faly', 'mifaly', 'hafaliana', 'fifaliana',
    'tiako', 'tiavina', 'fitiavana', 'fanantenana', 'amim-pifaliana',
    'mahita', 'fahombiazana', 'fandresena', 'maharitra', 'matanjaka',
    'hendry', 'fahendrena', 'tonga', 'mahasoa', 'vonjy', 'afaka',
    'salama', 'fahasalamana', 'mazava', 'taratra', 'mipoitra',
    'misaotra', 'veloma', 'mahasoa', 'manao', 'mahafoy',
    'matoky', 'toky', 'fiankinana', 'finoana', 'hery',
    'miray', 'firaisana', 'fihavanana', 'fifandraisana', 'fitahiana',
    'mahafinaritra', 'manan-danja', 'tena tsara', 'tena soa',
    'mahaly', 'mailo', 'mavitrika', 'mandroso', 'fandrosoana',
    'harena', 'fananana', 'ambony', 'lava', 'bebe',
    'mendrika', 'vonona', 'mahomby', 'miomana', 'tanteraka',
}

NEGATIVE_WORDS = {
    # Émotions négatives
    'ratsy', 'ratsibe', 'maloto', 'marary', 'aretina', 'tahotra',
    'malahelo', 'alahelo', 'ory', 'anjaka', 'fahoriana',
    'tezitra', 'hatezerana', 'sakana', 'fanavakavahana',
    'kotrana', 'misy olana', 'olana', 'osaosa', 'reraka',
    'fadiranovana', 'kivy', 'mahantra', 'fahantrana', 'ka',
    'mafy', 'zara', 'sarotra', 'marefo', 'reraka',
    'very', 'levona', 'ringana', 'simba', 'voa',
    'mihena', 'latsaka', 'mianjera', 'maty', 'fahafatesana',
    'heloka', 'ota', 'ratsy', 'mamitaka', 'vazivazy',
    'fanenjehana', 'fatratra', 'adin-tsaina', 'hadalana',
    'fadiranovana', 'mampiahiahy', 'sento', 'takaitra',
    'manafintohina', 'manohitra', 'manakana', 'misakana',
}

# Intensificateurs
INTENSIFIERS = {
    'tena': 1.5,       # vraiment
    'dia': 1.2,        # (particule d'intensité)
    'tokoa': 1.5,      # vraiment, certainement
    'indrindra': 1.8,  # surtout, particulièrement
    'be': 1.3,         # beaucoup
    'loatra': 1.4,     # trop
    'nohony': 0.8,     # un peu moins
}

# Négateurs
NEGATORS = {'tsy', 'tsia', 'aza', 'tsy misy'}


def analyze_sentiment(text: str) -> Dict:
    """
    Analyse le sentiment d'un texte malagasy.
    Retourne:
    {
        'label': 'positif' | 'négatif' | 'neutre',
        'score': float (-1.0 à 1.0),
        'positive_words': [...],
        'negative_words': [...],
        'confidence': float
    }
    """
    tokens = text.lower().split()

    positive_score = 0.0
    negative_score = 0.0
    found_positive = []
    found_negative = []

    i = 0
    while i < len(tokens):
        token = re.sub(r'[^\w]', '', tokens[i])

        # Vérifier si précédé d'un négateur (fenêtre de 1-2 mots)
        negated = False
        if i > 0 and re.sub(r'[^\w]', '', tokens[i-1]) in NEGATORS:
            negated = True
        if i > 1 and re.sub(r'[^\w]', '', tokens[i-2]) in NEGATORS:
            negated = True

        # Calculer le multiplicateur d'intensité
        intensifier = 1.0
        if i > 0 and tokens[i-1] in INTENSIFIERS:
            intensifier = INTENSIFIERS[tokens[i-1]]

        if token in POSITIVE_WORDS:
            contribution = intensifier
            if negated:
                negative_score += contribution * 0.7
                found_negative.append(f"tsy {token}")
            else:
                positive_score += contribution
                found_positive.append(token)

        elif token in NEGATIVE_WORDS:
            contribution = intensifier
            if negated:
                positive_score += contribution * 0.5
                found_positive.append(f"tsy {token}")
            else:
                negative_score += contribution
                found_negative.append(token)

        i += 1

    total = positive_score + negative_score
    if total == 0:
        score = 0.0
        confidence = 0.1
        label = 'neutre'
    else:
        score = (positive_score - negative_score) / total
        confidence = min(total / 5.0, 1.0)
        if score > 0.15:
            label = 'positif'
        elif score < -0.15:
            label = 'négatif'
        else:
            label = 'neutre'

    return {
        'label': label,
        'score': round(score, 3),
        'positive_words': found_positive,
        'negative_words': found_negative,
        'confidence': round(confidence, 3),
        'positive_count': len(found_positive),
        'negative_count': len(found_negative)
    }


# ─── NER (Named Entity Recognition) ────────────────────────────────────────

# Villes et lieux connus de Madagascar
CITIES = {
    'antananarivo', 'tana', 'tananarive',
    'toamasina', 'tamatave',
    'fianarantsoa', 'fiana',
    'mahajanga', 'majunga',
    'toliara', 'tuléar',
    'antsiranana', 'diégo',
    'antsirabe',
    'ambositra',
    'moramanga',
    'ambatondrazaka',
    'manakara',
    'farafangana',
    'fort-dauphin', 'taolanaro',
    'morondava',
    'maintirano',
    'tsiroanomandidy',
    'miarinarivo',
    'anjozorobe',
    'ambohidratrimo',
    'imerintsiatosika',
    'arivonimamo',
    'soavinandriana',
    'betafo',
    'mandoto',
    'miandrivazo',
    'malaimbandy',
    'manja',
    'belo tsiribihina',
    'nosy be', 'hellville',
    'sambava',
    'vohemar',
    'antalaha',
    'maroantsetra',
    'mananara',
    'fenoarivo atsinanana',
    'soanierana-ivongo',
    'vavatenina',
    'toamasina',
    'brickaville', 'ampasimanolotra',
    'vohipeno',
    'ikongo',
    'iakora',
    'ihosy',
    'betroka',
    'tsivory',
    'amboasary',
}

# Personnalités historiques malagasy connues
PERSONS = {
    'andrianampoinimerina', 'radama', 'radama i', 'radama ii',
    'ranavalona', 'rasoherina', 'ranavalona ii', 'ranavalona iii',
    'rainilaiarivoiny', 'rainimaharavo',
    'jean de la fontaine',  # Exemple non-malagasy
    'hery rajaonarimampianina', 'andry rajoelina', 'marc ravalomanana',
    'didier ratsiraka', 'philibert tsiranana',
    'gabriel razafimandimby',
}

# Organisations
ORGANIZATIONS = {
    'ispm', 'université d\'antananarivo', 'cnaps', 'jirama',
    'telma', 'orange', 'airtel', 'mvola',
    'banky foiben\'i madagasikara', 'bfm',
    'arema', 'tim', 'hvm', 'irmar',
}

# Indicateurs de personnes (titres)
PERSON_INDICATORS = {
    'andriana', 'mpanjaka', 'dokotera', 'profesora', 'mpampianatra',
    'ministre', 'filoha', 'prezidanta', 'governora', 'deotera',
    'andriamatoa', 'ramatoa', 'ralehibe',
}


def extract_entities(text: str) -> Dict:
    """
    Détecte les entités nommées dans le texte malagasy.
    Retourne:
    {
        'cities': [...],
        'persons': [...],
        'organizations': [...],
        'all_entities': [{'text': ..., 'type': ..., 'start': ..., 'end': ...}]
    }
    """
    text_lower = text.lower()
    entities = []
    found_cities = []
    found_persons = []
    found_orgs = []

    # Recherche des villes (insensible à la casse)
    for city in CITIES:
        pattern = re.compile(r'\b' + re.escape(city) + r'\b', re.IGNORECASE)
        for match in pattern.finditer(text):
            found_cities.append(match.group())
            entities.append({
                'text': match.group(),
                'type': 'VILLE',
                'start': match.start(),
                'end': match.end(),
                'normalized': city
            })

    # Recherche des personnes connues
    for person in PERSONS:
        pattern = re.compile(r'\b' + re.escape(person) + r'\b', re.IGNORECASE)
        for match in pattern.finditer(text):
            found_persons.append(match.group())
            entities.append({
                'text': match.group(),
                'type': 'PERSONNE',
                'start': match.start(),
                'end': match.end(),
                'normalized': person
            })

    # Recherche des organisations
    for org in ORGANIZATIONS:
        pattern = re.compile(r'\b' + re.escape(org) + r'\b', re.IGNORECASE)
        for match in pattern.finditer(text):
            found_orgs.append(match.group())
            entities.append({
                'text': match.group(),
                'type': 'ORGANISATION',
                'start': match.start(),
                'end': match.end(),
                'normalized': org
            })

    # Heuristique: mots capitalisés non en début de phrase = probables noms propres
    sentences = re.split(r'[.!?]\s+', text)
    for sentence in sentences:
        words_in_sentence = sentence.split()
        for j, word in enumerate(words_in_sentence):
            if j == 0:
                continue  # Ignorer le premier mot (toujours capitalisé)
            clean = re.sub(r'[^\w]', '', word)
            if clean and clean[0].isupper() and len(clean) > 2:
                # Vérifie que ce n'est pas déjà trouvé
                already_found = any(
                    e['text'].lower() == clean.lower() for e in entities
                )
                if not already_found:
                    # Trouver la position dans le texte original
                    match = re.search(r'\b' + re.escape(clean) + r'\b', text)
                    if match:
                        entities.append({
                            'text': clean,
                            'type': 'PROBABLE_NOM_PROPRE',
                            'start': match.start(),
                            'end': match.end(),
                            'normalized': clean.lower()
                        })

    # Trier par position
    entities.sort(key=lambda x: x['start'])

    return {
        'cities': list(set(found_cities)),
        'persons': list(set(found_persons)),
        'organizations': list(set(found_orgs)),
        'all_entities': entities,
        'entity_count': len(entities)
    }
