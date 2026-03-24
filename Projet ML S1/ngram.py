"""
ngram.py - Modèle N-gram pour l'autocomplétion (Next Word Prediction)
Stratégie:
  - Bigrams et trigrams entraînés sur corpus intégré
  - Fallback sur fréquences de mots si contexte inconnu
  - Corpus intégré: proverbes, phrases malagasy courantes
"""

import re
import json
import os
from collections import defaultdict, Counter
from typing import List, Tuple, Dict

# ─── Corpus malagasy intégré ─────────────────────────────────────────────────
# Phrases extraites de proverbes (ohabolana), textes courants
# Enrichir avec Bible/Wikipedia scraping si temps disponible

BUILTIN_CORPUS = """
ny fitiavana no valim-pitia
ny teny tsara manova fo
izay mianatra no mahita fahombiazana
ny ray aman-dreny no foto-pianarana
ny ankizy no haren'ny firenena
aza matahotra ny fahavalo fa matokia ny rariny
ny asa no ifampitsarana
ny fahendrena tsy vitan'ny vola
mianara aloha vao mampianatra
ny tany malagasy dia tany malalaka
izao no mahasoa ny firenena
manao ny asanao amim-pahamalinana
ny fiteny malagasy dia harena ho antsika
sorata tsara ny hevitrao
vakio ny boky mba hahalala bebe kokoa
ny mpianatra tsara no ho lasa mpampianatra
ny fianarana no lalana mankany amin'ny fahombiazana
ataovy tsara ny asanao isan'andro
ny malagasy dia olom-baovao
ny hevitra tsara dia tokony avela hiely
miasà maimbo andro sy alina
ny vola tsy manan-tompon
ny vary no sakafo malagasy
ny rano malagasy dia madio sy tsara
ny tany sy ny ala no harena voajanahary
mahafinaritra ny tontolo iainana
ny fanjakan'i madagasikara dia matanjaka
ny vahoaka malagasy dia matoria amin'ny rariny
mifampitia sy mifanajà
ny fihavanana no tena manan-danja
aza adino ny niaviaviana
ny tantara malagasy dia manan-karena
mitandrina ny fomban-drazana
ny trano malagasy dia misy kojakoja maro
ny hira malagasy dia mampifaly fo
mandinika tsara aloha vao manao
ny fahamarinana tsy maty
ny rariny no baikon'ny mpanao hevitra
miresaka amim-panajana amin'ny olona rehetra
ny fiehezan-tena no mampiavaka ny olona mahenina
tsara ny mahay miteny malagasy tsara
ny voambolana malagasy dia maro sy manan-karena
manoratra tsara ny teny malagasy
ny fitambarana no hery
mikambana mba hahazoana hery
ny firaisankina no mampiray firenena
soavaly tsara no mitondra ny mpitarika
ny firenena salama dia miankina amin'ny fahasalaman'ny vahoaka
andalio ny teny ratsy amin'ny firesahana
manaja ny elabe sy ny tanora
ny fifandraisana tsara no mampivelatra ny firenena
ataovy modely ny fitondrantenanao
izay mandresy lahatra no hahazo ny fandresena
ny tady lava dia mahafaoka be
ny harena tsy mitoetra amin'izay tsy mitandrina azy
omeo lanja ny asa kely sy ny asa lehibe
ny vonjy maika dia vonjy aina
azafady omeo ahy ny teny malagasy
misaotra anao noho ny fanampianao
salama tsara ianao androany
manana fanantenana ho amin'ny ho avy
ny toerana tsara dia eto antananarivo
mipetraka any toamasina izy
mandeha any fianarantsoa aho rahampitso
ny tanàna mahafinaritra eto madagasikara
ny siansa sy ny teknika dia manan-danja
ny informatika dia mahasoa ny fianakaviana
ny solosaina sy ny finday dia fitaovana mahasoa
ny aterineto dia manampy ny fianarana
vakio ny gazety isan'andro
mihaino radio malagasy isan'androany
ny fahitalavitra dia mampiseho vaovao
mahita vaovao vaovao isan'andro
ny dokotera malagasy dia mahay sy mpanompo
ny sekoly tsara no miteraka mpianatra tsara
ny hopitaly dia toerana fitsaboana
ny lalàna dia tokony hajaina amin'ny fomba rehetra
ny fanjakana dia manao ny tsara ho an'ny vahoaka
ny polisy dia miaro ny vahoaka
miasa mafy mba hahazoana vola ampy
ny tsena dia misy entana maro
ny vidiny dia misondrotra hatrany
ny fiara vaovao dia lafo vidiny
ny sambo lehibe dia mandeha any ranomasina
ny fiaramanidina dia haingana amin'ny dia lavitra
ny lamasinina dia mitondra olona maro
ny tendrombohitra malagasy dia avo sy mahafinaritra
ny ala malagasy dia misy biby maro
ny ranomasina dia misy trondro maro
ny afo malagasy dia afaka manafoana ny hafa
ny rivotra madio dia tsara ho an'ny fahasalaman
ny andro mahery dia mahasoa ny fambolena
ny alina mangina dia mahafinaritra ny torimaso
ny maraina mazava dia manome hery vaovao
ny hariva mitsitsy dia fotoana fialam-boly
"""


