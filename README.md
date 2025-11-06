# ProspectExtractor v1.0 🎯

Une application web Python puissante pour extraire automatiquement les informations de prospects depuis les pages Google Maps et les exporter directement vers Notion.

## 📸 Aperçu

### Interface d'Upload
![Interface d'upload](.github/images/interface.png)

### Base Notion
![Base de données Notion](.github/images/notion.png)

## ✨ Fonctionnalités

- 📋 Extraction automatique des données depuis les fichiers HTML Google Maps
- 🌐 Interface web conviviale pour le téléchargement des fichiers
- 📝 Saisie manuelle du type d'entreprise pour une meilleure catégorisation
- 🔄 Synchronisation automatique avec Notion
- 🏢 Support pour les informations d'entreprise incluant :
  - Nom de l'entreprise
  - Adresse complète
  - Numéro de téléphone
  - Site web
  - Type d'entreprise (personnalisable)
  - Ville

## 🚀 Installation

1. Cloner le dépôt :
```bash
git clone https://github.com/ettorhake/GoogleMapExtractor.git
cd GoogleMapExtractor
```

2. Créer et activer un environnement virtuel Python :
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. Installer les dépendances :
```bash
pip install -r requirements.txt
```

## ⚙️ Configuration

1. Copier le fichier de configuration exemple :
```bash
cp config/config.example.yaml config/config.yaml
```

2. Configurer votre intégration Notion :
   - Créer une intégration sur [Notion Developers](https://www.notion.so/my-integrations)
   - Copier le token d'intégration
   - Partager votre base de données Notion avec l'intégration
   - Copier l'ID de la base de données depuis son URL

3. Modifier `config/config.yaml` avec vos informations :
```yaml
notion:
  token: "votre_token_notion"
  database_id: "votre_database_id"
```

## 📖 Utilisation

1. Démarrer l'application :
```bash
# Windows
start.bat

# Linux/Mac
python src/web_interface.py
```

2. Accéder à l'interface web : http://localhost:5000

3. Pour extraire des prospects :
   - Ouvrir Google Maps et rechercher des entreprises
   - Enregistrer la page au format HTML (Ctrl+S ou Cmd+S)
   - Glisser-déposer le fichier HTML dans l'interface
   - Spécifier le type d'entreprise
   - Cliquer sur "Envoyer"

4. Les données seront automatiquement extraites et synchronisées avec votre base Notion

## 📁 Structure du Projet

```
ProspectExtractor/
├── config/
│   ├── config.example.yaml   # Configuration exemple
│   └── config.yaml          # Configuration réelle (non versionné)
├── src/
│   ├── templates/
│   │   └── index.html      # Interface utilisateur web
│   ├── uploads/            # Dossier de téléchargement temporaire
│   ├── html_extractor.py   # Logique d'extraction
│   ├── notion_client.py    # Client API Notion
│   └── web_interface.py    # Application Flask
├── .github/
│   └── images/            # Images pour la documentation
├── .gitignore
├── README.md
├── requirements.txt
└── start.bat              # Script de démarrage Windows
```

## 🔧 Prérequis Techniques

- Python 3.8+
- Compte Notion avec droits d'administrateur
- Navigateur web moderne

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
1. Fork le projet
2. Créer une branche (`git checkout -b feature/AmeliorationIncroyable`)
3. Commit vos changements (`git commit -m 'Ajout de fonctionnalités incroyables'`)
4. Push vers la branche (`git push origin feature/AmeliorationIncroyable`)
5. Ouvrir une Pull Request

## 📄 Licence

Ce projet est sous licence MIT - voir le fichier [LICENSE](LICENSE) pour plus de détails.

## ⭐ Support

Si vous trouvez ce projet utile, n'hésitez pas à lui donner une étoile sur GitHub !

## 📫 Contact

Pour toute question ou suggestion, n'hésitez pas à ouvrir une issue sur GitHub.
