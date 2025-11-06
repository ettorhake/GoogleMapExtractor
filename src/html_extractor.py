"""
Module d'extraction des données d'entreprises depuis le HTML de Google Maps
Remplace l'analyse par IA pour éviter les hallucinations
"""

import re
import yaml
from bs4 import BeautifulSoup
import json
from typing import List, Dict, Optional, Union
import logging
import requests
import sys

# Configuration du logging pour afficher dans la console
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Empêcher la propagation des logs au parent
logger.propagate = False

# Créer un handler pour la console
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# Définir le format
formatter = logging.Formatter('%(message)s')  # Format simplifié pour la console
console_handler.setFormatter(formatter)

# Ajouter le handler au logger
logger.addHandler(console_handler)

class HTMLGoogleMapsExtractor:
    def __init__(self, config_path: str = None):
        """Initialise l'extracteur HTML avec la configuration"""
        try:
            if config_path is None:
                # Utilise un chemin absolu par défaut
                import os
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                config_path = os.path.join(base_dir, 'config', 'config.yaml')
            
            with open(config_path, 'r', encoding='utf-8') as file:
                self.config = yaml.safe_load(file)
            
            # Configuration Notion
            self.notion_token = self.config['notion']['token']
            self.database_id = self.config['notion']['database_id']
            self.notion_url = f"https://api.notion.com/v1/pages"
            
            logger.info("Configuration chargée avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la configuration: {e}")
            raise

    def extract_businesses_from_html(self, html_content: str) -> List[Dict]:
        """
        Extrait les informations des entreprises depuis le HTML de Google Maps
        
        Args:
            html_content: Le contenu HTML de la page Google Maps
            
        Returns:
            Liste des entreprises avec leurs informations
        """
        businesses = []
        successful_extractions = 0
        failed_extractions = 0
        extraction_errors = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Trouver tous les conteneurs d'entreprises
            # Les entreprises sont dans des divs avec classe "Nv2PK tH5CWc THOPZb" ou "Nv2PK THOPZb"
            business_containers = soup.find_all('div', class_=re.compile(r'Nv2PK'))
            
            logger.info(f"Trouvé {len(business_containers)} conteneurs d'entreprises")
            
            # Afficher les classes trouvées pour débug
            if len(business_containers) == 0:
                logger.info("Analyse de la structure du HTML pour debug:")
                main_content = soup.find_all('div', class_='m6QErb')
                if main_content:
                    logger.info("Zone principale trouvée")
                    all_divs_with_class = soup.find_all('div', class_=True)
                    class_names = set()
                    for div in all_divs_with_class:
                        classes = div.get('class')
                        if classes:
                            class_names.update(classes)
                    logger.info(f"Classes trouvées dans le HTML: {', '.join(sorted(class_names))}")
                else:
                    logger.warning("Zone principale non trouvée - le HTML pourrait ne pas être au bon format")
            
            for container in business_containers:
                try:
                    business_data = self._extract_single_business(container)
                    if business_data:
                        businesses.append(business_data)
                        logger.info(f"✅ Extrait: {business_data.get('nom', 'Sans nom')}")
                        successful_extractions += 1
                    else:
                        failed_extractions += 1
                        extraction_errors.append("Données d'entreprise incomplètes")
                        
                except Exception as e:
                    failed_extractions += 1
                    error_msg = str(e)
                    extraction_errors.append(error_msg)
                    logger.warning(f"❌ Erreur lors de l'extraction d'une entreprise: {error_msg}")
                    continue
            
            logger.info(f"\n📊 Résumé de l'extraction:")
            logger.info(f"  ✅ Réussies: {successful_extractions}")
            logger.info(f"  ❌ Échouées: {failed_extractions}")
            
            if failed_extractions > 0:
                logger.info("\nDétail des erreurs d'extraction:")
                for i, error in enumerate(extraction_errors, 1):
                    logger.info(f"  {i}. {error}")
                    
            logger.info(f"\nTotal d'entreprises extraites: {len(businesses)}")
            return businesses
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction HTML: {e}")
            return []

    def _extract_single_business(self, container) -> Optional[Dict]:
        """
        Extrait les informations d'une seule entreprise depuis son conteneur HTML
        
        Args:
            container: L'élément BeautifulSoup du conteneur de l'entreprise
            
        Returns:
            Dictionnaire avec les informations de l'entreprise ou None
        """
        business = {}
        
        try:
            # Extraction du nom de l'entreprise
            name_element = container.find('div', class_=re.compile(r'qBF1Pd\s+fontHeadlineSmall'))
            if name_element:
                business['nom'] = name_element.get_text(strip=True)
            else:
                logger.warning("Nom d'entreprise non trouvé")
                return None
            
            # Extraction de la note et du nombre d'avis
            rating_container = container.find('span', class_=re.compile(r'ZkP5Je'))
            if rating_container:
                # Note
                rating_text = rating_container.find('span', class_='MW4etd')
                if rating_text:
                    try:
                        business['note'] = float(rating_text.get_text(strip=True).replace(',', '.'))
                    except:
                        business['note'] = None
                
                # Nombre d'avis
                reviews_text = rating_container.find('span', class_='UY7F9')
                if reviews_text:
                    reviews_str = reviews_text.get_text(strip=True)
                    reviews_match = re.search(r'\((\d+)\)', reviews_str)
                    if reviews_match:
                        business['nombre_avis'] = int(reviews_match.group(1))
            
            # Extraction du type d'entreprise et de l'adresse
            info_divs = container.find_all('div', class_='W4Efsd')
            for div in info_divs:
                text = div.get_text(strip=True)
                
                # On n'essaie plus de détecter le type d'entreprise automatiquement
                # car il sera fourni par l'interface
                
                # Adresse (chercher des patterns d'adresse)
                if any(keyword in text.lower() for keyword in ['rue', 'avenue', 'boulevard', 'place', 'bd']):
                    if '·' in text:
                        parts = text.split('·')
                        for part in parts:
                            part = part.strip()
                            if any(keyword in part.lower() for keyword in ['rue', 'avenue', 'boulevard', 'place', 'bd']):
                                business['adresse'] = part
                                # Extraction de la ville depuis l'adresse
                                business['ville'] = self._extract_city_from_address(part)
                                break
            
            # Extraction du téléphone
            phone_element = container.find('span', class_='UsdlK')
            if phone_element:
                business['telephone'] = phone_element.get_text(strip=True)
            
            # Extraction du site web
            website_link = container.find('a', class_=re.compile(r'lcr4fd\s+S9kvJb'))
            if website_link and website_link.get('href'):
                business['site_web'] = website_link.get('href')
            
            # Extraction des horaires/statut
            status_elements = container.find_all('span', style=True)
            for element in status_elements:
                style = element.get('style', '')
                text = element.get_text(strip=True)
                
                # Statut d'ouverture (rouge = fermé, vert = ouvert, orange = ferme bientôt)
                if 'color: rgba(220,54,46' in style and text:  # Rouge - Fermé
                    business['statut_ouverture'] = text
                elif 'color: rgba(25,134,57' in style and text:  # Vert - Ouvert
                    business['statut_ouverture'] = text
                elif 'color: rgba(178,108,0' in style and text:  # Orange - Ferme bientôt
                    business['statut_ouverture'] = text
            
            # Validation : au minimum le nom doit être présent
            if not business.get('nom'):
                return None
            
            # Ajout de champs par défaut
            business.setdefault('note', None)
            business.setdefault('nombre_avis', 0)
            # On utilise le type d'entreprise fourni par l'interface ou "Non spécifié"
            business['type_entreprise'] = self.default_business_type if hasattr(self, 'default_business_type') and self.default_business_type else 'Non spécifié'
            business.setdefault('adresse', 'Non spécifiée')
            business.setdefault('ville', 'Non spécifiée')
            business.setdefault('telephone', 'Non spécifié')
            business.setdefault('site_web', 'Non spécifié')
            business.setdefault('statut_ouverture', 'Non spécifié')
            
            return business
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction d'une entreprise: {e}")
            return None

    def _get_current_date(self) -> str:
        """
        Retourne la date actuelle au format ISO pour Notion
        
        Returns:
            Date actuelle au format YYYY-MM-DD
        """
        from datetime import date
        return date.today().isoformat()

    def _get_or_create_ville_option(self, ville: str) -> str:
        """
        Retourne le nom de la ville ou utilise la ville par défaut
        Note: Utilise d'abord la ville par défaut si définie
        """
        # Si une ville par défaut est définie, l'utiliser
        if hasattr(self, 'default_city') and self.default_city:
            return self.default_city.strip()
        
        if not ville or ville.strip() == "" or ville == "Non spécifiée":
            return "Non spécifiée"
        
        # Nettoyer la ville (enlever les codes postaux, etc.)
        ville_clean = ville.strip()
        if ville_clean.isdigit():  # Si c'est juste un code postal
            return "Non spécifiée"
        
        # Extraire la ville du texte complet si besoin
        # Ex: "35000 Rennes" -> "Rennes"
        parts = ville_clean.split()
        if len(parts) > 1 and parts[0].isdigit():
            ville_clean = " ".join(parts[1:])
        
        return ville_clean.title()  # Première lettre en majuscule
        
    def _get_or_create_business_type_option(self, business_type: str) -> dict:
        """
        Retourne le type d'entreprise formaté pour Notion
        
        Args:
            business_type: Type d'entreprise à formater
            
        Returns:
            Dict: Structure Notion pour le champ select
        """
        # Si un type d'entreprise par défaut est défini, l'utiliser
        if hasattr(self, 'default_business_type') and self.default_business_type:
            type_value = self.default_business_type.strip()
        else:
            type_value = business_type.strip() if business_type and business_type.strip() != "" else "Non spécifié"
            
        # Retourner le format Notion pour le champ select
        return {"select": {"name": type_value}}

    def check_if_company_exists(self, company_name: str) -> bool:
        """
        Vérifie si une entreprise existe déjà dans la base de données Notion
        
        Args:
            company_name: Nom de l'entreprise à vérifier
            
        Returns:
            True si l'entreprise existe déjà, False sinon
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.notion_token}',
                'Content-Type': 'application/json',
                'Notion-Version': '2022-06-28'
            }
            
            # Recherche par nom exact
            search_data = {
                "filter": {
                    "property": "Nom",
                    "title": {
                        "equals": company_name
                    }
                }
            }
            
            response = requests.post(f"https://api.notion.com/v1/databases/{self.database_id}/query", 
                                   headers=headers, json=search_data)
            
            if response.status_code == 200:
                results = response.json().get('results', [])
                return len(results) > 0
            else:
                logger.warning(f"Erreur lors de la vérification de doublon: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de doublon: {e}")
            return False

    def send_to_notion(self, business_data: Dict) -> bool:
        """
        Envoie les données d'une entreprise vers la base Notion
        
        Args:
            business_data: Dictionnaire contenant les informations de l'entreprise
            
        Returns:
            True si l'envoi a réussi, False sinon
        """
        try:
            company_name = business_data.get('nom', '')
            
            headers = {
                'Authorization': f'Bearer {self.notion_token}',
                'Content-Type': 'application/json',
                'Notion-Version': '2022-06-28'
            }
            
            # Formatage des données pour Notion selon la structure réelle
            notion_data = {
                'parent': {'database_id': self.database_id},
                'properties': {
                    'Nom': {
                        'title': [{'text': {'content': business_data.get('nom', 'Sans nom')}}]
                    },
                    'Téléphone': {
                        'phone_number': business_data.get('telephone') if business_data.get('telephone') != 'Non spécifié' else None
                    },
                    'Site Web': {
                        'url': business_data.get('site_web') if business_data.get('site_web') != 'Non spécifié' else None
                    },
                    'Ville': {
                        'rich_text': [{'text': {'content': self._get_or_create_ville_option(business_data.get('ville', 'Non spécifiée'))}}]
                    },
                    'Type d\'entreprise': self._get_or_create_business_type_option(business_data.get('type_entreprise', 'Non spécifié')),
                    'Statut': {
                        'select': {'name': 'À contacter'}  # Statut par défaut
                    },
                    'Commentaires': {
                        'rich_text': [{'text': {'content': f"Adresse: {business_data.get('adresse', 'Non spécifiée')}\nStatut ouverture: {business_data.get('statut_ouverture', 'Non spécifié')}"}}]
                    }
                }
            }
            
            # Note: La base n'a pas de champs pour la note et le nombre d'avis
            # Ces informations seront ajoutées dans les commentaires si disponibles
            if business_data.get('note') is not None or business_data.get('nombre_avis') is not None:
                note_info = ""
                if business_data.get('note') is not None:
                    note_info += f"\nNote: {business_data['note']}/5"
                if business_data.get('nombre_avis') is not None:
                    note_info += f"\nNombre d'avis: {business_data['nombre_avis']}"
                
                current_comment = notion_data['properties']['Commentaires']['rich_text'][0]['text']['content']
                notion_data['properties']['Commentaires']['rich_text'][0]['text']['content'] = current_comment + note_info
            
            response = requests.post(self.notion_url, headers=headers, json=notion_data)
            
            if response.status_code == 200:
                logger.info(f"✅ Entreprise '{business_data['nom']}' ajoutée à Notion")
                return True
            else:
                error_detail = json.loads(response.text)
                error_msg = error_detail.get('message', 'Erreur inconnue')
                logger.error(f"❌ Erreur Notion pour '{business_data['nom']}': Code {response.status_code}")
                logger.error(f"   Message d'erreur: {error_msg}")
                if 'code' in error_detail:
                    logger.error(f"   Code d'erreur: {error_detail['code']}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi vers Notion: {e}")
            return False

    def process_html_file(self, html_file_path: str, default_city: Optional[str] = None, default_business_type: Optional[str] = None) -> Dict:
        """
        Traite un fichier HTML et extrait toutes les entreprises vers Notion
        
        Args:
            html_file_path: Chemin vers le fichier HTML
            default_city: Ville par défaut à utiliser pour toutes les entreprises
            default_business_type: Type d'entreprise par défaut à utiliser pour toutes les entreprises
            
        Returns:
            Dictionnaire avec les statistiques du traitement
        """
        try:
            # Stocker la ville et le type d'entreprise par défaut
            self.default_city = default_city
            self.default_business_type = default_business_type
            extraction_errors = []  # Liste pour stocker les erreurs
            
            # Lecture du fichier HTML
            with open(html_file_path, 'r', encoding='utf-8') as file:
                html_content = file.read()
            
            logger.info(f"Fichier HTML lu: {html_file_path}")
            if default_city:
                logger.info(f"Ville par défaut définie: {default_city}")
            if default_business_type:
                logger.info(f"Type d'entreprise par défaut défini: {default_business_type}")
            
            # Extraction des entreprises
            businesses = self.extract_businesses_from_html(html_content)
            
            if not businesses:
                logger.warning("Aucune entreprise trouvée dans le HTML")
                return {'total': 0, 'success': 0, 'errors': 0}
            
            # Envoi vers Notion
            success_count = 0
            error_count = 0
            duplicate_count = 0
            
            for business in businesses:
                company_name = business.get('nom', '')
                
                # Vérification des doublons avant envoi
                if self.check_if_company_exists(company_name):
                    logger.info(f"⚠️ Entreprise '{company_name}' déjà existante - ignorée")
                    duplicate_count += 1
                    continue
                
                if self.send_to_notion(business):
                    success_count += 1
                else:
                    error_count += 1
            
            stats = {
                'total': len(businesses),
                'success': success_count,
                'errors': error_count,
                'duplicates': duplicate_count,
                'error_details': extraction_errors
            }
            
            logger.info(f"\n📊 Statistiques finales:")
            logger.info(f"  Total d'entreprises: {stats['total']}")
            logger.info(f"  ✅ Succès: {stats['success']}")
            logger.info(f"  ❌ Erreurs: {stats['errors']}")
            logger.info(f"  ⚠️ Doublons: {stats['duplicates']}")
            
            if stats['errors'] > 0:
                logger.info("\n� Détail des erreurs:")
                for i, error in enumerate(extraction_errors, 1):
                    logger.info(f"  {i}. {error}")
            
            return stats
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement du fichier HTML: {e}")
            return {'total': 0, 'success': 0, 'errors': 1}

    def _extract_city_from_address(self, address: str) -> str:
        """
        Extrait la ville depuis une adresse complète
        
        Args:
            address: Adresse complète
            
        Returns:
            Nom de la ville ou 'Non spécifiée'
        """
        try:
            # Pattern pour extraire la ville (dernière partie après le code postal)
            city_pattern = r'\b\d{5}\s+([A-ZÀ-Ÿ][A-Za-zÀ-ÿ\s\-\']+)'
            match = re.search(city_pattern, address)
            
            if match:
                city = match.group(1).strip()
                # Nettoyer la ville (enlever les caractères parasites)
                city = re.sub(r'[^\w\s\-\'À-ÿ]', '', city).strip()
                return city
            
            # Si pas de code postal trouvé, essayer d'autres patterns
            # Chercher "Paris", "Lyon", etc. directement
            common_cities = ['Paris', 'Lyon', 'Marseille', 'Toulouse', 'Nice', 'Nantes', 'Strasbourg', 
                           'Montpellier', 'Bordeaux', 'Lille', 'Rennes', 'Reims', 'Le Havre', 
                           'Saint-Étienne', 'Toulon', 'Grenoble', 'Dijon', 'Angers', 'Nîmes', 'Villeurbanne']
            
            for city in common_cities:
                if city.lower() in address.lower():
                    return city
            
            # Pattern alternatif : dernière partie de l'adresse
            parts = address.split(',')
            if len(parts) >= 2:
                last_part = parts[-1].strip()
                # Enlever les codes postaux
                last_part = re.sub(r'\b\d{5}\b', '', last_part).strip()
                if last_part and len(last_part) > 2:
                    return last_part
            
            return 'Non spécifiée'
            
        except Exception as e:
            logger.warning(f"Erreur lors de l'extraction de la ville: {e}")
            return 'Non spécifiée'

def main():
    """Fonction principale pour tester l'extracteur"""
    try:
        extractor = HTMLGoogleMapsExtractor()
        
        # Traitement du fichier HTML fourni
        html_file = "src/result.html"
        stats = extractor.process_html_file(html_file)
        
        print(f"\n📊 RÉSULTATS:")
        print(f"  Total d'entreprises trouvées: {stats['total']}")
        print(f"  Succès: {stats['success']}")
        print(f"  Erreurs: {stats['errors']}")
        
        if stats['success'] > 0:
            print(f"\n✅ {stats['success']} entreprises ont été ajoutées à votre base Notion!")
        
    except Exception as e:
        logger.error(f"Erreur dans le main: {e}")

if __name__ == "__main__":
    main()
