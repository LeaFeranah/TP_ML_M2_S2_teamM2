"""
app.py - Backend Flask pour l'éditeur malagasy augmenté
Routes API disponibles:
  POST /api/spellcheck       - Correcteur orthographique
  POST /api/lemmatize        - Lemmatisation d'un mot
  POST /api/autocomplete     - Autocomplétion / next word
  POST /api/sentiment        - Analyse de sentiment
  POST /api/ner              - Reconnaissance d'entités
  POST /api/translate        - Traduction mot
  POST /api/chat             - Chatbot assistant
  GET  /api/status           - État du serveur
  GET  /                     - Interface web
"""

import os
import sys
import json
import io

# Ajouter le répertoire backend au path
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
try:
    from gtts import gTTS
    from gtts.lang import tts_langs
    GTTS_AVAILABLE = True
except ImportError:
    gTTS = None
    tts_langs = None
    GTTS_AVAILABLE = False

# Imports des modules NLP
from scraper import load_or_scrape
from spellchecker import check_text, get_word_info, suggest_corrections
from lemmatizer import lemmatize, get_verb_forms, get_word_family
from ngram import get_model
from sentiment_ner import analyze_sentiment, extract_entities

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)  # Permettre les requêtes cross-origin

# ─── Initialisation du dictionnaire et du modèle ─────────────────────────────

print("Chargement du dictionnaire...")
DICTIONARY = load_or_scrape()

print("Initialisation du modèle N-gram...")
NGRAM_MODEL = get_model()

print(f"Serveur pret - {len(DICTIONARY)} mots dans le dictionnaire")


# ─── Routes ──────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    """Sert l'interface web principale."""
    return send_from_directory('.', 'index.html')


@app.route('/api/status')
def status():
    """Vérifie l'état du serveur."""
    return jsonify({
        'status': 'ok',
        'dictionary_size': len(DICTIONARY),
        'ngram_trained': NGRAM_MODEL._trained,
        'vocabulary_size': len(NGRAM_MODEL.vocabulary)
    })


@app.route('/api/spellcheck', methods=['POST'])
def spellcheck():
    """
    Correcteur orthographique.
    Input: {"text": "texte à vérifier"}
    Output: {"errors": [...], "corrected_text": "..."}
    """
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'Champ "text" requis'}), 400

    text = data['text']
    errors = check_text(text, DICTIONARY)

    return jsonify({
        'errors': errors,
        'error_count': len(errors),
        'has_errors': len(errors) > 0
    })


@app.route('/api/wordinfo', methods=['POST'])
def word_info():
    """
    Informations complètes sur un mot.
    Input: {"word": "mianatra"}
    Output: {valid, definition, suggestions, phonotactic_issues}
    """
    data = request.get_json()
    if not data or 'word' not in data:
        return jsonify({'error': 'Champ "word" requis'}), 400

    word = data['word'].strip()
    info = get_word_info(word, DICTIONARY)
    return jsonify(info)


@app.route('/api/lemmatize', methods=['POST'])
def lemmatize_word():
    """
    Lemmatisation d'un mot.
    Input: {"word": "mianatra"}
    Output: {original, lemma, method, definition, verb_forms, word_family}
    """
    data = request.get_json()
    if not data or 'word' not in data:
        return jsonify({'error': 'Champ "word" requis'}), 400

    word = data['word'].strip()
    result = lemmatize(word, DICTIONARY)

    # Ajouter les formes verbales si racine trouvée
    result['verb_forms'] = get_verb_forms(result['lemma'])

    # Famille de mots
    result['word_family'] = get_word_family(result['lemma'], DICTIONARY)

    return jsonify(result)


@app.route('/api/autocomplete', methods=['POST'])
def autocomplete():
    """
    Autocomplétion et prédiction du mot suivant.
    Input: {"text": "ny fitiavana no "}
    Output: {next_word: [...], autocomplete: [...]}
    """
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'Champ "text" requis'}), 400

    text = data['text']
    suggestions = NGRAM_MODEL.get_suggestions(text, top_n=6)
    return jsonify(suggestions)


@app.route('/api/sentiment', methods=['POST'])
def sentiment():
    """
    Analyse de sentiment.
    Input: {"text": "mahafinaritra ny andro androany"}
    Output: {label, score, positive_words, negative_words, confidence}
    """
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'Champ "text" requis'}), 400

    text = data['text']
    result = analyze_sentiment(text)
    return jsonify(result)


