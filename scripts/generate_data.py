from faker import Faker
import pandas as pd
import numpy as np
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import random
import os

# Initialize Faker with French locale
fake = Faker(['fr_FR'])
Faker.seed(42)  # Pour la reproductibilité
np.random.seed(42)

# Configuration des chemins
DATA_DIR = '/opt/airflow/data'

def init_dirs():
    """Ensure all required directories exist"""
    os.makedirs(DATA_DIR, exist_ok=True)

# Données prédéfinies
VILLES_PREDEFINIES = [
    {'ville': 'Paris', 'code_postal': '75000'},
    {'ville': 'Lyon', 'code_postal': '69000'},
    {'ville': 'Marseille', 'code_postal': '13000'},
    {'ville': 'Bordeaux', 'code_postal': '33000'},
    {'ville': 'Lille', 'code_postal': '59000'},
    {'ville': 'Toulouse', 'code_postal': '31000'},
    {'ville': 'Nice', 'code_postal': '06000'},
    {'ville': 'Nantes', 'code_postal': '44000'},
    {'ville': 'Strasbourg', 'code_postal': '67000'},
    {'ville': 'Montpellier', 'code_postal': '34000'}
]

PRODUITS_PREDEFINIS = [
    {'nom_produit': 'iPhone 13 Pro', 'categorie': 'Électronique', 'prix_unitaire': 999.99},
    {'nom_produit': 'Samsung Galaxy S21', 'categorie': 'Électronique', 'prix_unitaire': 859.99},
    {'nom_produit': 'MacBook Pro 14"', 'categorie': 'Électronique', 'prix_unitaire': 1999.99},
    {'nom_produit': 'PlayStation 5', 'categorie': 'Électronique', 'prix_unitaire': 499.99},
    {'nom_produit': 'Nike Air Max', 'categorie': 'Sport', 'prix_unitaire': 129.99},
    {'nom_produit': 'Adidas Ultraboost', 'categorie': 'Sport', 'prix_unitaire': 159.99},
    {'nom_produit': 'Machine à café Delonghi', 'categorie': 'Électroménager', 'prix_unitaire': 299.99},
    {'nom_produit': 'Robot cuiseur Thermomix', 'categorie': 'Électroménager', 'prix_unitaire': 1299.99},
    {'nom_produit': 'Aspirateur Dyson V15', 'categorie': 'Électroménager', 'prix_unitaire': 599.99},
    {'nom_produit': 'TV OLED LG 65"', 'categorie': 'Électronique', 'prix_unitaire': 2499.99}
]

CATEGORIES = ['Électronique', 'Sport', 'Électroménager', 'Mode', 'Maison', 'Jardin', 'Alimentation']
SEGMENTS_CLIENT = ['Premium', 'Standard', 'Basic']
MOYENS_PAIEMENT = ['CB', 'PayPal', 'Virement', 'Apple Pay', 'Google Pay']

def generate_clients(n=1000):
    """
    Génère des données clients.
    
    Args:
        n (int): Nombre de clients à générer
    
    Returns:
        pandas.DataFrame: DataFrame contenant les données clients
    """
    clients = []
    
    for _ in range(n):
        ville_info = random.choice(VILLES_PREDEFINIES)
        date_inscription = fake.date_between(start_date='-5y', end_date='today')
        
        client = {
            'client_id': fake.unique.random_number(digits=6),
            'nom': fake.last_name(),
            'prenom': fake.first_name(),
            'email': fake.email(),
            'telephone': fake.phone_number(),
            'ville': ville_info['ville'],
            'code_postal': ville_info['code_postal'],
            'adresse': fake.street_address(),
            'segment': np.random.choice(SEGMENTS_CLIENT, p=[0.2, 0.5, 0.3]),
            'date_inscription': date_inscription.strftime('%Y-%m-%d'),
            'age': random.randint(18, 80),
            'genre': random.choice(['M', 'F']),
            'newsletter': random.choice([True, False]),
            'derniere_connexion': fake.date_between(start_date=date_inscription, end_date='today').strftime('%Y-%m-%d')
        }
        clients.append(client)
    
    return pd.DataFrame(clients)