def tokenize(text: str) -> List[str]:
    """Tokenisation simple pour le malagasy."""
    # Lowercase et suppression de la ponctuation
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    tokens = text.split()
    # Filtrer les tokens trop courts
    return [t for t in tokens if len(t) >= 2]


def build_ngrams(tokens: List[str], n: int) -> Dict[tuple, Counter]:
    """
    Construit un modèle n-gram à partir d'une liste de tokens.
    Retourne un dict: {contexte_tuple: Counter{mot_suivant: count}}
    """
    model = defaultdict(Counter)

    for i in range(len(tokens) - n + 1):
        context = tuple(tokens[i:i+n-1])
        next_word = tokens[i+n-1]
        model[context][next_word] += 1

    return dict(model)


class NgramModel:
    def __init__(self):
        self.bigram_model = {}
        self.trigram_model = {}
        self.word_freq = Counter()
        self.vocabulary = set()
        self._trained = False

    def train(self, text: str = None):
        """Entraîne le modèle sur le corpus donné (ou le corpus intégré)."""
        corpus = (text or "") + "\n" + BUILTIN_CORPUS
        tokens = tokenize(corpus)

        self.word_freq = Counter(tokens)
        self.vocabulary = set(tokens)
        self.bigram_model = build_ngrams(tokens, 2)
        self.trigram_model = build_ngrams(tokens, 3)
        self._trained = True

        print(f"NgramModel entraîné: {len(tokens)} tokens, {len(self.vocabulary)} mots uniques")

    def train_from_file(self, filepath: str):
        """Entraîne depuis un fichier texte."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
            self.train(text)
        except FileNotFoundError:
            print(f"Fichier corpus non trouvé: {filepath}, utilisation corpus intégré")
            self.train()

    def predict_next(self, context_words: List[str], top_n: int = 5) -> List[Tuple[str, float]]:
        """
        Prédit les N mots suivants les plus probables.
        context_words: liste des derniers mots (1-2 mots de contexte)
        Retourne: [(mot, probabilité), ...]
        """
        if not self._trained:
            self.train()

        predictions = Counter()

        # Essai trigram (contexte de 2 mots)
        if len(context_words) >= 2:
            ctx = tuple(w.lower() for w in context_words[-2:])
            if ctx in self.trigram_model:
                total = sum(self.trigram_model[ctx].values())
                for word, count in self.trigram_model[ctx].most_common(top_n):
                    predictions[word] += count / total * 2.0  # Poids fort pour trigram

        # Essai bigram (contexte de 1 mot)
        if len(context_words) >= 1:
            ctx = (context_words[-1].lower(),)
            if ctx in self.bigram_model:
                total = sum(self.bigram_model[ctx].values())
                for word, count in self.bigram_model[ctx].most_common(top_n):
                    predictions[word] += count / total * 1.0  # Poids normal bigram

        # Fallback: mots les plus fréquents
        if not predictions:
            for word, count in self.word_freq.most_common(top_n * 2):
                total_words = sum(self.word_freq.values())
                predictions[word] = count / total_words * 0.1  # Poids faible

        # Normaliser et retourner
        results = [(word, score) for word, score in predictions.most_common(top_n)]
        return results

    def autocomplete_word(self, partial: str, top_n: int = 5) -> List[str]:
        """
        Autocomplétion d'un mot partiellement tapé.
        partial: début du mot (ex: "mian" -> ["mianatra", "miandrandra"...])
        """
        if not self._trained:
            self.train()

        partial_lower = partial.lower()
        matches = [
            word for word in self.vocabulary
            if word.startswith(partial_lower) and word != partial_lower
        ]

        # Trier par fréquence décroissante
        matches.sort(key=lambda w: self.word_freq.get(w, 0), reverse=True)
        return matches[:top_n]

    def get_suggestions(self, text: str, top_n: int = 5) -> dict:
        """
        Interface principale: donne suggestions de mot suivant ET autocomplétion.
        text: texte actuel de l'éditeur
        """
        tokens = tokenize(text)

        result = {
            'next_word': [],
            'autocomplete': []
        }

        if not tokens:
            return result

        last_word = tokens[-1] if tokens else ''

        # Si le texte se termine par un espace, prédire le mot suivant
        if text.endswith(' ') or text.endswith('\n'):
            result['next_word'] = [w for w, _ in self.predict_next(tokens, top_n)]
        else:
            # Sinon, autocompléter le mot en cours
            result['autocomplete'] = self.autocomplete_word(last_word, top_n)
            # Et aussi prédire pour contexte précédent
            if len(tokens) > 1:
                result['next_word'] = [w for w, _ in self.predict_next(tokens[:-1], top_n)]

        return result


# Instance globale (singleton)
_model_instance = None

def get_model() -> NgramModel:
    global _model_instance
    if _model_instance is None:
        _model_instance = NgramModel()
        # Essayer de charger un corpus externe
        corpus_path = os.path.join(os.path.dirname(__file__), 'data', 'corpus.txt')
        if os.path.exists(corpus_path):
            _model_instance.train_from_file(corpus_path)
        else:
            _model_instance.train()
    return _model_instance
