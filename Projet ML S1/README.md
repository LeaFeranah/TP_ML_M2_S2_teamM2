# 🇲🇬 TenyAI — Éditeur de Texte Augmenté par l'IA pour le Malagasy
> Projet TP Machine Learning — Institut Supérieur Polytechnique de Madagascar (ISPM) — S1

---

##  Membres du groupe

| Nom | Rôle |
|-----|------|
| MAHATAMBELONIRINA Jessica Tinah n31 | Scraping & Dictionnaire |
| FERANA Lea Therese n35 | NLP Core (Spellcheck, Lemmatisation) |
| DIMBIMALALA Fanorenana n11 | NLP Avancé (N-grams, Sentiment, NER) |
| RAZANANNIRIN Felana Natalia n09 | Frontend & Intégration Flask |
| MIHANTAHARISOA Solange n28 |  Scraping & Dictionnaire |
| SITRAKINIAVO Harenjanahary Sarobidy n33 | NLP Core (Spellcheck, Lemmatisation) |
| RAZAFINDRAHANIRAKA Fitahiana Henintsoa n01 | Frontend & Intégration Flask |

---

##  Lancement rapide

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. (Optionnel) Construire le dictionnaire via scraping
cd backend
python scraper.py

# 3. Démarrer le serveur
python app.py

# 4. Ouvrir dans le navigateur
# http://localhost:5000
```

---

##  Fonctionnalités IA intégrées

### 1.  Correcteur Orthographique
- **Technique**: Distance de Levenshtein (via `rapidfuzz`) + dictionnaire scrapé
- **Règles phonotactiques**: Détection des combinaisons interdites (nb, mk, nk, dt, bp, sz)
- **Suggestions**: Top-5 corrections classées par distance

### 2.  Lemmatisation
- **Technique hybride**: Tables de règles (préfixes/suffixes) + irréguliers connus
- **Préfixes traités**: mi-, ma-, man-, mam-, maha-, mpan-, fi-, fan-...
- **Suffixes traités**: -ana, -ina, -na, -tra, -ka
- **Formes verbales**: Génération automatique des formes actives/passives

### 3.  Autocomplétion / Next Word Prediction
- **Technique**: Modèle N-gram (bigrams + trigrams) avec lissage par fréquences
- **Corpus**: Proverbes malagasy, phrases courantes (extensible avec Bible/Wikipedia)
- **Interface**: Dropdown interactif avec Tab/Entrée pour accepter

### 4.  Analyse de Sentiment
- **Technique**: Bag of Words avec listes de mots positifs/négatifs (200+ termes)
- **Améliorations**: Gestion des intensificateurs (tena, tokoa, indrindra) et négateurs (tsy, aza)
- **Output**: Label (positif/négatif/neutre) + score [-1, 1] + confiance

### 5.  Reconnaissance d'Entités (NER)
- **Technique**: Dictionnaire de noms propres + heuristique de capitalisation
- **Entités détectées**: Villes (50+ villes malagasy), Personnes (personnalités historiques), Organisations
- **Fallback**: Détection heuristique des mots capitalisés en milieu de phrase

### 6.  Traducteur Mot-à-Mot
- **Technique**: Lookup dans dictionnaire local + fallback via lemmatisation
- **Déclenchement**: Clic droit sur n'importe quel mot dans l'éditeur

### 7.  Chatbot Assistant
- **Technique**: Pattern matching sur l'intention + appel aux modules NLP
- **Capacités**: Synonymes, conjugaisons, définitions, racines, familles de mots

---

##  Stratégies Low-Resource

Le malagasy étant une Low Resource Language, nous avons utilisé:

1. **Approche symbolique** pour les règles phonotactiques (zéro donnée requise)
2. **Dictionnaire scrapé** de tenymalagasy.org comme base de connaissances
3. **Corpus intégré** de proverbes et phrases pour le N-gram (extensible)
4. **Tables de correspondances** manuelles pour la lemmatisation des irréguliers
5. **Listes de mots-clés** pour le sentiment (approche Bag of Words)
6. **Heuristiques linguistiques** (capitalisation, VSO word order) pour le NER

---

##  Architecture technique

```
malagasy-editor/
├── backend/
│   ├── app.py          # API REST Flask (8 routes)
│   ├── scraper.py      # Scraping tenymalagasy.org + dict intégré
│   ├── spellchecker.py # Levenshtein + règles phonotactiques
│   ├── lemmatizer.py   # Lemmatisation par règles
│   ├── ngram.py        # Modèle N-gram pour autocomplétion
│   └── sentiment_ner.py # Sentiment (BoW) + NER par dictionnaire
├── data/
│   └── dictionary.json # Dictionnaire généré au premier lancement
├── frontend/
│   └── index.html      # Interface éditeur (vanilla JS + CSS)
├── requirements.txt
└── README.md
```

---

##  Bibliographie & Sources de données

- **tenymalagasy.org** — Dictionnaire malagasy en ligne (scraping)
- **mg.wikipedia.org** — Wikipedia malagasy (~90k articles, API MediaWiki)
- **Ohabolana** — Proverbes malagasy (corpus intégré)
- Jurafsky, D. & Martin, J.H. — *Speech and Language Processing* (N-grams, NER)
- Levenshtein, V. — *Binary codes capable of correcting deletions, insertions, and reversals* (1966)
- rapidfuzz — https://github.com/maxbachmann/RapidFuzz
- Flask — https://flask.palletsprojects.com/

---

##  Évolutions prévues (avant 14 avril 2026)

- [ ] Intégration du corpus de la Bible en malagasy (Baiboly) pour enrichir les N-grams
- [ ] Scraping de Wikipedia MG pour un dictionnaire de 10 000+ mots
- [ ] Synthèse Vocale (TTS) avec gTTS pour lecture du texte
- [ ] Export du texte en PDF/DOCX
- [ ] Mode hors-ligne complet (PWA)
- [ ] Amélioration NER avec contexte de fenêtre glissante
