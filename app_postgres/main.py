from librairie_db import Librairie, LibrairieDB
from flask import Flask, jsonify, request
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

app = Flask(__name__)

# Initialiser la base de données
db = LibrairieDB()

# Créer ou récupérer la librairie CGI
def get_librairie():
    # Rechercher si la librairie existe déjà dans la base de données
    conn = db.db_params.copy()
    conn["dbname"] = db.db_name
    
    import psycopg2
    connection = psycopg2.connect(**conn)
    cursor = connection.cursor()
    
    cursor.execute("SELECT id FROM librairies WHERE nom = %s", ("CGI",))
    result = cursor.fetchone()
    
    if result:
        # La librairie existe déjà, on va la récupérer
        librairie_id = result[0]
        cursor.close()
        connection.close()
        
        # Récupérer les détails de la librairie
        cursor = connection.cursor()
        cursor.execute("SELECT nom, adresse FROM librairies WHERE id = %s", (librairie_id,))
        nom, adresse = cursor.fetchone()
        cursor.close()
        connection.close()
        
        # Créer l'objet Librairie avec l'ID existant
        librairie = Librairie(nom, adresse, [])
        librairie.id = librairie_id
        return librairie
    else:
        # La librairie n'existe pas, on va la créer
        cursor.close()
        connection.close()
        
        # Créer la librairie
        librairie = Librairie("CGI", "15 Avenue du Docteur Maurice Grynfogel", [])
        
        # Ajouter les livres initiaux
        librairie.add_livres("Le DevOps c'est super !")
        librairie.add_livres("Le Python pour les nuls")
        
        return librairie

# Initialiser la librairie au démarrage de l'application
librairie1 = get_librairie()

@app.route("/")
def get():
    return jsonify(librairie1.get_nom())

@app.route("/nom")
def getnom():
    return jsonify(librairie1.get_nom())

@app.route("/livres")
def getlivres():
    # Récupérer la liste des livres à partir de la base de données
    livres = librairie1.get_livres()
    
    # Convertir en liste de titres pour maintenir la compatibilité avec le code original
    titres_livres = [livre["titre"] for livre in livres]
    
    return jsonify(titres_livres)

@app.route('/livres', methods=['POST'])
def addlivres():
    livre = request.get_json()
    print(livre)
    librairie1.add_livres(livre['nomLivre'])
    return "", 204

@app.route('/livres', methods=['DELETE'])
def dellivres():
    livre = request.get_json()
    print(livre)
    librairie1.del_livres(livre['nomLivre'])
    return "", 204

# Point de terminaison Health Check pour Kubernetes
@app.route('/health', methods=['GET'])
def health_check():
    # Vérifier la connexion à la base de données
    try:
        import psycopg2
        conn = db.db_params.copy()
        conn["dbname"] = db.db_name
        connection = psycopg2.connect(**conn)
        connection.close()
        return jsonify({'status': 'healthy', 'database': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

# Point de terminaison pour obtenir des informations détaillées sur les livres
@app.route('/livres/details')
def get_livres_details():
    # Récupérer tous les détails des livres
    livres = librairie1.get_livres()
    return jsonify(livres)

# Point de terminaison pour rechercher des livres
@app.route('/livres/search')
def search_livres():
    terme = request.args.get('q', '')
    if not terme:
        return jsonify([])
    
    livres_trouves = db.rechercher_livres(terme)
    return jsonify(livres_trouves)

if __name__ == "__main__":
    # Récupérer le port depuis les variables d'environnement ou utiliser 5000 par défaut
    port = int(os.environ.get("PORT", 5000))
    
    # Exécuter l'application
    app.run(host="0.0.0.0", port=port, debug=True)