class Librairie :
    def __init__(self, nom, adresse, livres):
        self.set_nom(nom)
        self.set_adresse(adresse)
        self.set_livres(livres)
    
    def set_livres(self, livres):
        try:
            if isinstance(livres, list):
                self.__livres = livres
            else: 
                raise ValueError
        except ValueError:
            print("Attention la liste est incorrecte")
    
    def set_nom(self, nom):
        try:
            if isinstance(nom, str):
                self.__nom = nom
            else: 
                raise ValueError
        except ValueError:
            print("Attention le nom est incorrect")
    
    def set_adresse(self, adresse):
        try:
            if isinstance(adresse, str):
                self.__adresse = adresse 
            else: 
                raise ValueError
        except ValueError:
                print("Attention l'adresse est incorrecte")
    
    def get_nom(self):
        return self.__nom
    
    def get_addresse(self):
        return self.__adresse
    
    def get_livres(self):
        return self.__livres
    
    def add_livres(self, livre):
        try:
            if not isinstance(livre, str):
                raise ValueError
        except ValueError:
            print("Attention le livre donne est incorrect")
        present = False
        for livreref in self.__livres:
            if livreref == livre:
                print("Attention le livre est deja present")
                present = True
        if not present:
            self.__livres.append(livre)
    
    def del_livres(self, livre):
        self.__livres.remove(livre)
    
    def index(self, livre):
        return "Bienvenu sur le site de la librairie {0} !".format(self.__nom)