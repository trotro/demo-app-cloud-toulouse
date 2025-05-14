import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis un fichier .env
load_dotenv()

class LibrairieDB:
    def __init__(self):
        # Récupérer les informations de connexion depuis les variables d'environnement
        self.db_params = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": os.getenv("DB_PORT", "5432"),
            "user": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD", ""),
        }
        self.db_name = os.getenv("DB_NAME", "librairie_db")
        
        # Créer la base de données si elle n'existe pas
        self.create_database()
        
        # Mettre à jour les paramètres pour inclure le nom de la base de données
        self.db_params["dbname"] = self.db_name
        
        # Créer les tables si elles n'existent pas
        self.create_tables()
    
    def create_database(self):
        """Créer la base de données si elle n'existe pas déjà"""
        # Connexion au serveur PostgreSQL sans spécifier de base de données
        conn = psycopg2.connect(**{k: v for k, v in self.db_params.items() if k != "dbname"})
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Vérifier si la base de données existe
        cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (self.db_name,))
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(self.db_name)))
            print(f"Base de données '{self.db_name}' créée avec succès.")
        else:
            print(f"La base de données '{self.db_name}' existe déjà.")
        
        cursor.close()
        conn.close()
    
    def create_tables(self):
        """Créer les tables nécessaires pour la librairie"""
        conn = psycopg2.connect(**self.db_params)
        cursor = conn.cursor()
        
        # Table des librairies
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS librairies (
                id SERIAL PRIMARY KEY,
                nom VARCHAR(100) NOT NULL,
                adresse TEXT NOT NULL,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table des livres
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS livres (
                id SERIAL PRIMARY KEY,
                titre VARCHAR(200) NOT NULL,
                auteur VARCHAR(100),
                isbn VARCHAR(20) UNIQUE,
                annee_publication INTEGER,
                date_ajout TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table de relation entre librairies et livres (many-to-many)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS librairie_livres (
                librairie_id INTEGER REFERENCES librairies(id) ON DELETE CASCADE,
                livre_id INTEGER REFERENCES livres(id) ON DELETE CASCADE,
                date_ajout TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (librairie_id, livre_id)
            )
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        print("Tables créées avec succès.")
    
    def ajouter_librairie(self, nom, adresse):
        """Ajouter une nouvelle librairie"""
        if not isinstance(nom, str) or not isinstance(adresse, str):
            print("Attention: le nom et l'adresse doivent être des chaînes de caractères")
            return None
        
        conn = psycopg2.connect(**self.db_params)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO librairies (nom, adresse) VALUES (%s, %s) RETURNING id",
            (nom, adresse)
        )
        librairie_id = cursor.fetchone()[0]
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"Librairie '{nom}' ajoutée avec succès (ID: {librairie_id}).")
        return librairie_id
    
    def ajouter_livre(self, titre, auteur=None, isbn=None, annee_publication=None):
        """Ajouter un nouveau livre"""
        if not isinstance(titre, str):
            print("Attention: le titre doit être une chaîne de caractères")
            return None
        
        conn = psycopg2.connect(**self.db_params)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO livres (titre, auteur, isbn, annee_publication) VALUES (%s, %s, %s, %s) RETURNING id",
            (titre, auteur, isbn, annee_publication)
        )
        livre_id = cursor.fetchone()[0]
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"Livre '{titre}' ajouté avec succès (ID: {livre_id}).")
        return livre_id
    
    def ajouter_livre_a_librairie(self, librairie_id, livre_id):
        """Ajouter un livre existant à une librairie"""
        conn = psycopg2.connect(**self.db_params)
        cursor = conn.cursor()
        
        # Vérifier si le livre est déjà présent dans la librairie
        cursor.execute(
            "SELECT 1 FROM librairie_livres WHERE librairie_id = %s AND livre_id = %s",
            (librairie_id, livre_id)
        )
        existe = cursor.fetchone()
        
        if existe:
            print("Attention: le livre est déjà présent dans cette librairie")
        else:
            cursor.execute(
                "INSERT INTO librairie_livres (librairie_id, livre_id) VALUES (%s, %s)",
                (librairie_id, livre_id)
            )
            print("Livre ajouté à la librairie avec succès.")
        
        conn.commit()
        cursor.close()
        conn.close()
    
    def supprimer_livre_de_librairie(self, librairie_id, livre_id):
        """Supprimer un livre d'une librairie"""
        conn = psycopg2.connect(**self.db_params)
        cursor = conn.cursor()
        
        cursor.execute(
            "DELETE FROM librairie_livres WHERE librairie_id = %s AND livre_id = %s",
            (librairie_id, livre_id)
        )
        
        if cursor.rowcount > 0:
            print("Livre supprimé de la librairie avec succès.")
        else:
            print("Livre non trouvé dans cette librairie.")
        
        conn.commit()
        cursor.close()
        conn.close()
    
    def obtenir_librairie(self, librairie_id):
        """Obtenir les informations d'une librairie par son ID"""
        conn = psycopg2.connect(**self.db_params)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, nom, adresse FROM librairies WHERE id = %s",
            (librairie_id,)
        )
        librairie = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if librairie:
            return {
                "id": librairie[0],
                "nom": librairie[1],
                "adresse": librairie[2]
            }
        return None
    
    def obtenir_livres_de_librairie(self, librairie_id):
        """Obtenir tous les livres d'une librairie"""
        conn = psycopg2.connect(**self.db_params)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT l.id, l.titre, l.auteur, l.isbn, l.annee_publication
            FROM livres l
            JOIN librairie_livres ll ON l.id = ll.livre_id
            WHERE ll.librairie_id = %s
            ORDER BY l.titre
        """, (librairie_id,))
        
        livres = []
        for livre in cursor.fetchall():
            livres.append({
                "id": livre[0],
                "titre": livre[1],
                "auteur": livre[2],
                "isbn": livre[3],
                "annee_publication": livre[4]
            })
        
        cursor.close()
        conn.close()
        
        return livres
    
    def rechercher_livres(self, terme_recherche):
        """Rechercher des livres par titre ou auteur"""
        conn = psycopg2.connect(**self.db_params)
        cursor = conn.cursor()
        
        terme = f"%{terme_recherche}%"
        cursor.execute("""
            SELECT id, titre, auteur, isbn, annee_publication
            FROM livres
            WHERE titre ILIKE %s OR auteur ILIKE %s
            ORDER BY titre
        """, (terme, terme))
        
        livres = []
        for livre in cursor.fetchall():
            livres.append({
                "id": livre[0],
                "titre": livre[1],
                "auteur": livre[2],
                "isbn": livre[3],
                "annee_publication": livre[4]
            })
        
        cursor.close()
        conn.close()
        
        return livres


# Adapter la classe Librairie pour utiliser la base de données
class Librairie:
    def __init__(self, nom, adresse, livres=None):
        self.db = LibrairieDB()
        self.set_nom(nom)
        self.set_adresse(adresse)
        self.id = self.db.ajouter_librairie(nom, adresse)
        
        if livres:
            self.set_livres(livres)
    
    def set_livres(self, livres):
        try:
            if isinstance(livres, list):
                # Supprimer tous les livres existants et ajouter les nouveaux
                conn = psycopg2.connect(**self.db.db_params)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM librairie_livres WHERE librairie_id = %s", (self.id,))
                conn.commit()
                cursor.close()
                conn.close()
                
                # Ajouter chaque livre
                for livre in livres:
                    self.add_livres(livre)
            else:
                raise ValueError
        except ValueError:
            print("Attention la liste est incorrecte")
    
    def set_nom(self, nom):
        try:
            if isinstance(nom, str):
                self.__nom = nom
                # Mettre à jour dans la base de données si l'ID existe
                if hasattr(self, 'id') and self.id:
                    conn = psycopg2.connect(**self.db.db_params)
                    cursor = conn.cursor()
                    cursor.execute("UPDATE librairies SET nom = %s WHERE id = %s", (nom, self.id))
                    conn.commit()
                    cursor.close()
                    conn.close()
            else:
                raise ValueError
        except ValueError:
            print("Attention le nom est incorrect")
    
    def set_adresse(self, adresse):
        try:
            if isinstance(adresse, str):
                self.__adresse = adresse
                # Mettre à jour dans la base de données si l'ID existe
                if hasattr(self, 'id') and self.id:
                    conn = psycopg2.connect(**self.db.db_params)
                    cursor = conn.cursor()
                    cursor.execute("UPDATE librairies SET adresse = %s WHERE id = %s", (adresse, self.id))
                    conn.commit()
                    cursor.close()
                    conn.close()
            else:
                raise ValueError
        except ValueError:
            print("Attention l'adresse est incorrecte")
    
    def get_nom(self):
        return self.__nom
    
    def get_addresse(self):
        return self.__adresse
    
    def get_livres(self):
        return self.db.obtenir_livres_de_librairie(self.id)
    
    def add_livres(self, livre, auteur=None, isbn=None, annee_publication=None):
        try:
            if not isinstance(livre, str):
                raise ValueError
        except ValueError:
            print("Attention le livre donné est incorrect")
            return
        
        # Vérifier si le livre existe déjà dans la base de données
        livres_trouves = self.db.rechercher_livres(livre)
        livre_id = None
        
        # Si un livre avec ce titre exact existe, utiliser son ID
        for l in livres_trouves:
            if l["titre"].lower() == livre.lower():
                livre_id = l["id"]
                break
        
        # Si le livre n'existe pas, l'ajouter
        if not livre_id:
            livre_id = self.db.ajouter_livre(livre, auteur, isbn, annee_publication)
        
        # Ajouter le livre à la librairie
        self.db.ajouter_livre_a_librairie(self.id, livre_id)
    
    def del_livres(self, livre):
        # Trouver l'ID du livre
        livres_trouves = self.db.rechercher_livres(livre)
        
        for l in livres_trouves:
            if l["titre"].lower() == livre.lower():
                # Supprimer la relation entre le livre et la librairie
                self.db.supprimer_livre_de_librairie(self.id, l["id"])
                return
        
        print(f"Livre '{livre}' non trouvé dans la librairie")
    
    def index(self, livre=None):
        return "Bienvenu sur le site de la librairie {0} !".format(self.__nom)


# Exemple d'utilisation
if __name__ == "__main__":
    # Initialiser la base de données
    db = LibrairieDB()
    
    # Créer une librairie
    librairie = Librairie("Librairie du Centre", "123 Rue de la Paix, 75001 Paris", [])
    
    # Ajouter des livres
    librairie.add_livres("L'Étranger", "Albert Camus", "978-2070360024", 1942)
    librairie.add_livres("Les Misérables", "Victor Hugo", "978-2253096344", 1862)
    librairie.add_livres("Le Petit Prince", "Antoine de Saint-Exupéry", "978-2070612758", 1943)
    
    # Afficher tous les livres de la librairie
    print("\nListe des livres de la librairie:")
    for livre in librairie.get_livres():
        print(f"- {livre['titre']} par {livre['auteur']} ({livre['annee_publication']})")
    
    # Supprimer un livre
    librairie.del_livres("Les Misérables")
    
    # Afficher la liste mise à jour
    print("\nListe mise à jour des livres:")
    for livre in librairie.get_livres():
        print(f"- {livre['titre']} par {livre['auteur']} ({livre['annee_publication']})")
    
    # Afficher la page d'index
    print("\n" + librairie.index())