@app.route('/api/ner', methods=['POST'])
def ner():
    """
    Reconnaissance d'entités nommées.
    Input: {"text": "Mandeha any Antananarivo aho rahampitso"}
    Output: {cities, persons, organizations, all_entities}
    """
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'Champ "text" requis'}), 400

    text = data['text']
    result = extract_entities(text)
    return jsonify(result)


@app.route('/api/translate', methods=['POST'])
def translate():
    """
    Traduction mot-à-mot (dictionnaire local).
    Input: {"word": "fitiavana", "direction": "mg_to_fr"}
    Output: {word, translation, definition}
    """
    data = request.get_json()
    if not data or 'word' not in data:
        return jsonify({'error': 'Champ "word" requis'}), 400

    word = data['word'].lower().strip()
    definition = DICTIONARY.get(word, '')

    if definition:
        return jsonify({
            'word': word,
            'translation': definition,
            'found': True,
            'source': 'dictionary'
        })
    else:
        # Essai lemmatisation avant traduction
        lemma_result = lemmatize(word, DICTIONARY)
        lemma = lemma_result['lemma']
        lemma_def = DICTIONARY.get(lemma, '')

        return jsonify({
            'word': word,
            'translation': lemma_def if lemma_def else 'Traduction non disponible',
            'found': bool(lemma_def),
            'source': 'lemma_dictionary',
            'lemma_used': lemma
        })


