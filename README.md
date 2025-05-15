## Guide d'Atelier

### Table des Matières
1. [Introduction](#introduction)
2. [Prérequis de l'Atelier](#prerequis)
3. [GitHub Workflows et CI/CD](#github-workflows)
4. [ArgoCD - GitOps pour Kubernetes](#argocd)
5. [Scénarios d'Atelier](#scenarios-atelier)
6. [Crossplane pour gérer son infra applicative](#crossplane)
7. [Conclusion](#conclusion)

Annexes : 
 - Utilisation Avancée d'ArgoCD
 - Troubleshooting
 - Ressources
 - GitOps

<a name="introduction"></a>
## 1. Introduction

Cet atelier offre une expérience pratique avec les architectures modernes de déploiement et les workflows CI/CD en utilisant :

- **ArgoCD** : Un outil de livraison continue déclaratif basé sur GitOps pour Kubernetes
- **GitHub Workflows** : Un service d'intégration et de livraison continues intégré à GitHub

À la fin de cet atelier, les participants comprendront comment :
- Implémenter des workflows GitOps avec ArgoCD
- Configurer des pipelines CI/CD avec GitHub Actions
- Automatiser le cycle de vie complet de déploiement d'applications cloud-natives
- Appliquer les bonnes pratiques pour des déploiements robustes et fiables

<a name="prerequis"></a>
## 2. Prérequis de l'Atelier

### Connaissances Requises
- Compréhension basique des concepts Kubernetes (Pods, Déploiements, Services)
- Familiarité avec Git et les technologies de conteneurs
- Compétences de base en ligne de commande
- Notions fondamentales de CI/CD

### Prérequis Techniques
- Compte GitHub
- Accès à un registre Harbor privé (fourni pour l'atelier)
- Accès à un cluster Kubernetes (fourni pour l'atelier)
- Client Git installé localement
- Éditeur de texte au choix

### Configuration des Accès GitHub

Pour permettre à ArgoCD et à vos workflows CI/CD d'accéder à vos dépôts GitHub et au registre Harbor, vous devez configurer les accès appropriés :

1. **Création d'un Personal Access Token (PAT) GitHub** :
   - Accédez à GitHub > Settings > Developer settings > Personal access tokens
   - Cliquez sur "Generate new token" et sélectionnez les autorisations suivantes :
     - `repo` (accès complet aux dépôts)
     - `read:packages` (pour accéder aux packages GitHub si nécessaire)
     - `write:packages` (pour publier des packages GitHub si nécessaire)
   - Copiez le token généré et conservez-le en lieu sûr

2. **Configuration des identifiants Harbor** :
   - Récupérez vos identifiants pour le registre Harbor privé :
     - URL du registre : `harbor.cgicloudtoulouse.fr`
     - Nom d'utilisateur Harbor
     - Mot de passe ou token d'accès Harbor

3. **Configuration de GitHub Secrets pour CI/CD** :
   - Dans votre dépôt GitHub, allez dans Settings > Secrets and variables > Actions
   - Ajoutez les secrets suivants :
     - `HARBOR_URL` : l'URL de votre registre Harbor (ex: harbor.example.com)
     - `HARBOR_USERNAME` : votre nom d'utilisateur Harbor
     - `HARBOR_PASSWORD` : votre mot de passe ou token Harbor

<a name="github-workflows"></a>
## 3. GitHub Workflows et CI/CD

### 3.1 Introduction aux GitHub Actions

GitHub Actions est un service d'intégration et de livraison continues intégré directement à GitHub. Il permet d'automatiser les flux de travail de développement logiciel, y compris les tests, la construction et le déploiement.

Concepts clés des GitHub Actions :
- **Workflow** : Processus automatisé configurable
- **Events** : Activités qui déclenchent un workflow (push, pull request, etc.)
- **Jobs** : Ensemble d'étapes exécutées sur un même runner
- **Steps** : Tâches individuelles dans un job
- **Actions** : Applications réutilisables pour les steps
- **Runners** : Serveurs qui exécutent les workflows

### 3.2 Création d'un Workflow CI GitHub Actions

Créons un workflow CI basique pour une application :

1. Dans votre dépôt GitHub, créez un répertoire `.github/workflows`
2. Ajoutez un fichier `ci.yml` avec le contenu suivant :

```yaml
name: CI Pipeline

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  push_to_registries:
    name: Push Docker image to single registry
    runs-on: ubuntu-latest
    permissions:
      packages: write
      contents: read
      attestations: write
      id-token: write
    steps:
      - name: Check out the repo
        uses: actions/checkout@v4

      - name: Log in to the Container registry
        uses: docker/login-action@65b78e6e13532edd9afa3aa52ac7964289d1a9c1
        with:
          registry: ${{ secrets.HARBOR_URL }}
          username: ${{ secrets.HARBOR_USERNAME }}
          password: ${{ secrets.HARBOR_PASSWORD }}

      - name: Extract metadata (tags, labels) for Docker
        id: meta
        uses: docker/metadata-action@9ec57ed1fcdbf14dcef7dfbe97b2010124a938b7
        with:
          images: ${{ secrets.HARBOR_URL }}/library/standard-app
          tags: type=sha

      - name: Build and push Docker images
        id: push
        uses: docker/build-push-action@3b5e8027fcad23fda98b2e3ac259d8d67585f671
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
```

3. Configurez les secrets dans votre dépôt GitHub comme indiqué dans la section précédente.

### 3.3 Intégration CI/CD avec ArgoCD

Pour compléter le pipeline CI/CD, vous allez intégrer GitHub Actions avec ArgoCD :

1. Ajoutez un job de déploiement à votre workflow GitHub Actions :

```yaml
  update-manifests:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          repository: VOTRE_NOM_UTILISATEUR/demo-app-cloud-toulouse.git
      - name: Update image tag
        run: |
          sed -i "s|image: .*/IMAGE_NAME:.*$|image: ${{ secrets.HARBOR_URL }}/library/IMAGE_NAME:${{ github.sha }}|g" charts/standard-app/values.yaml
      - name: Commit and push changes
        run: |
          git config --global user.name "GitHub Actions"
          git config --global user.email "actions@github.com"
          git add charts/standard-app/values.yaml
          git commit -m "Update image to ${{ github.sha }}"
          git push
```

Ce workflow :
1. Met à jour le manifeste de déploiement Kubernetes avec le nouveau tag d'image
2. ArgoCD détecte le changement et déploie automatiquement la nouvelle version

### 3.4 Workflow Avancé avec Validation et Tests d'Intégration

Améliorons notre workflow avec des validations supplémentaires et des tests d'intégration :

```yaml
name: CI/CD Pipeline

on:présentés précédemment
  push:
    branches: [ master ]
  pull_request:
    branches: [ master ]

jobs:
  ...
  
  integration-test:
    needs: build
    if: github.event_name != 'pull_request'
    runs-on: ubuntu-latest
    timeout-minutes: 60
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install test dependencies
        run: |
          python -m pip install --upgrade pip
          pip install pytest requests

      - name: Set up chart-testing
        uses: helm/chart-testing-action@v2.7.0

      - name: Run chart-testing (list-changed)
        id: list-changed
        run: |
          changed=$(ct list-changed --target-branch ${{ github.event.repository.default_branch }})
          if [[ -n "$changed" ]]; then
            echo "changed=true" >> "$GITHUB_OUTPUT"
          fi

      - name: Run chart-testing (lint)
        if: steps.list-changed.outputs.changed == 'true'
        run: ct lint --target-branch ${{ github.event.repository.default_branch }}

      - name: Set up k8s Kind cluster
        uses: helm/kind-action@v1.12.0
      - name: Create image pull secret
        run: |
          # Création du namespace de test
          kubectl create namespace test --dry-run=client -o yaml | kubectl apply -f -
          
          kubectl create secret docker-registry harbor-creds \
            --namespace test \
            --docker-server=${{ secrets.HARBOR_URL }} \
            --docker-username=${{ secrets.HARBOR_USERNAME }} \
            --docker-password=${{ secrets.HARBOR_PASSWORD }} \
            --dry-run=client -o yaml | kubectl apply -f -
      - name: Deploy app to test cluster
        run: |
          # Création d'un fichier values.yaml temporaire avec l'image mise à jour
          cat <<EOF > /tmp/values-override.yaml
          image:
            name: ${{ secrets.HARBOR_URL }}/library/standard-app:${{ github.sha }}
          EOF
          
          # Installation/mise à jour du chart Helm avec les valeurs personnalisées
          helm upgrade --install standard-app ./charts/standard-app \
            --namespace test \
            -f ./charts/standard-app/values-dev.yaml \
            -f /tmp/values-override.yaml \
            --debug
          
          sleep 30

          # Check pod status
          echo "Checking pod status..."
          kubectl get pods -n test -l app=standard-app -o wide
          
          # Check events for troubleshooting
          echo "Checking events..."
          kubectl get events -n test --sort-by='.lastTimestamp'
          
          # Describe deployment for detailed status and potential errors
          echo "Deployment details:"
          kubectl describe deployment/standard-app-deployment -n test
          
          # Check logs of any pods that exist
          echo "Pod logs (if available):"
          POD_NAME=$(kubectl get pods -n test -l app=standard-app -o jsonpath="{.items[0].metadata.name}" --ignore-not-found)
          if [ -n "$POD_NAME" ]; then
            kubectl logs $POD_NAME -n test --tail=50
          else
            echo "No pods found yet"
          fi
          
          # Wait with timeout for deployment to be ready
          echo "Waiting for deployment to be ready..."
          kubectl -n test rollout status deployment/standard-app-deployment --timeout=3m
          
          # Expose service for tests
          echo "Exposing service for tests..."
          kubectl -n test port-forward svc/standard-app-svc 5000:5000 &
          echo "Waiting for port-forward to establish..."
          sleep 5
          
          # Test the endpoint
          echo "Testing endpoint..."
          curl -s http://localhost:5000/health || echo "Health check failed"
      - name: Run integration tests
        run: |
          # Run the integration tests against the deployed app
          curl -s http://localhost:5000/health | grep healthy
          curl -s http://localhost:5000/livres | grep "Le DevOps c'est super !"
  
 ...
```

### 3.5 Stratégies de Déploiement Progressif

Pour des déploiements plus sûrs, vous pourrez implémenter des stratégies de déploiement progressif avec GitHub Actions et ArgoCD :

#### 1. Déploiement Canary

1. Créez un manifeste pour le déploiement canary dans `kubernetes/canary.yaml`

2. Ajoutez un job à votre workflow pour déployer d'abord en canary :

```yaml
  deploy-canary:
    needs: integration-test
    if: github.event_name != 'pull_request'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          repository: VOTRE_NOM_UTILISATEUR/argocd-demo-app
      - name: Update canary image
        run: |
          sed -i "s|image: .*/demo-app:.*$|image: ${{ secrets.HARBOR_URL }}/project-name/demo-app:${{ github.sha }}|g" kubernetes/canary.yaml
      - name: Commit and push canary changes
        run: |
          git config --global user.name "GitHub Actions"
          git config --global user.email "actions@github.com"
          git add kubernetes/canary.yaml
          git commit -m "Update canary to ${{ github.sha }}"
          git push
      - name: Wait for canary validation
        run: sleep 300 # Attendez 5 minutes ou utilisez une action pour attendre l'approbation manuelle
```

#### 2. Déploiement Blue/Green

Pour un déploiement blue/green, vous pouvez créer deux environnements identiques et basculer le trafic entre eux :

1. Créez des manifestes distincts pour les environnements blue et green
2. Configurez ArgoCD pour gérer les deux environnements
3. Utilisez GitHub Actions pour mettre à jour l'environnement inactif et basculer le trafic

<a name="argocd"></a>
## 4. ArgoCD - GitOps pour Kubernetes

### 4.0 Prérequis pour réaliser cette section 

Pour de réaliser cette partie, vous aurez besoin d'une adresse mail associée à un compte Google. 

En effet sur l'url https://argocd.cgicloudtoulouse.fr, vous aurez la possibilité de pouvoir vous connecter à l'application ArgoCD. Cependant, vous devez en amont positionner des droits. 

Cela se fait via un projet ArgoCD, qui est une entité permettant de gérer un ensemble d'applications. Il offre également la possibilité de définir divers droits et restrictions pour un meilleur contrôle des déploiements.

Parmi ces droits, on peut citer :

- La gestion des droits utilisateurs (RBAC propres à ArgoCD, distincts de ceux de Kubernetes).
- La mise en place de restrictions sur les ressources déployables.
- La définition de restrictions sur les dépôts GitHub autorisés.
- L'application de restrictions sur les namespaces dans lesquels une application peut être déployée.

Voici un exemple de projet

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AppProject
metadata:
  name: demo-standard
  namespace: argocd
spec:
  description: demo app to deploy
  clusterResourceWhitelist:
  # création de tout type de ressources
  - group: '*'
    kind: '*'
  destinations:
  # gestion des droits de déploiement uniquement dans ces namespaces
  - name: in-cluster
    namespace: standard-deployment
    server: https://kubernetes.default.svc
  # Limitation des repo sources
  sourceRepos:
  - https://github.com/Wariie/demo-app-cloud-toulouse.git
  roles:
  # mise en place des droits à partir des utilisateur ou de leurs groupes (cf: https://argo-cd.readthedocs.io/en/stable/operator-manual/rbac/#rbac-model-structure)
    - name: edit-demo
      description: Read Only privileges to simple user 
      policies:
        - p, proj:standard-app:edit-dev, applications, *, standard-app/*, allow
        - p, proj:standard-app:edit-dev, logs, *, standard-app/*, allow
        - p, proj:standard-app:edit-dev, repositories, *, standard-app/*, allow
      groups:
        - cgicloudtoulouse@gmail.com
```

### 4.1 Concepts d'ArgoCD

ArgoCD suit le modèle GitOps où :
- Git est la source unique de vérité pour votre infrastructure
- L'état souhaité est décrit de manière déclarative
- Les changements approuvés sont automatiquement appliqués au système
- Des agents logiciels détectent et corrigent les écarts par rapport à l'état souhaité

Concepts clés d'ArgoCD :
- **Application** : Un groupe de ressources Kubernetes
- **Projet** : Regroupement logique d'applications
- **Synchronisation** : Processus d'application de l'état Git au cluster
- **Santé** : Évaluation de l'état d'exécution de l'application
- **Vagues de Synchronisation** : Contrôle de l'ordre de création/suppression des ressources

### 4.2 Création d'une Application ArgoCD

Pour créer une application dans ArgoCD qui utilise des images de votre registre Harbor privé :

1. Forkez ce dépôt exemple : https://github.com/Wariie/demo-app-cloud-toulouse.git

2. Dans ce dossier, on retrouve un ensemble de fichier permettant de déployer simplement l'image créée auparavent. Ce projet helm comporte l'ensemble d'éléments suivants :
- Un deployment
- Un ingress GCP
- Un HPA
- Un service 
- Un ensemble de différents objets Crossplane (qui par défaut ne sont pas créés cf: Partie 5)

3. Créez une application ArgoCD via l'interface :

Faute d'accès au cluster Kubernetes, il est tout à fait possible de créer l'application ArgoCD depuis l'interface. 

Une application ArgoCD est défini par ArgoCD comme une Custom Resource (CR) :

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: standard-app
  namespace: argocd
spec:
  project: demo-standard
  source:
    repoURL: https://github.com/VOTRE_NOM_UTILISATEUR/demo-app-cloud-toulouse.git
    path: .
    targetRevision: HEAD
    helm:
      parameters:
        - name: crossplane.enabled
          value: 'true'
      valueFiles:
        - values.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: standard-deployment
  syncPolicy:
    syncOptions:
      - CreateNamespace=true
```
Il est aisé de retrouver ces différentes options pour ajouter une nouvelle application. 

Il est également possible d'utiliser les lignes de commande argocd pour arriver au même résultat :

```bash
argocd app create standard-app \
  --project demo-standard \
  --repo https://github.com/VOTRE_NOM_UTILISATEUR/demo-app-cloud-toulouse.git \
  --path . \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace standard-deployment \
  --sync-policy automated \
  --sync-option CreateNamespace=true \
  --values ./values.yaml
```

### 4.3 Stratégies de Synchronisation ArgoCD 

ArgoCD offre plusieurs stratégies de synchronisation :
- **Manuelle** : Les changements doivent être explicitement approuvés et déclenchés
- **Automatisée** : Les changements sont automatiquement appliqués lorsqu'ils sont détectés
- **Synchronisation Sélective** : Spécifiez les ressources à synchroniser

Autres fonctionnalités utiles d'ArgoCD :
- **Rollback** : Retour à un état précédent de l'application
- **Hooks de Synchronisation** : Opérations pré/post synchronisation
- **Élagage des Ressources** : Suppression des ressources qui ne sont plus dans Git

<a name="scenarios-atelier"></a>
## 5. Scénarios d'Atelier

Ce guide propose quatre scénarios pratiques qui vous permettront de mettre en application les concepts présentés précédemment :

### ⚠️ Note importante pour les participants

**Attention :** Les scénarios 5.1 et 5.2 utilisent le même dépôt source (`demo-app-cloud-toulouse.git`) avec des configurations différentes. Pour éviter les conflits lorsque vous suivez ces scénarios :

- **Option recommandée** : Utilisez des namespaces distincts pour chaque scénario
  ```bash
  # Scénario 5.1 - namespace: scenario1
  # Scénario 5.2 - namespace: scenario2
  ```

- **OU** créez une branche Git distincte pour chaque scénario
  ```bash
  git checkout -b scenario-5.1  # Pour le premier scénario
  git checkout -b scenario-5.2  # Pour le deuxième scénario
  
  # Puis spécifiez la branche dans ArgoCD avec --revision
  ```

- **OU** complétez entièrement un scénario, puis supprimez l'application avant de passer au suivant
  ```bash
  # Après avoir terminé le scénario 5.1
  argocd app delete standard-app
  kubectl delete namespace microservices
  ```

Choisissez l'approche qui vous convient le mieux selon votre niveau de confort avec Git et ArgoCD.

---

### 5.1 Scénario 1 : Déploiement d'une Application Standard avec ArgoCD

Dans ce scénario, vous déploierez une application REST simple en utilisant ArgoCD :

1. Forkez le dépôt : https://github.com/Wariie/demo-app-cloud-toulouse.git

2. Enregistrez l'application dans ArgoCD :
```bash
argocd app create standard-app \
  --project demo-standard
  --repo https://github.com/VOTRE_NOM_UTILISATEUR/demo-app-cloud-toulouse.git \
  --path . \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace microservices \
  --sync-policy automated \
  --self-heal \ 
  --values ./values.yaml
```

3. Explorez les composants et dépendances de l'application déployée

4. Effectuez une modification de configuration (par exemple, changez le nombre de réplicas) et observez le workflow GitOps en action

### 5.2 Scénario 2 : Déploiement d'une Application Standard avec PostgreSQL

Dans ce scénario, vous allez mettre en place une application qui interagit avec une base de données PostgreSQL :

1. Forkez le dépôt contenant l'application avec PostgreSQL : https://github.com/Wariie/demo-app-cloud-toulouse.git

2. Analysez l'architecture de l'application :
   - Frontend/API en Flask
   - Base de données PostgreSQL
   - Secrets Kubernetes pour les identifiants de la base de données

3. Créez une application ArgoCD pour déployer l'ensemble :
```bash
argocd app create standard-app-postgres \
  --project demo-standard
  --repo https://github.com/VOTRE_NOM_UTILISATEUR/demo-app-cloud-toulouse.git \
  --path . \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace postgres-demo \
  --sync-policy automated \
  --self-heal \
  --values ./values-postgres.yaml
```

4. Testez l'application et observez comment les différents composants interagissent entre eux

5. Explorez comment la gestion des secrets est réalisée dans un environnement GitOps sécurisé

### 5.3 Scénario 3 : Déploiement de Bookstack avec ArgoCD 

#TODO CHECK BOOKSTACK

Dans ce scénario, vous allez déployer Bookstack, une plateforme open-source de gestion de documentation basée sur Laravel :

1. Forkez le dépôt contenant les charts Helm pour Bookstack : https://github.com/Wariie/bookstack-k8s.git

2. Examinez les dépendances de Bookstack :
   - Application web PHP/Laravel
   - Base de données MySQL
   - Système de stockage pour les médias

3. Créez une application ArgoCD pour déployer Bookstack :
```bash
argocd app create bookstack \
  --repo https://github.com/VOTRE_NOM_UTILISATEUR/bookstack-k8s.git \
  --path helm \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace bookstack \
  --sync-policy automated \
  --self-heal \
  --helm-set mariadb.auth.rootPassword=rootpassword \
  --helm-set bookstack.password=mypassword
```

4. Accédez à l'interface Bookstack et créez quelques ressources documentaires

5. Explorez comment les volumes persistants sont gérés pour stocker les données et les médias

### 5.4 Scénario 4 : Pipeline CI/CD Complet avec GitHub Actions et ArgoCD

Dans ce scénario, vous implémenterez un pipeline CI/CD complet avec intégration entre GitHub Actions et ArgoCD :

1. Forkez le dépôt qui combine application et configuration : https://github.com/Wariie/demo-app-cloud-toulouse.git

   > **Note**: Bien que la séparation du code source et des manifestes de déploiement soit généralement une bonne pratique, ce dépôt unique simplifie la démonstration. Dans un environnement de production, envisagez de séparer ces préoccupations.

2. Examinez le workflow GitHub Actions déjà configuré :
   - Exécution de tests automatisés
   - Construction et publication d'une image Docker dans Harbor
   - Mise à jour automatique des manifestes Helm dans le même dépôt
   - Possibilité pour ArgoCD de détecter et d'appliquer les changements

3. Configurez ArgoCD pour surveiller et déployer depuis ce dépôt :
```bash
argocd app create demo-cicd \
  --repo https://github.com/VOTRE_NOM_UTILISATEUR/demo-app-cloud-toulouse.git \
  --path . \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace demo-cicd \
  --sync-policy automated \
  --values ./values.yaml
```

4. Effectuez une modification de code dans l'application :
   - Modifiez un endpoint ou ajoutez une fonctionnalité simple
   - Poussez les changements et observez le pipeline complet en action

5. Explorez le tableau de bord GitHub Actions et ArgoCD pour comprendre comment les différentes étapes s'enchaînent :
   - Le code est testé et validé
   - Une nouvelle image est construite et publiée dans Harbor
   - Les manifestes Helm sont mis à jour avec la nouvelle version d'image
   - ArgoCD détecte les changements et déploie automatiquement la nouvelle version

Ce scénario illustre l'intégration complète entre les phases CI (Intégration Continue) et CD (Déploiement Continu), en utilisant GitHub Actions et ArgoCD comme outils principaux.

<a name="crossplane"></a>
## 6. Crossplane pour gérer son infra applicative

### 6.1 Principes de Crossplane 

Crossplane est une solution permettant de déployer une infrastructure Cloud à travers Kubernetes. https://www.crossplane.io/

Pour fonctionner, Crossplane utilise les providers de Terraform et génère un exemple de CRD permettant de créer les ressources correspondant aux objets Cloud demandés. 

La mise en place de crossplane pour ce Workshop est effectué grâce aux fichiers suivant:
- **argocd-ref/templates/crossplane.yaml** qui permet de déployer la solution Crossplane en elle même 
- **argocd-ref/templates/crossplane-provider.yaml** qui permet de déployer les providers et prérequis pour créer des ressources Cloud avec Crossplane via le répertoire **crossplane-provider**

Le répertoire **crossplane-provider** contient les composants suivants :

- Les deux providers pour GCP et OVH. Ces derniers permettent de générer les CRD qui permettront de créer les ressources qui nous intéresserons plus tard. Ces providers sont trouvables sur le site upbound.com (par exemple pour gcp https://marketplace.upbound.io/providers/upbound/provider-gcp-compute/v1.8.3)
- Les provider config. Ces deux éléments permettent d'authentifier le cluster auprès des provider cloud. Les identifiants sont données en amont de ce workshop via la commande ```kubectl create secret generic ovh-secret-demo -n crossplane-system --from-file=creds=ovh.json``` à partir d'un fichier d'identifiant d'ovh par exemple. 
- Une function qui est un élément qui sert à la construction de Composition
- Une composition et sa définition d'un point de vue API. Ces éléments permettent de créer nos propres custom ressource sur Kubernetes un peu sur le même modèle que les modules terraform. C'est très pratique par exemple dans le cadre ou des ressources ont des dépendances (ex: une adresse ip et son entrée DNS)

### 6.2 Utilisation de Crossplane. 

Afin d'utiliser Crossplane, il va falloir modifier le projet ArgoCD créé en amont. Supprimez la ressource Ingress avant toute chose pour éviter les problèmes de déploiement avec Crossplane. 

En effet, il va falloir modifier la variable helm crossplane.enabled pour la passer a true. 

Cette modification va avoir pour effet de déployer une composition Crossplane. 

Cette composition Crossplane, déploie une adresse ip pour l'ingress gcp et fait un enregistrement DNS sur OVH. 

La base ayant permis la création de ces deux composant est présente dans le dossier **charts/standard-app**

Par exemple le fichier charts/standard-app/templates/ipanddns.yaml va contenir plusieurs ressources. 

Voici la ressource permettant de créer une adresse ip sur GCP :
```yaml
apiVersion: compute.gcp.upbound.io/v1beta1
kind: GlobalAddress
metadata:
  name: {{ include "clean-release-name" .  }}-ip
spec:
  forProvider:
    ipVersion: IPV4
  providerConfigRef:
    name: gcp-demo-provider-config
```

Afin de comprendre comment définir une ressource crossplane, une description api et potentiellement des exemples sont donnés pour chaque ressource dans la documentation associée sur Upbound. Par exemple pour cette ressource voici ce que nous avons : https://marketplace.upbound.io/providers/upbound/provider-gcp-compute/v1.8.3/resources/compute.gcp.upbound.io/GlobalAddress/v1beta1

Sinon, par défault, nous passons par une composition (cf: https://docs.crossplane.io/v2.0-preview/composition/composite-resource-definitions/). 
Celle-ci est définie par le fichier crossplane-provider/compositionipdns.yaml

La Custom Ressource est déployé via le fichier charts/standard-app/templates/ipanddns.yaml.

Ainsi via la composition une adresse ip est remontée, une fois créée cette dernière va être remontée à la CR qui va donner cette information à la ressource ZoneRecord (décrite par https://marketplace.upbound.io/providers/edixos/provider-ovh/v1.1.0/resources/dns.ovh.edixos.io/ZoneRecord/v1alpha1 )

Ainsi normalement il ne reste plus qu'à déployer et tester. 

ArgoCD, une fois configuré pour Crossplane, permet un suivi en temps réel du status des ressources. 

Cela est avantageux vis-à-vis d'un terraform car les ressources sont synchronisée en temps réel ce qu'il fait que la démarche GitOps est assurée en passant par cette méthode.

<a name="conclusion"></a>
## 7. Conclusion

Ce guide d'atelier vous a fourni une introduction complète aux pratiques modernes de déploiement et de gestion d'infrastructure avec des outils de pointe tels que ArgoCD, GitHub Workflows, Harbor et Crossplane. À travers les différentes sections, vous avez appris à mettre en place un pipeline CI/CD complet qui automatise l'ensemble du cycle de vie de vos applications, de leur développement à leur déploiement.

### Principaux concepts acquis

1. **GitOps avec ArgoCD** - Vous avez découvert comment utiliser Git comme source unique de vérité pour vos déploiements, permettant une gestion déclarative, versionnable et auditée de votre infrastructure. Le modèle GitOps facilite la collaboration, améliore la traçabilité et offre des mécanismes de rollback simples en cas de problème.

2. **Automation avec GitHub Actions** - L'automatisation des tests, du linting, des analyses de sécurité, de la construction d'images et des mises à jour de configuration vous permet d'accélérer les cycles de développement tout en maintenant un haut niveau de qualité et de sécurité dans votre code.

3. **Sécurité avec Harbor** - L'utilisation d'un registre privé comme Harbor vous permet de sécuriser vos images, d'appliquer des politiques de sécurité, de scanner les vulnérabilités et de maintenir la conformité de vos déploiements.

4. **Stratégies de déploiement avancées** - Vous avez exploré différentes stratégies comme les déploiements blue/green et canary qui vous permettent de réduire les risques associés aux mises en production tout en garantissant une expérience utilisateur optimale.

5. **Infrastructure as Code avec Crossplane** - Vous avez découvert comment Crossplane permet d'étendre les principes GitOps à l'infrastructure cloud elle-même, en utilisant les Custom Resources de Kubernetes pour provisionner et gérer des ressources cloud dans différents fournisseurs.

### Applications pratiques

Les scénarios d'atelier vous ont permis de mettre en pratique ces concepts dans des contextes concrets :
- Déploiement d'applications simples et de microservices
- Mise en place de pipelines CI/CD complets
- Gestion de multiples environnements (dev, staging, production)
- Création et gestion d'infrastructure cloud via Kubernetes

### Perspectives et prochaines étapes

Pour approfondir vos connaissances et améliorer encore vos pratiques DevOps, vous pourriez explorer :

1. **Observabilité** - Intégrer des solutions de monitoring, logging et tracing pour avoir une visibilité complète sur vos applications et votre infrastructure.

2. **Policy as Code** - Implémenter des politiques de sécurité et de conformité automatisées avec des outils comme Open Policy Agent (OPA) ou Kyverno.

3. **GitOps avancé** - Explorer des fonctionnalités plus avancées d'ArgoCD comme l'ApplicationSet pour gérer des applications à travers de multiples clusters ou environnements.

4. **Infrastructure avancée avec Crossplane** - Créer des compositions complexes pour provisionner des environnements complets avec un minimum d'intervention manuelle.

5. **Sécurité continue** - Mettre en place des pratiques de sécurité plus avancées comme le scanning d'images en continu, la signature d'images et la vérification d'intégrité.

### Mot de la fin

La mise en place d'un pipeline CI/CD moderne basé sur les principes GitOps représente un investissement significatif en temps et en ressources, mais les bénéfices en termes de productivité, de qualité et de fiabilité sont considérables. En automatisant le déploiement et la gestion de configuration, vous permettez à vos équipes de se concentrer sur ce qui apporte réellement de la valeur : le développement de nouvelles fonctionnalités et l'amélioration de l'expérience utilisateur.

N'oubliez pas que le voyage vers DevOps et GitOps est un processus d'amélioration continue. Commencez petit, mesurez vos progrès, et étendez progressivement vos pratiques à d'autres parties de votre organisation.

Nous espérons que cet atelier vous a fourni les connaissances et l'inspiration nécessaires pour commencer ou poursuivre votre parcours vers des pratiques de déploiement plus modernes et efficaces.

---