def generate_products(n=100):
    """
    Génère des données produits.
    
    Args:
        n (int): Nombre total de produits à générer (incluant les prédéfinis)
    
    Returns:
        list: Liste de dictionnaires contenant les données produits
    """
    products = []
    
    # Ajouter d'abord les produits prédéfinis
    for prod in PRODUITS_PREDEFINIS:
        product = {
            'product_id': fake.unique.random_number(digits=5),
            'nom_produit': prod['nom_produit'],
            'categorie': prod['categorie'],
            'prix_unitaire': prod['prix_unitaire'],
            'stock': random.randint(0, 1000),
            'date_ajout': fake.date_between(start_date='-2y', end_date='today').strftime('%Y-%m-%d'),
            'fournisseur': fake.company(),
            'description': fake.text(max_nb_chars=200),
            'poids': round(random.uniform(0.1, 20.0), 2),
            'disponible': random.choice([True, False]),
            'note_moyenne': round(random.uniform(3.5, 5.0), 1)
        }
        products.append(product)
    
    # Générer les produits supplémentaires
    for _ in range(n - len(PRODUITS_PREDEFINIS)):
        product = {
            'product_id': fake.unique.random_number(digits=5),
            'nom_produit': fake.catch_phrase(),
            'categorie': random.choice(CATEGORIES),
            'prix_unitaire': round(random.uniform(10, 2000), 2),
            'stock': random.randint(0, 1000),
            'date_ajout': fake.date_between(start_date='-2y', end_date='today').strftime('%Y-%m-%d'),
            'fournisseur': fake.company(),
            'description': fake.text(max_nb_chars=200),
            'poids': round(random.uniform(0.1, 20.0), 2),
            'disponible': random.choice([True, False]),
            'note_moyenne': round(random.uniform(3.5, 5.0), 1)
        }
        products.append(product)
    
    return products

def generate_transactions(n=10000, clients_df=None, products=None):
    """
    Génère des données de transactions.
    
    Args:
        n (int): Nombre de transactions à générer
        clients_df (pandas.DataFrame): DataFrame contenant les données clients
        products (list): Liste des produits disponibles
    
    Returns:
        list: Liste de dictionnaires contenant les données de transactions
    """
    transactions = []
    client_ids = clients_df['client_id'].tolist()
    
    start_date = datetime.now() - timedelta(days=365)
    end_date = datetime.now()
    
    for _ in range(n):
        client_id = np.random.choice(client_ids)
        nb_products = np.random.randint(1, 6)  # 1 à 5 produits par transaction
        transaction_date = fake.date_time_between(start_date=start_date, end_date=end_date)
        
        for _ in range(nb_products):
            product = random.choice(products)
            quantity = np.random.randint(1, 5)
            prix_unitaire = float(product['prix_unitaire'])
            
            # Appliquer une réduction aléatoire
            if random.random() < 0.2:  # 20% de chance d'avoir une réduction
                reduction = round(random.uniform(0.05, 0.25), 2)  # 5% à 25% de réduction
                prix_unitaire = prix_unitaire * (1 - reduction)
            
            montant_total = round(quantity * prix_unitaire, 2)
            
            transaction = {
                'transaction_id': fake.unique.random_number(digits=8),
                'client_id': int(client_id),
                'product_id': product['product_id'],
                'date_transaction': transaction_date.strftime('%Y-%m-%d %H:%M:%S'),
                'quantite': quantity,
                'prix_unitaire': prix_unitaire,
                'montant_total': montant_total,
                'moyen_paiement': np.random.choice(MOYENS_PAIEMENT, p=[0.4, 0.3, 0.1, 0.1, 0.1]),
                'statut': random.choice(['Completée', 'En cours', 'Annulée']),
                'code_promo_utilise': random.choice([True, False]),
                'commentaire': fake.text(max_nb_chars=100) if random.random() < 0.3 else None
            }
            transactions.append(transaction)
    
    return transactions

def save_transactions_to_xml(transactions):
    """
    Sauvegarde les transactions au format XML.
    
    Args:
        transactions (list): Liste des transactions à sauvegarder
    """
    root = ET.Element('transactions')
    
    for trans in transactions:
        transaction = ET.SubElement(root, 'transaction')
        for key, value in trans.items():
            elem = ET.SubElement(transaction, key)
            elem.text = str(value)
    
    tree = ET.ElementTree(root)
    tree.write(os.path.join(DATA_DIR, 'transactions.xml'), encoding='utf-8', xml_declaration=True)

def main():
    """
    Fonction principale pour générer toutes les données.
    """
    print("Generating data...")
    
    # Initialize directories
    init_dirs()
    
    # Générer et sauvegarder les clients
    print("Generating clients...")
    clients_df = generate_clients(n=1000)
    clients_df.to_csv(os.path.join(DATA_DIR, 'clients.csv'), index=False, encoding='utf-8')
    
    # Générer et sauvegarder les produits
    print("Generating products...")
    products = generate_products(n=100)
    with open(os.path.join(DATA_DIR, 'products.json'), 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    
    # Générer et sauvegarder les transactions
    print("Generating transactions...")
    transactions = generate_transactions(n=10000, clients_df=clients_df, products=products)
    save_transactions_to_xml(transactions)
    
    print("Data generation completed!")
    print(f"Generated files in {DATA_DIR}/:")
    print("- clients.csv")
    print("- products.json")
    print("- transactions.xml")

if __name__ == "__main__":
    main()