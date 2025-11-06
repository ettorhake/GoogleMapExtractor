"""
Interface web pour uploader des fichiers HTML Google Maps
et extraire automatiquement les entreprises vers Notion
"""

from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
import os
import uuid
import sys
from werkzeug.utils import secure_filename
from html_extractor import HTMLGoogleMapsExtractor as ProspectExtractor
import logging

# Configuration
app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Configuration du logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.propagate = False

# Créer un handler pour la console
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# Définir le format
formatter = logging.Formatter('%(message)s')
console_handler.setFormatter(formatter)

# Ajouter le handler au logger
logger.addHandler(console_handler)

# Désactiver les logs de Flask en production
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.WARNING)

# Créer le dossier uploads s'il n'existe pas
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Extensions autorisées
ALLOWED_EXTENSIONS = {'html', 'htm'}

def allowed_file(filename):
    """Vérifie si l'extension du fichier est autorisée"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Page d'accueil avec le formulaire d'upload"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Traite l'upload du fichier HTML et extrait les entreprises"""
    try:
        # Vérification qu'un fichier a été envoyé
        if 'file' not in request.files:
            return jsonify({'error': 'Aucun fichier sélectionné'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'Aucun fichier sélectionné'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Type de fichier non autorisé. Utilisez .html ou .htm'}), 400
        
        # Lecture du contenu pour vérification
        content = file.read()
        if not content:
            return jsonify({'error': 'Le fichier est vide'}), 400
            
        # Retour au début du fichier pour la sauvegarde
        file.seek(0)
        
        # Sauvegarde sécurisée du fichier
        if not file.filename:
            return jsonify({'error': 'Nom de fichier invalide'}), 400
            
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        
        # Vérification de la sauvegarde
        if os.path.getsize(filepath) == 0:
            return jsonify({'error': 'Erreur lors de la sauvegarde du fichier (fichier vide)'}), 500
        
        logger.info(f"Fichier sauvegardé ({os.path.getsize(filepath)} octets): {filepath}")
        
        # Récupération de la ville par défaut si fournie
        default_city = request.form.get('default_city', '').strip()
        if default_city:
            logger.info(f"Ville par défaut reçue: {default_city}")
            
        # Récupération du type d'entreprise par défaut si fourni
        default_business_type = request.form.get('default_business_type', '').strip()
        if default_business_type:
            logger.info(f"Type d'entreprise par défaut reçu: {default_business_type}")
        
        # Traitement du fichier avec l'extracteur
        extractor = ProspectExtractor()
        stats = extractor.process_html_file(filepath, 
                                          default_city=default_city if default_city else None,
                                          default_business_type=default_business_type if default_business_type else None)
        
        # Nettoyage du fichier temporaire seulement si l'extraction a réussi et trouvé des entreprises
        if stats and stats.get('success', 0) > 0:
            try:
                os.remove(filepath)
                logger.info(f"Fichier temporaire supprimé: {filepath}")
            except Exception as e:
                logger.warning(f"Impossible de supprimer le fichier temporaire: {e}")
        else:
            logger.info(f"Conservation du fichier temporaire pour debug: {filepath}")
        
        # Retour des résultats avec les mêmes clés que l'extracteur
        return jsonify({
            'success': True,
            'message': 'Fichier traité avec succès!',
            'stats': {
                'total': stats.get('total', 0),
                'success': stats.get('success', 0),
                'errors': stats.get('errors', 0),
                'duplicates': stats.get('duplicates', 0),
                'error_details': stats.get('error_details', [])
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement: {e}")
        return jsonify({'error': f'Erreur lors du traitement: {str(e)}'}), 500

@app.route('/status')
def status():
    """Vérifie le statut de la configuration Notion"""
    try:
        extractor = ProspectExtractor()
        # Test simple de connexion
        return jsonify({
            'notion_configured': bool(extractor.notion_token and extractor.database_id),
            'database_id': extractor.database_id[:8] + '...' if extractor.database_id else None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Démarrage de l'interface web...")
    print("📂 Ouvrez votre navigateur sur: http://localhost:5000")
    print("💡 Glissez-déposez vos fichiers HTML Google Maps pour les traiter")
    app.run(debug=True, host='0.0.0.0', port=5000)