@app.route('/api/tts', methods=['POST'])
def tts():
    """
    Synthèse vocale (TTS) malagasy.
    Input: {"text": "mianatra"}
    Output: audio/mpeg (MP3)
    """
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'Champ "text" requis'}), 400

    if not GTTS_AVAILABLE:
        return jsonify({
            'error': "Synthèse vocale indisponible: gTTS non installé. "
                     "Installez-le avec 'pip install gTTS' ou utilisez le venv du projet."
        }), 503

    text = (data.get('text') or '').strip()
    if not text:
        return jsonify({'error': 'Texte vide'}), 400

    # Eviter les abus / payload trop gros
    if len(text) > 200:
        return jsonify({'error': 'Texte trop long (max 200 caractères)'}), 400

    # gTTS ne supporte pas forcément "mg" selon version; on fait un fallback.
    requested_lang = (data.get('lang') or 'mg').strip().lower()
    supported = tts_langs()
    fallback_order = [requested_lang, 'mg', 'fr', 'en']
    lang = next((l for l in fallback_order if l in supported), 'en')

    try:
        mp3_fp = io.BytesIO()
        tts_obj = gTTS(text=text, lang=lang)
        tts_obj.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        resp = Response(mp3_fp.read(), mimetype='audio/mpeg')
        resp.headers['X-TTS-Lang'] = lang
        return resp
    except Exception as e:
        return jsonify({'error': f'TTS indisponible: {str(e)}'}), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Chatbot assistant malagasy.
    Input: {"message": "synonymes de tsara", "context": [...]}
    Output: {response, suggestions}
    """
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'Champ "message" requis'}), 400

    message = data['message'].lower().strip()
    response = handle_chat(message)
    return jsonify(response)


def handle_chat(message: str) -> dict:
    """
    Logique du chatbot assistant.
    Analyse la question et répond de manière intelligente.
    """
    # Patterns de questions
    synonym_patterns = ['synonyme', 'synonymes', 'teny mitovy', 'hafa mitovy']
    conjugate_patterns = ['conjugaison', 'conjuguer', 'endri-teny', 'formes verbales', 'fiendrian-teny']
    define_patterns = ['définition', 'def', 'inona no', 'signification', 'midika']
    lemma_patterns = ['racine', 'origine', 'fototeny', 'lemmatiser']
    family_patterns = ['famille', 'fianakaviana', 'mots liés', 'teny mifandray']

    # Extraire le mot cible (dernier "mot important" de la question)
    words = message.split()
    target_word = words[-1] if words else ''

    # Nettoyer les mots de question courants
    stop_words = {'de', 'du', 'le', 'la', 'les', 'un', 'une', 'pour', 'avec',
                  'dans', 'sur', 'que', 'qui', 'quoi', 'comment', 'donne',
                  'moi', 'me', 'donner', 'avoir', 'les', 'des', 'synonymes',
                  'conjugaison', 'racine', 'famille'}
    content_words = [w for w in words if w not in stop_words and len(w) > 2]
    target_word = content_words[-1] if content_words else target_word

    # Détecter l'intention
    if any(p in message for p in synonym_patterns):
        # Synonymes via famille de mots + mots similaires dans le dict
        suggestions = suggest_corrections(target_word, DICTIONARY, max_suggestions=5, max_distance=1)
        family = get_word_family(target_word, DICTIONARY)
        definition = DICTIONARY.get(target_word, '')

        if definition:
            response_text = f"**{target_word}** signifie: {definition}\n\n"
        else:
            response_text = f"Voici des mots proches de **{target_word}**:\n\n"

        if family:
            response_text += "Famille de mots: " + ", ".join(family[:6])
        elif suggestions:
            response_text += "Mots similaires: " + ", ".join([s[0] for s in suggestions])
        else:
            response_text += "Aucun synonyme trouvé dans le dictionnaire actuel."

        return {'response': response_text, 'type': 'synonyms', 'target': target_word}

    elif any(p in message for p in conjugate_patterns):
        forms = get_verb_forms(target_word)
        lemma_result = lemmatize(target_word, DICTIONARY)
        root = lemma_result['lemma']
        verb_forms = get_verb_forms(root)

        response_text = f"Formes verbales de **{root}** (racine de '{target_word}'):\n\n"
        for form in verb_forms:
            response_text += f"• **{form['form']}** — {form['note']}\n"

        return {'response': response_text, 'type': 'conjugation', 'target': target_word, 'forms': verb_forms}

    elif any(p in message for p in define_patterns):
        definition = DICTIONARY.get(target_word, '')
        if not definition:
            lemma_result = lemmatize(target_word, DICTIONARY)
            definition = lemma_result.get('definition', '')
            if definition:
                response_text = f"**{target_word}** (racine: {lemma_result['lemma']}): {definition}"
            else:
                response_text = f"Définition de **{target_word}** non trouvée dans le dictionnaire."
        else:
            response_text = f"**{target_word}**: {definition}"

        return {'response': response_text, 'type': 'definition', 'target': target_word}

    elif any(p in message for p in lemma_patterns):
        result = lemmatize(target_word, DICTIONARY)
        response_text = (f"La racine (fototeny) de **{target_word}** est: **{result['lemma']}**\n"
                        f"Méthode: {result['method']}\n"
                        f"Définition: {result.get('definition', 'Non disponible')}")
        return {'response': response_text, 'type': 'lemma', 'target': target_word, 'lemma': result}

    elif any(p in message for p in family_patterns):
        family = get_word_family(target_word, DICTIONARY)
        if family:
            response_text = f"Famille de mots de **{target_word}**:\n" + "\n".join(f"• {w}" for w in family)
        else:
            response_text = f"Aucune famille de mots trouvée pour **{target_word}**."
        return {'response': response_text, 'type': 'family', 'target': target_word, 'family': family}

    else:
        # Réponse générique: définition + suggestions
        definition = DICTIONARY.get(target_word, '')
        suggestions = suggest_corrections(target_word, DICTIONARY, max_suggestions=3)

        if definition:
            response_text = f"**{target_word}**: {definition}"
        elif suggestions:
            response_text = (f"Je n'ai pas trouvé '{target_word}' exactement.\n"
                            f"Vouliez-vous dire: " + ", ".join([s[0] for s in suggestions]) + "?")
        else:
            response_text = ("Je peux vous aider avec:\n"
                           "• **synonymes de [mot]** - trouver des mots similaires\n"
                           "• **conjugaison de [mot]** - formes verbales\n"
                           "• **définition de [mot]** - signification\n"
                           "• **racine de [mot]** - trouver le fototeny\n"
                           "• **famille de [mot]** - mots de la même famille")

        return {'response': response_text, 'type': 'general', 'target': target_word}


@app.route('/api/full_analysis', methods=['POST'])
def full_analysis():
    """
    Analyse complète d'un texte (toutes fonctionnalités).
    Input: {"text": "..."}
    Output: {spellcheck, sentiment, ner, stats}
    """
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'Champ "text" requis'}), 400

    text = data['text']

    # Statistiques de base
    words = text.split()
    sentences = [s.strip() for s in text.replace('!', '.').replace('?', '.').split('.') if s.strip()]

    return jsonify({
        'spellcheck': check_text(text, DICTIONARY),
        'sentiment': analyze_sentiment(text),
        'ner': extract_entities(text),
        'stats': {
            'word_count': len(words),
            'sentence_count': len(sentences),
            'char_count': len(text),
            'avg_word_length': round(sum(len(w) for w in words) / len(words), 1) if words else 0
        }
    })


if __name__ == '__main__':
    print("\nDemarrage du serveur Editeur Malagasy Augmente")
    print("Interface: http://localhost:5000")
    print("API: http://localhost:5000/api/status\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
