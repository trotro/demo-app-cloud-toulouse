from librairie import Librairie
from flask import Flask, jsonify, request

app = Flask(__name__)

librairie1 = Librairie("CGI", "15 Avenue du Docteur Maurice Grynfogel", ["Le DevOps c'est super !", "Le Python pour les nuls"])

@app.route("/")
def get():
    return jsonify(librairie1.get_nom())

@app.route("/nom")
def getnom():
    return jsonify(librairie1.get_nom())

@app.route("/livres")
def getlivres():
    return jsonify(librairie1.get_livres())

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
