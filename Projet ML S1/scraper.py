"""
scraper.py - Scraping du dictionnaire depuis tenymalagasy.org
Stratégie : on parcourt les pages alphabétiques A-Z du site
et on extrait mot + définition.
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import os

BASE_URL = "https://tenymalagasy.org/bins/tenyR2.cgi"
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "data", "dictionary.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Educational Bot - ISPM Machine Learning Project)"
}

def scrape_letter(letter: str) -> dict:
    """
    Scrape tous les mots commençant par une lettre donnée.
    Retourne un dict {mot: définition}.
    """
    words = {}
    page = 1

    while True:
        # Le site utilise des paramètres GET pour filtrer par lettre
        params = {
            "tam": "sofina",
            "L1": letter.upper(),
            "page": page
        }

        try:
            response = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"  Erreur réseau pour '{letter}' page {page}: {e}")
            break

        soup = BeautifulSoup(response.text, "html.parser")

        # Cherche les entrées du dictionnaire
        # Structure typique : <div class="entry"> ou <tr> avec mot + définition
        entries = soup.find_all("div", class_="entry")
        if not entries:
            # Fallback: chercher dans les tableaux
            entries = soup.find_all("tr")

        if not entries:
            break

        count = 0
        for entry in entries:
            try:
                # Essai de récupérer le mot (titre/header de l'entrée)
                word_tag = entry.find("span", class_="mot") or entry.find("td", class_="mot")
                def_tag = entry.find("span", class_="def") or entry.find("td", class_="def")

                if not word_tag:
                    # Fallback : première colonne = mot, deuxième = définition
                    cols = entry.find_all("td")
                    if len(cols) >= 2:
                        word_tag = cols[0]
                        def_tag = cols[1]

                if word_tag:
                    word = word_tag.get_text(strip=True).lower()
                    definition = def_tag.get_text(strip=True) if def_tag else ""
                    if word and len(word) > 1:
                        words[word] = definition
                        count += 1
            except Exception:
                continue

        print(f"  Lettre '{letter}' page {page}: {count} mots trouvés")

        # Vérifier s'il y a une page suivante
        next_btn = soup.find("a", string=lambda t: t and ("suiv" in t.lower() or "next" in t.lower() or ">" in t))
        if not next_btn or count == 0:
            break

        page += 1
        time.sleep(0.5)  # Respecter le serveur

    return words


def scrape_all(letters=None, max_words=5000) -> dict:
    """
    Scrape le dictionnaire complet (ou partiel pour aller vite).
    Pour gagner du temps en TP, on peut limiter à quelques lettres.
    """
    if letters is None:
        # Lettres les plus fréquentes en malagasy d'abord
        letters = list("abdefhiklmnoprstvy")

    full_dict = {}

    for letter in letters:
        print(f"Scraping lettre: {letter.upper()}")
        words = scrape_letter(letter)
        full_dict.update(words)
        print(f"  Total cumulé: {len(full_dict)} mots")

        if len(full_dict) >= max_words:
            print(f"Limite de {max_words} mots atteinte, arrêt du scraping.")
            break

        time.sleep(1)

    return full_dict


def fallback_builtin_dictionary() -> dict:
    """
    Dictionnaire minimal intégré au cas où le scraping échoue.
    Suffisant pour les démonstrations.
    """
    return {
        "teny": "mot, langage, parole",
        "fitiavana": "amour, affection",
        "ankizy": "enfants",
        "ray": "père",
        "reny": "mère",
        "fianakaviana": "famille",
        "tokantrano": "foyer, maison",
        "nahita": "a vu, a trouvé",
        "manao": "faire, dit",
        "mianatra": "apprendre, étudier",
        "mpianatra": "étudiant, élève",
        "sekoly": "école",
        "boky": "livre",
        "fanorona": "jeu traditionnel malgache",
        "vary": "riz",
        "hena": "viande",
        "rano": "eau",
        "tany": "terre, pays, sol",
        "lanitra": "ciel",
        "andro": "jour, soleil, temps",
        "alina": "nuit",
        "maraina": "matin",
        "hariva": "soir",
        "izao": "ceci, maintenant",
        "izany": "cela",
        "eny": "oui",
        "tsia": "non",
        "misaotra": "merci",
        "azafady": "s'il vous plaît, pardon",
        "salama": "bonjour, bonne santé",
        "veloma": "au revoir",
        "inona": "quoi, qu'est-ce que",
        "aiza": "où",
        "oviana": "quand",
        "firy": "combien",
        "iza": "qui",
        "malagasy": "malgache, langue malgache",
        "madagasikara": "Madagascar",
        "antananarivo": "capitale de Madagascar",
        "toamasina": "ville côtière de Madagascar",
        "mahitsy": "droit, direct",
        "mahasoa": "qui fait du bien, bénéfique",
        "mahafinaritra": "agréable, plaisant",
        "tsara": "bien, beau, bon",
        "ratsy": "mauvais, méchant",
        "lehibe": "grand, important, adulte",
        "kely": "petit, peu",
        "maro": "beaucoup, nombreux",
        "vitsy": "peu nombreux, rare",
        "mafy": "dur, fort, difficile",
        "mora": "facile, doux, bon marché",
        "haingana": "vite, rapide",
        "moramora": "doucement, lentement",
        "mandeha": "aller, marcher",
        "mipetraka": "habiter, s'asseoir",
        "miasa": "travailler",
        "matory": "dormir",
        "mihinana": "manger",
        "misotro": "boire",
        "miteny": "parler",
        "mihaino": "écouter",
        "mijery": "regarder",
        "mahalala": "savoir, connaître",
        "tia": "aimer",
        "mahafoy": "sacrifier, renoncer",
        "matoky": "faire confiance, croire",
        "mifaly": "se réjouir, être heureux",
        "malahelo": "triste",
        "tezitra": "en colère",
        "tahotra": "peur",
        "fanantenana": "espoir",
        "fahalalana": "connaissance, savoir",
        "fahendrena": "sagesse",
        "hevitra": "idée, opinion, pensée",
        "saina": "esprit, intelligence",
        "fo": "cœur",
        "tanana": "main, village",
        "tongotra": "pied, jambe",
        "loha": "tête",
        "maso": "œil, yeux",
        "sofina": "oreille",
        "vava": "bouche",
        "nify": "dent",
        "volon-doha": "cheveux",
        "vatana": "corps",
        "afo": "feu",
        "rivotra": "vent, air",
        "ranomasina": "mer, océan",
        "ala": "forêt",
        "tendrombohitra": "montagne",
        "lalana": "chemin, rue, loi",
        "trano": "maison, bâtiment",
        "fiara": "voiture",
        "lamasinina": "train",
        "sambo": "bateau, navire",
        "fiaramanidina": "avion",
        "vola": "argent",
        "vidiny": "prix",
        "tsena": "marché",
        "fanjakana": "gouvernement, état",
        "lalàna": "loi, règle",
        "fitsarana": "tribunal, jugement",
        "mpitsara": "juge",
        "polisy": "police",
        "dokotera": "médecin, docteur",
        "hopitaly": "hôpital",
        "fanafody": "médicament, remède",
        "aretina": "maladie",
        "fahasalamana": "santé",
        "fanabeazana": "éducation",
        "mpampianatra": "enseignant, professeur",
        "siansa": "science",
        "teknika": "technique",
        "informatika": "informatique",
        "fitaovana": "outil, équipement",
        "milina": "machine",
        "solosaina": "ordinateur",
        "finday": "téléphone portable",
        "aterineto": "internet",
        "gazety": "journal",
        "radio": "radio",
        "fahitalavitra": "télévision",
    }


def save_dictionary(words: dict, path: str = OUTPUT_PATH):
    """Sauvegarde le dictionnaire en JSON."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(words, f, ensure_ascii=False, indent=2)
    print(f"Dictionnaire sauvegardé: {len(words)} mots -> {path}")


