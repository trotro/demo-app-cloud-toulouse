# API Librairie Flask

Une application API REST simple pour la gestion d'une librairie, construite avec Flask et déployée via ArgoCD et GitHub Actions.

## 📋 Présentation

Cette application est une démonstration de la mise en place d'un pipeline CI/CD complet pour une application Flask, en utilisant:
- GitHub Actions pour l'intégration continue
- Harbor comme registre d'images privé
- ArgoCD pour le déploiement continu sur Kubernetes

L'application permet de gérer une librairie avec ses livres associés.

## 🛠️ Technologie

- Python 3.10
- Flask
- Docker
- Kubernetes
- GitHub Actions
- ArgoCD

## 🚀 Installation et démarrage rapide

### Démarrage local

1. **Cloner le dépôt**
   ```bash
   git clone https://github.com/votre-utilisateur/librairie-api.git
   cd librairie-api
   ```

2. **Créer un environnement virtuel**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Sur Windows: venv\Scripts\activate
   ```

3. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

4. **Démarrer l'application**
   ```bash
   flask run
   ```

L'API sera disponible à l'adresse http://localhost:5000

### Exécution avec Docker

```bash
# Construire l'image
docker build -t librairie-api:latest .

# Exécuter le conteneur
docker run -p 5000:5000 librairie-api:latest
```

## 📘 Utilisation de l'API

### Endpoints disponibles

- `GET /` - Obtenir le nom de la librairie
- `GET /nom` - Obtenir le nom de la librairie
- `GET /livres` - Récupérer tous les livres
- `POST /livres` - Ajouter un nouveau livre
- `DELETE /livres` - Supprimer un livre
- `GET /health` - Vérification de la santé de l'application pour Kubernetes

### Exemples d'utilisation

**Récupérer tous les livres:**
```bash
curl -X GET http://localhost:5000/livres
```

**Ajouter un nouveau livre:**
```bash
curl -X POST http://localhost:5000/livres \
  -H "Content-Type: application/json" \
  -d '{"nomLivre": "Les Misérables"}'
```

**Supprimer un livre:**
```bash
curl -X DELETE http://localhost:5000/livres \
  -H "Content-Type: application/json" \
  -d '{"nomLivre": "Les Misérables"}'
```

## 🧪 Tests

```bash
# Exécuter les tests unitaires
pytest

# Exécuter les tests avec couverture de code
pytest --cov=.
```

## 📦 Pipeline CI/CD

### Variables d'Environnement et Secrets pour CI/CD

Pour que le workflow GitHub Actions fonctionne correctement, vous devez configurer les secrets suivants dans les paramètres de votre dépôt GitHub (Settings > Secrets and variables > Actions) :

| Nom du Secret | Description | Exemple |
|---------------|-------------|---------|
| `HARBOR_URL` | URL de votre registre Harbor privé | `harbor.example.com` |
| `HARBOR_USERNAME` | Nom d'utilisateur Harbor pour l'authentification | `robot$project-name+github-actions` |
| `HARBOR_PASSWORD` | Mot de passe ou token Harbor | `eyJhbGciOiJSUzI1NiIsInR5...` |
| `GH_PAT` | Personal Access Token GitHub avec accès aux dépôts | `ghp_1234567890abcdef...` |

Le token GitHub (`GH_PAT`) doit avoir les autorisations suivantes :
- `repo` - Accès complet aux dépôts
- `read:packages` - Pour accéder aux packages GitHub
- `write:packages` - Pour publier des packages GitHub

#### Configuration du Dépôt de Manifestes ArgoCD

Le workflow CI/CD assume que vous avez un dépôt séparé pour les manifestes Kubernetes qu'ArgoCD surveille. Par défaut, le workflow pointe vers :

```
repository: VOTRE_NOM_UTILISATEUR/argocd-demo-app
```

Vous devez soit :
1. Créer ce dépôt avec le même nom
2. Ou modifier le workflow pour pointer vers votre dépôt de manifestes existant

#### Structure du Dépôt de Manifestes

Le dépôt de manifestes doit contenir au moins :
```
kubernetes/
  └── deployment.yaml    # Le manifeste que le pipeline CI/CD mettra à jour
```

### Workflow GitHub Actions

Le workflow GitHub Actions est configuré pour:
1. Exécuter le linting et les tests
2. Analyser la sécurité du code
3. Construire et pousser l'image Docker vers Harbor
4. Déployer sur un cluster de test pour les tests d'intégration
5. Mettre à jour les manifestes Kubernetes dans le dépôt ArgoCD

### ArgoCD

ArgoCD surveille le dépôt contenant les manifestes Kubernetes et applique automatiquement les changements au cluster de production.

## 🏗️ Structure du projet

```
librairie-api/
├── app.py                # Application Flask principale avec classe Librairie
├── requirements.txt      # Dépendances Python
├── Dockerfile            # Instructions pour construire l'image Docker
├── .github/
│   └── workflows/
│       └── ci-cd.yml     # Configuration du workflow GitHub Actions
├── kubernetes/
│   └── deployment.yaml   # Manifestes Kubernetes
└── tests/
    ├── unit/            # Tests unitaires
    └── integration/     # Tests d'intégration
```

## 🔧 Configuration Technique

### Fichier Dockerfile

```dockerfile
# Utiliser une image Python officielle comme base
FROM python:3.10-slim

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier les fichiers de dépendances et installer les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du code de l'application
COPY . .

# Exposer le port sur lequel l'application Flask va s'exécuter
EXPOSE 5000

# Variables d'environnement pour Flask
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Exécuter l'application avec Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

### Manifeste Kubernetes

Le déploiement Kubernetes inclut :
- Un Deployment avec plusieurs réplicas pour la haute disponibilité
- Un Service pour exposer l'application
- Des sondes de santé pour garantir la fiabilité
- Un Ingress pour l'accès externe (si vous utilisez un contrôleur Ingress)

Extrait du manifeste Kubernetes :
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: librairie-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: librairie-api
  template:
    spec:
      containers:
      - name: librairie-api
        image: harbor.example.com/project-name/librairie-api:latest
        ports:
        - containerPort: 5000
        readinessProbe:
          httpGet:
            path: /health
            port: 5000
```

### Configuration ArgoCD

Pour configurer ArgoCD afin qu'il surveille et déploie votre application :

1. Créez une application dans ArgoCD :

```bash
argocd app create librairie-api \
  --repo https://github.com/VOTRE_NOM_UTILISATEUR/argocd-demo-app.git \
  --path kubernetes \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace default \
  --sync-policy automated \
  --auto-prune \
  --self-heal
```

2. Vérifiez le statut de l'application :

```bash
argocd app get librairie-api
```

### Intégration avec Harbor

Pour tirer pleinement parti de Harbor, considérez ces configurations supplémentaires :

1. **Analyse de sécurité** : Activez les scans automatiques des images dans Harbor
2. **Règles de rétention** : Configurez des règles pour nettoyer les anciennes images
3. **Webhooks** : Configurez des webhooks Harbor pour notifier ArgoCD quand de nouvelles images sont disponibles

## 🔒 Variables d'environnement

- `FLASK_APP` - Nom du fichier de l'application Flask (par défaut: app.py)
- `FLASK_ENV` - Environnement Flask (development/production)

## 👥 Contribution

Les contributions sont les bienvenues! N'hésitez pas à ouvrir une issue ou une pull request.

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.