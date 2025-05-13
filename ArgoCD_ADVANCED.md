## Utilisation Avancée d'ArgoCD

### 1 Application des Applications (App of Apps)

Le pattern "Application des Applications" est une approche puissante pour gérer de multiples applications avec ArgoCD :

```yaml
# parent-app.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: applications-parent
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/VOTRE_NOM_UTILISATEUR/argocd-apps.git
    targetRevision: HEAD
    path: apps
  destination:
    server: https://kubernetes.default.svc
    namespace: argocd
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

Cette application parent pointe vers un répertoire contenant plusieurs définitions d'applications enfants, ce qui permet une gestion hiérarchique des déploiements.

### 2 Gestion des Secrets avec Sealed Secrets

ArgoCD suit le principe GitOps où tout est stocké dans Git, mais les secrets posent un problème de sécurité. Sealed Secrets de Bitnami résout ce problème :

1. Installez l'outil client `kubeseal` :
```bash
# MacOS
brew install kubeseal

# Linux
wget https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.19.0/kubeseal-0.19.0-linux-amd64.tar.gz
tar -xvzf kubeseal-0.19.0-linux-amd64.tar.gz
sudo install -m 755 kubeseal /usr/local/bin/kubeseal
```

2. Installez le contrôleur Sealed Secrets dans le cluster :
```bash
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.19.0/controller.yaml
```

3. Créez un secret scellé :
```bash
# Créez d'abord un secret standard
kubectl create secret generic db-credentials --from-literal=username=admin --from-literal=password=s3cr3t --dry-run=client -o yaml > db-credentials.yaml

# Scellez le secret
kubeseal --format yaml < db-credentials.yaml > sealed-db-credentials.yaml
```

4. Ajoutez le secret scellé à votre dépôt Git et laissez ArgoCD le déployer.

### 3 Déploiements Progressifs avec Argo Rollouts

Argo Rollouts étend les capacités de déploiement de Kubernetes avec des stratégies avancées :

1. Installez Argo Rollouts :
```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
```

2. Créez un Rollout au lieu d'un Deployment :
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: mon-application
spec:
  replicas: 5
  strategy:
    canary:
      steps:
      - setWeight: 20
      - pause: {duration: 1h}
      - setWeight: 40
      - pause: {duration: 1h}
      - setWeight: 60
      - pause: {duration: 1h}
      - setWeight: 80
      - pause: {duration: 1h}
  revisionHistoryLimit: 2
  selector:
    matchLabels:
      app: mon-application
  template:
    metadata:
      labels:
        app: mon-application
    spec:
      containers:
      - name: mon-application
        image: mon-image:1.0
        ports:
        - containerPort: 8080
```

ArgoCD peut gérer ces ressources personnalisées comme n'importe quelle autre ressource Kubernetes.

### 4 Notifications et Intégrations

ArgoCD peut envoyer des notifications sur différents événements :

1. Installez le contrôleur de notifications :
```bash
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj-labs/argocd-notifications/stable/manifests/install.yaml
```

2. Configurez les intégrations (exemple pour Slack) :
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-notifications-cm
  namespace: argocd
data:
  service.slack: |
    token: $slack-token
  template.app-sync-status: |
    message: |
      Application {{.app.metadata.name}} sync status is {{.app.status.sync.status}}
      {{if eq .app.status.sync.status "Synced"}}:white_check_mark:{{end}}
      {{if eq .app.status.sync.status "OutOfSync"}}:warning:{{end}}
      {{if eq .app.status.sync.status "Unknown"}}:question:{{end}}
  trigger.on-sync-status-change: |
    - when: app.status.sync.status == 'Synced'
      send: [app-sync-status]
    - when: app.status.sync.status == 'OutOfSync'
      send: [app-sync-status]
```

3. Configurez l'application pour recevoir des notifications :
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: mon-application
  namespace: argocd
  annotations:
    notifications.argoproj.io/subscribe.on-sync-status-change.slack: mon-canal-slack
# ...le reste de la définition
```

### 5 Gestion Multi-Clusters

ArgoCD peut gérer des applications sur plusieurs clusters :

