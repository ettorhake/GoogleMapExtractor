# Application d'Extraction de Prospects Google Maps

Cette application permet d'extraire les données de prospects depuis des fichiers HTML de Google Maps et de les importer dans Notion.

## Installation

1. Créer un environnement virtuel Python :
```bash
python -m venv venv
```

2. Activer l'environnement virtuel :
- Windows : `venv\Scripts\activate`
- Linux/Mac : `source venv/bin/activate`

3. Installer les dépendances :
```bash
pip install -r requirements.txt
```

## Configuration

1. Modifier le fichier `config/config.yaml` avec vos informations Notion :
```yaml
notion:
  token: "votre_token_notion"
  database_id: "votre_database_id"
```

## Utilisation

1. Lancer l'application :
```bash
python src/web_interface.py
```

2. Ouvrir votre navigateur sur : http://localhost:5000

3. Glisser-déposer un fichier HTML de Google Maps dans l'interface

4. Spécifier la ville si nécessaire

5. L'application extraira automatiquement les prospects et les importera dans Notion

## Structure des fichiers

- `src/web_interface.py` : Interface web Flask
- `src/html_extractor.py` : Moteur d'extraction HTML
- `src/notion_client.py` : Client Notion
- `src/templates/index.html` : Interface utilisateur
- `config/config.yaml` : Configuration
- `src/uploads/` : Dossier des fichiers uploadés
