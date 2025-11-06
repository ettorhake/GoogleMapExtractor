"""
Client Notion pour gérer la base de données de prospection
Crée la base de données et ajoute les entreprises automatiquement
"""

import logging
import time
from datetime import datetime
from notion_client import Client
from typing import List, Dict, Optional

class NotionProspectionClient:
    def __init__(self, config):
        """
        Initialise le client Notion avec la configuration
        """
        self.config = config
        self.notion_token = config['notion']['token']
        self.database_id = config['notion'].get('database_id')
        self.client = Client(auth=self.notion_token)
        self.setup_logging()
        
    def setup_logging(self):
        """Configure le logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def create_database(self, parent_page_id: str) -> Optional[str]:
        """
        Crée la base de données Notion pour la prospection
        """
        try:
            db_config = self.config['notion_database']
            
            # Structure des propriétés
            properties = {
                "Nom": {"title": {}},
                "Adresse": {"rich_text": {}},
                "Ville": {
                    "select": {
                        "options": [
                            {"name": "Paris", "color": "blue"},
                            {"name": "Lyon", "color": "green"},
                            {"name": "Marseille", "color": "orange"},
                            {"name": "Toulouse", "color": "purple"},
                            {"name": "Nice", "color": "pink"},
                            {"name": "Nantes", "color": "yellow"},
                            {"name": "Rennes", "color": "red"},
                            {"name": "Autre", "color": "gray"}
                        ]
                    }
                },
                "Téléphone": {"phone_number": {}},
                "Email": {"email": {}},
                "Site Web": {"url": {}},
                "Secteur": {
                    "select": {
                        "options": [
                            {"name": option, "color": "default"} 
                            for option in db_config['properties']['secteur']['options']
                        ]
                    }
                },
                "Statut": {
                    "select": {
                        "options": [
                            {"name": option, "color": self._get_status_color(option)} 
                            for option in db_config['properties']['statut']['options']
                        ]
                    }
                },
                "Note": {"number": {"format": "number"}},
                "Nb Avis": {"number": {"format": "number"}},
                "Date Ajout": {"date": {}},
                "Commentaires": {"rich_text": {}}
            }
            
            # Créer la base de données
            response = self.client.databases.create(
                parent={"page_id": parent_page_id},
                title=[{"type": "text", "text": {"content": db_config['title']}}],
                properties=properties
            )
            
            database_id = response["id"]
            self.database_id = database_id
            
            self.logger.info(f"Base de données créée avec l'ID : {database_id}")
            return database_id
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la création de la base de données : {e}")
            return None
    
    def _get_status_color(self, status: str) -> str:
        """
        Retourne la couleur appropriée pour chaque statut
        """
        color_map = {
            "À contacter": "red",
            "Contacté": "yellow", 
            "Réponse positive": "green",
            "Réponse négative": "gray",
            "Relance prévue": "orange",
            "Client potentiel": "blue"
        }
        return color_map.get(status, "default")
    
    def _get_or_create_ville_option(self, ville: str) -> str:
        """
        Retourne le nom de la ville ou 'Autre' si vide
        Note: Notion gère automatiquement les nouvelles options quand on les utilise
        """
        if not ville or ville.strip() == "":
            return "Autre"
        
        # Nettoyer la ville (enlever les codes postaux, etc.)
        ville_clean = ville.strip()
        if ville_clean.isdigit():  # Si c'est juste un code postal
            return "Autre"
        
        # Extraire la ville du texte complet si besoin
        # Ex: "35000 Rennes" -> "Rennes"
        parts = ville_clean.split()
        if len(parts) > 1 and parts[0].isdigit():
            ville_clean = " ".join(parts[1:])
        
        return ville_clean.title()  # Première lettre en majuscule
    
    def add_company(self, company_data: Dict) -> bool:
        """
        Ajoute une entreprise à la base de données
        """
        try:
            if not self.database_id:
                self.logger.error("Aucune base de données configurée")
                return False
            
            # Préparer les propriétés
            properties = {
                "Nom": {
                    "title": [{"type": "text", "text": {"content": company_data.get('nom', '')}}]
                },
                "Adresse": {
                    "rich_text": [{"type": "text", "text": {"content": company_data.get('adresse', '')}}]
                },
                "Ville": {
                    "select": {"name": self._get_or_create_ville_option(company_data.get('ville', 'Autre'))}
                },
                "Secteur": {
                    "select": {"name": company_data.get('secteur', 'Autre')}
                },
                "Statut": {
                    "select": {"name": "À contacter"}
                },
                "Date Ajout": {
                    "date": {"start": datetime.now().isoformat().split('T')[0]}
                }
            }
            
            # Ajouter les champs optionnels s'ils existent
            if company_data.get('telephone'):
                properties["Téléphone"] = {
                    "phone_number": company_data['telephone']
                }
            
            if company_data.get('site_web'):
                properties["Site Web"] = {
                    "url": company_data['site_web']
                }
            
            if company_data.get('note'):
                try:
                    note_value = float(str(company_data['note']).replace('/5', ''))
                    properties["Note"] = {"number": note_value}
                except (ValueError, TypeError):
                    pass
            
            if company_data.get('nb_avis'):
                try:
                    avis_value = int(company_data['nb_avis'])
                    properties["Nb Avis"] = {"number": avis_value}
                except (ValueError, TypeError):
                    pass
            
            # Créer la page dans la base de données
            response = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties
            )
            
            self.logger.info(f"Entreprise ajoutée : {company_data.get('nom', 'Nom inconnu')}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'ajout de l'entreprise : {e}")
            return False
    
    def add_companies_batch(self, companies: List[Dict]) -> Dict:
        """
        Ajoute plusieurs entreprises à la base de données
        """
        results = {
            'success': 0,
            'failed': 0,
            'total': len(companies)
        }
        
        self.logger.info(f"Ajout de {len(companies)} entreprises en cours...")
        
        for i, company in enumerate(companies):
            self.logger.info(f"Ajout {i+1}/{len(companies)} : {company.get('nom', 'Nom inconnu')}")
            
            if self.add_company(company):
                results['success'] += 1
            else:
                results['failed'] += 1
            
            # Pause pour éviter les limites de taux de l'API
            if i < len(companies) - 1:
                time.sleep(0.5)
        
        self.logger.info(f"Ajout terminé. Succès: {results['success']}, Échecs: {results['failed']}")
        return results
    
    def check_company_exists(self, company_name: str) -> bool:
        """
        Vérifie si une entreprise existe déjà dans la base
        """
        try:
            if not self.database_id:
                return False
            
            response = self.client.databases.query(
                database_id=self.database_id,
                filter={
                    "property": "Nom",
                    "title": {
                        "equals": company_name
                    }
                }
            )
            
            return len(response["results"]) > 0
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification : {e}")
            return False
    
    def update_company_status(self, company_name: str, new_status: str, comments: str = "") -> bool:
        """
        Met à jour le statut d'une entreprise
        """
        try:
            if not self.database_id:
                return False
            
            # Chercher l'entreprise
            response = self.client.databases.query(
                database_id=self.database_id,
                filter={
                    "property": "Nom",
                    "title": {
                        "equals": company_name
                    }
                }
            )
            
            if not response["results"]:
                self.logger.warning(f"Entreprise '{company_name}' non trouvée")
                return False
            
            page_id = response["results"][0]["id"]
            
            # Préparer les propriétés à mettre à jour
            properties = {
                "Statut": {
                    "select": {"name": new_status}
                }
            }
            
            if comments:
                properties["Commentaires"] = {
                    "rich_text": [{"type": "text", "text": {"content": comments}}]
                }
            
            # Mettre à jour la page
            self.client.pages.update(
                page_id=page_id,
                properties=properties
            )
            
            self.logger.info(f"Statut mis à jour pour {company_name} : {new_status}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la mise à jour : {e}")
            return False
    
    def get_companies_by_status(self, status: str) -> List[Dict]:
        """
        Récupère les entreprises par statut
        """
        try:
            if not self.database_id:
                return []
            
            response = self.client.databases.query(
                database_id=self.database_id,
                filter={
                    "property": "Statut",
                    "select": {
                        "equals": status
                    }
                }
            )
            
            companies = []
            for page in response["results"]:
                properties = page["properties"]
                company = {
                    'id': page["id"],
                    'nom': self._extract_title(properties.get("Nom")),
                    'adresse': self._extract_rich_text(properties.get("Adresse")),
                    'ville': self._extract_select(properties.get("Ville")),
                    'telephone': self._extract_phone(properties.get("Téléphone")),
                    'email': self._extract_email(properties.get("Email")),
                    'site_web': self._extract_url(properties.get("Site Web")),
                    'secteur': self._extract_select(properties.get("Secteur")),
                    'statut': self._extract_select(properties.get("Statut")),
                    'date_ajout': self._extract_date(properties.get("Date Ajout"))
                }
                companies.append(company)
            
            return companies
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération : {e}")
            return []
    
    def _extract_title(self, prop):
        """Extrait le texte d'une propriété title"""
        if prop and prop.get("title"):
            return "".join([t["text"]["content"] for t in prop["title"]])
        return ""
    
    def _extract_rich_text(self, prop):
        """Extrait le texte d'une propriété rich_text"""
        if prop and prop.get("rich_text"):
            return "".join([t["text"]["content"] for t in prop["rich_text"]])
        return ""
    
    def _extract_phone(self, prop):
        """Extrait le numéro de téléphone"""
        if prop and prop.get("phone_number"):
            return prop["phone_number"]
        return ""
    
    def _extract_email(self, prop):
        """Extrait l'email"""
        if prop and prop.get("email"):
            return prop["email"]
        return ""
    
    def _extract_url(self, prop):
        """Extrait l'URL"""
        if prop and prop.get("url"):
            return prop["url"]
        return ""
    
    def _extract_select(self, prop):
        """Extrait la valeur d'un select"""
        if prop and prop.get("select") and prop["select"]:
            return prop["select"]["name"]
        return ""
    
    def _extract_date(self, prop):
        """Extrait la date"""
        if prop and prop.get("date") and prop["date"]:
            return prop["date"]["start"]
        return ""


if __name__ == "__main__":
    # Test du client Notion
    import yaml
    
    with open('../config/config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Remplacez par votre vraie configuration
    config['notion']['token'] = "YOUR_REAL_TOKEN"
    
    client = NotionProspectionClient(config)
    
    # Test d'ajout d'une entreprise
    test_company = {
        'nom': 'Test Agency',
        'adresse': '123 Test Street, Paris',
        'telephone': '+33123456789',
        'site_web': 'https://test-agency.com',
        'secteur': 'Agence UX/UI',
        'note': '4.5',
        'nb_avis': '25'
    }
    
    # Décommentez pour tester
    # client.add_company(test_company)