1. Ajoutez un cluster distant à ArgoCD :
```bash
argocd cluster add nom-contexte-distant
```

2. Déployez une application vers ce cluster :
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: application-distante
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/VOTRE_NOM_UTILISATEUR/mon-app.git
    targetRevision: HEAD
    path: kubernetes
  destination:
    server: https://URL-API-CLUSTER-DISTANT
    namespace: default
```

Cette approche permet une gestion centralisée des déploiements sur une infrastructure distribuée.

### 6 Intégration de GitHub Webhooks avec ArgoCD

Pour optimiser la réactivité d'ArgoCD aux changements dans vos dépôts Git, configurez des webhooks GitHub :

1. Configurez le service ArgoCD pour être accessible depuis Internet (ou utilisez un tunneling comme ngrok pour les tests)

2. Dans votre dépôt GitHub, accédez à Settings > Webhooks > Add webhook :
   - **Payload URL** : https://votre-argocd-server/api/webhook
   - **Content type** : application/json
   - **Secret** : Créez un secret partagé
   - **Events** : Sélectionnez "Just the push event"

3. Configurez ArgoCD pour accepter le webhook :
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-cm
  namespace: argocd
data:
  webhook.github.secret: votre-secret-partagé
```

4. Testez la configuration en effectuant un push dans votre dépôt et en observant la réponse rapide d'ArgoCD.

### 7 GitOps avec GitHub Pull Requests

Implémentez une approche GitOps plus contrôlée en utilisant les Pull Requests GitHub :

1. Créez une branche protégée pour chaque environnement (ex. dev, staging, prod)

2. Configurez des règles de protection de branche :
   - Exigez des examens de pull request avant de fusionner
   - Exigez des statuts de vérification réussis avant la fusion
   - Limitez qui peut pousser vers la branche

3. Configurez ArgoCD pour surveiller ces branches spécifiques :
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: prod-application
  namespace: argocd
spec:
  source:
    repoURL: https://github.com/VOTRE_NOM_UTILISATEUR/votre-repo.git
    targetRevision: prod  # Branche protégée
    path: kubernetes
  # Reste de la configuration...
```

4. Utilisez GitHub Actions pour automatiser les validations et les tests sur les pull requests :
```yaml
name: PR Validation