def load_or_scrape(force_scrape=False) -> dict:
    """
    Charge le dictionnaire depuis le fichier JSON si existant,
    sinon lance le scraping (ou utilise le dictionnaire intégré).
    """
    if not force_scrape and os.path.exists(OUTPUT_PATH):
        with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"Dictionnaire chargé: {len(data)} mots")
        return data

    print("Lancement du scraping (peut prendre quelques minutes)...")
    try:
        # Scraping limité aux lettres les plus fréquentes pour gagner du temps
        words = scrape_all(letters=list("abfhilmnrst"), max_words=3000)
        if len(words) < 100:
            raise ValueError("Trop peu de mots scrapés, utilisation du dictionnaire intégré")
    except Exception as e:
        print(f"Scraping échoué ({e}), utilisation du dictionnaire intégré.")
        words = fallback_builtin_dictionary()

    # Toujours enrichir avec le dictionnaire intégré
    builtin = fallback_builtin_dictionary()
    builtin.update(words)  # Le scrapé écrase le built-in si conflit
    words = builtin

    save_dictionary(words)
    return words


if __name__ == "__main__":
    # Lancer directement ce fichier pour construire le dictionnaire
    words = load_or_scrape(force_scrape=True)
    print(f"\n✅ Dictionnaire prêt: {len(words)} mots")
    # Afficher quelques exemples
    for w, d in list(words.items())[:5]:
        print(f"  {w}: {d}")