on:
  pull_request:
    branches: [ prod ]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Validate Kubernetes manifests
        run: |
          # Installation de kubeval
          wget https://github.com/instrumenta/kubeval/releases/latest/download/kubeval-linux-amd64.tar.gz
          tar xf kubeval-linux-amd64.tar.gz
          sudo cp kubeval /usr/local/bin
          
          # Validation des manifestes
          kubeval --strict kubernetes/*.yaml
          
      - name: Verify Harbor image security
        run: |
          # Vérifiez que l'image référencée a été scannée et n'a pas de vulnérabilités critiques
          # Extraction du tag d'image du manifeste
          IMAGE_TAG=$(grep -o "${{ secrets.HARBOR_URL }}/project-name/demo-app:[^\"]*" kubernetes/deployment.yaml | head -1)
          
          # Vérification des vulnérabilités via l'API Harbor
          curl -s -u "${{ secrets.HARBOR_USERNAME }}:${{ secrets.HARBOR_PASSWORD }}" \
            "https://${{ secrets.HARBOR_URL }}/api/v2.0/projects/project-name/repositories/demo-app/artifacts/$(echo $IMAGE_TAG | cut -d: -f2)/vulnerabilities" > vuln.json
            
          # Échec si des vulnérabilités critiques sont trouvées
          CRITICAL_COUNT=$(jq '.vulnerabilities[] | select(.severity=="Critical") | .id' vuln.json | wc -l)
          if [ "$CRITICAL_COUNT" -gt "0" ]; then
            echo "L'image contient $CRITICAL_COUNT vulnérabilités critiques!"
            exit 1
          fi
```

Cette approche assure une gouvernance plus stricte des changements tout en maintenant les avantages du GitOps.

### 8 Configuration de Harbor pour l'intégration avec ArgoCD et GitHub Actions

Pour optimiser l'intégration de votre registre Harbor privé avec ArgoCD et GitHub Actions, suivez ces étapes :

1. **Création d'un robot account dans Harbor** :
   - Connectez-vous à l'interface Harbor
   - Accédez à votre projet > Robot Accounts > New Robot Account
   - Donnez-lui un nom descriptif (ex: `github-actions-robot`)
   - Accordez les permissions `push`, `pull` et `list` sur les artefacts
   - Copiez le token généré pour l'utiliser dans GitHub Actions

2. **Configuration de règles de rétention d'images** :
   - Configurez des règles de rétention dans Harbor pour gérer automatiquement le cycle de vie des images
   - Par exemple, conservez uniquement les 10 dernières versions des images de développement
   - Conservez toutes les versions des images de production

3. **Activation du scanner de vulnérabilités Harbor** :
   - Activez le scanner intégré dans Harbor (Trivy ou Clair)
   - Configurez des règles de blocage des images vulnérables en fonction de la sévérité

4. **Vérification des images avant déploiement** :
   - Ajoutez une étape dans votre workflow GitHub Actions pour vérifier la sécurité des images
   ```yaml
   verify-image-security:
     needs: build
     runs-on: ubuntu-latest
     steps:
       - name: Check image vulnerabilities
         run: |
           # Utilisation de l'API Harbor pour vérifier les vulnérabilités
           VULN_COUNT=$(curl -s -u "${{ secrets.HARBOR_USERNAME }}:${{ secrets.HARBOR_PASSWORD }}" \
             "https://${{ secrets.HARBOR_URL }}/api/v2.0/projects/project-name/repositories/demo-app/artifacts/${{ github.sha }}/vulnerabilities" | \
             jq '.vulnerabilities | length')
           
           if [ "$VULN_COUNT" -gt "10" ]; then
             echo "Image contient trop de vulnérabilités ($VULN_COUNT trouvées)"
             exit 1
           fi
   ```

5. **Intégration de Harbor avec ArgoCD pour l'authentification** :
   - Créez un secret Kubernetes contenant les identifiants Harbor
   ```bash
   kubectl create secret docker-registry harbor-creds \
     --namespace argocd \
     --docker-server=$HARBOR_URL \
     --docker-username=$HARBOR_USERNAME \
     --docker-password=$HARBOR_PASSWORD
   ```
   
   - Configurez ArgoCD pour utiliser ce secret
   ```yaml
   apiVersion: v1
   kind: ConfigMap
   metadata:
     name: argocd-cm
     namespace: argocd
   data:
     dex.config: |
       connectors:
         - type: dockerRegistry
           name: harbor
           config:
             useLoginAsID: true
             registryURL: harbor.example.com
   ```

6. **Mise en place de webhooks Harbor vers ArgoCD** :
   - Configurez des webhooks dans Harbor pour notifier ArgoCD lorsque de nouvelles images sont publiées
   - Cela permet une synchronisation plus rapide lorsque de nouvelles versions sont disponibles

Cette configuration complète assure un flux de travail sécurisé et automatisé entre votre code source, le registre Harbor et le déploiement sur Kubernetes via ArgoCD.

### 9 Gestion des Environnements Multi-Cloud avec ArgoCD et Harbor

Pour les organisations qui opèrent dans plusieurs environnements cloud, il est crucial d'établir une stratégie de déploiement cohérente. Voici comment configurer ArgoCD et Harbor pour gérer efficacement les déploiements multi-cloud :

1. **Structure de Projet Harbor Multi-Environnement** :
   - Créez une structure de projets dans Harbor qui reflète vos environnements :
     - `project-name/dev` - Images pour l'environnement de développement
     - `project-name/staging` - Images pour l'environnement de staging
     - `project-name/prod` - Images pour l'environnement de production
   - Appliquez des politiques de sécurité et d'accès différentes selon l'environnement

2. **Configuration ArgoCD Multi-Cluster** :
   - Ajoutez plusieurs clusters à ArgoCD :
   ```bash
   # Ajout d'un cluster AWS
   argocd cluster add aws-eks-cluster-context
   
   # Ajout d'un cluster GCP
   argocd cluster add gcp-gke-cluster-context
   
   # Ajout d'un cluster Azure
   argocd cluster add azure-aks-cluster-context
   ```

3. **Applications ArgoCD pour Chaque Environnement/Cloud** :
   ```yaml
   # Application pour environnement de dev sur AWS
   apiVersion: argoproj.io/v1alpha1
   kind: Application
   metadata:
     name: demo-app-dev-aws
   spec:
     project: default
     source:
       repoURL: https://github.com/VOTRE_NOM_UTILISATEUR/argocd-demo-app.git
       targetRevision: main
       path: overlays/dev/aws
     destination:
       server: https://kubernetes.default.svc  # URL du cluster AWS
       namespace: dev
     syncPolicy:
       automated:
         prune: true
         selfHeal: true
   
   # Application pour environnement de prod sur GCP
   apiVersion: argoproj.io/v1alpha1
   kind: Application
   metadata:
     name: demo-app-prod-gcp
   spec:
     project: default
     source:
       repoURL: https://github.com/VOTRE_NOM_UTILISATEUR/argocd-demo-app.git
       targetRevision: main
       path: overlays/prod/gcp
     destination:
       server: https://[URL_API_CLUSTER_GCP]
       namespace: prod
     syncPolicy:
       automated:
         prune: true
         selfHeal: true
   ```

4. **Configuration de Replications Harbor entre Régions** :
   - Configurez la réplication des images entre différentes instances Harbor déployées dans différentes régions
   - Cela permet une haute disponibilité et réduit la latence lors du déploiement
   ```yaml
   # Exemple de configuration de réplication dans Harbor
   {
     "name": "prod-image-replication",
     "dest_registry": {
       "url": "https://harbor-eu-west.example.com",
       "name": "eu-west-harbor"
     },
     "trigger": {
       "type": "event_based"
     },
     "filters": [{
       "type": "name",
       "value": "project-name/prod/**"
     }]
   }
   ```

5. **Workflow CI/CD pour le Déploiement Multi-Cloud** :
   ```yaml
   # Job supplémentaire dans votre workflow GitHub Actions
   deploy-multi-region:
     needs: [integration-test]
     runs-on: ubuntu-latest
     steps:
       - uses: actions/checkout@v3
         with:
           repository: VOTRE_NOM_UTILISATEUR/argocd-demo-app
           token: ${{ secrets.GH_PAT }}
           
       - name: Update image tags for all regions
         run: |
           # Mise à jour pour AWS
           sed -i "s|image: .*/demo-app:.*$|image: ${{ secrets.HARBOR_URL }}/project-name/prod/demo-app:${{ github.sha }}|g" overlays/prod/aws/kustomization.yaml
           
           # Mise à jour pour GCP
           sed -i "s|image: .*/demo-app:.*$|image: ${{ secrets.HARBOR_URL }}/project-name/prod/demo-app:${{ github.sha }}|g" overlays/prod/gcp/kustomization.yaml
           
           # Mise à jour pour Azure
           sed -i "s|image: .*/demo-app:.*$|image: ${{ secrets.HARBOR_URL }}/project-name/prod/demo-app:${{ github.sha }}|g" overlays/prod/azure/kustomization.yaml
           
       - name: Commit and push changes
         run: |
           git config --global user.name "GitHub Actions"
           git config --global user.email "actions@github.com"
           git add .
           git commit -m "Update image to ${{ github.sha }} across all cloud providers"
           git push
   ```

6. **Tableau de Bord de Surveillance Multi-Cloud** :
   - Intégrez ArgoCD avec un outil de surveillance comme Prometheus et Grafana
   - Créez un tableau de bord qui montre l'état de synchronisation de toutes vos applications à travers les différents clouds
   - Ajoutez des alertes pour les échecs de déploiement ou désynchronisations

Cette architecture permet de maintenir la cohérence des déploiements à travers différents fournisseurs cloud tout en tirant parti des avantages spécifiques de chaque plateforme.
