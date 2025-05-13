## Guide de Dépannage

### 1. Dépannage d'ArgoCD

Problèmes courants d'ArgoCD et leurs solutions :

1. **Application désynchronisée**
   - Vérifiez le statut de l'application : `argocd app get <nomapp>`
   - Comparez avec Git : `argocd app diff <nomapp>`
   - Forcez la synchronisation si nécessaire : `argocd app sync <nomapp> --force`
   - Vérifiez si des hooks sont bloqués : `argocd app terminate-op <nomapp>`

2. **Problèmes d'authentification**
   - Réinitialisez le mot de passe admin : `argocd account update-password`
   - Vérifiez les paramètres RBAC dans le ConfigMap d'ArgoCD
   - Vérifiez l'accès au dépôt Git : `argocd repo list` et `argocd repo get <URL_REPO>`

3. **Échecs de synchronisation avec images Harbor**
   - Vérifiez que le secret d'extraction d'image est correctement configuré
   - Assurez-vous que la référence d'image dans les manifestes correspond exactement à la structure du registre Harbor
   - Vérifiez que le robot account Harbor a les permissions suffisantes
   - Examinez les logs du pod ArgoCD : `kubectl logs -n argocd deployment/argocd-application-controller`

4. **Problèmes de performances d'ArgoCD**
   - Augmentez les ressources du contrôleur d'application : `kubectl -n argocd patch deployment argocd-application-controller -p '{"spec":{"template":{"spec":{"containers":[{"name":"argocd-application-controller","resources":{"limits":{"cpu":"2","memory":"4Gi"},"requests":{"cpu":"1","memory":"2Gi"}}}]}}}}'`
   - Ajustez le paramètre `ARGOCD_CONTROLLER_REPLICAS` pour les grands clusters
   - Utilisez le mode "server-side apply" pour les grands déploiements : `--server-side` dans la commande sync

5. **Erreurs de certificat SSL avec Harbor**
   - Ajoutez le certificat CA de Harbor au certificat TLS de confiance d'ArgoCD
   ```bash
   kubectl -n argocd create configmap harbor-ca-cert --from-file=ca.crt=/path/to/harbor/ca.crt
   kubectl -n argocd patch deployment argocd-repo-server -p '{"spec":{"template":{"spec":{"volumes":[{"name":"harbor-ca-cert","configMap":{"name":"harbor-ca-cert","items":[{"key":"ca.crt","path":"ca.crt"}]}}],"containers":[{"name":"argocd-repo-server","volumeMounts":[{"name":"harbor-ca-cert","mountPath":"/etc/ssl/certs/harbor-ca.crt","subPath":"ca.crt"}]}]}}}}'
   ```

### 2. Dépannage des Workflows GitHub

1. **Les Actions GitHub échouent**
   - Vérifiez les logs d'exécution dans l'onglet "Actions" de votre dépôt
   - Assurez-vous que tous les secrets nécessaires sont configurés
   - Vérifiez les permissions des actions et des tokens
   - Testez les commandes problématiques localement pour reproduire le problème

2. **Les images ne sont pas publiées sur Harbor**
   - Vérifiez les identifiants Harbor dans les secrets GitHub
   - Assurez-vous que votre compte Harbor a les permissions nécessaires sur le projet
   - Vérifiez que l'URL du registre Harbor est correcte et accessible
   - Vérifiez les logs d'exécution pour les erreurs de construction ou d'authentification
   - Essayez de vous connecter au registre Harbor manuellement pour confirmer l'accès
   - Vérifiez les quotas et limitations du projet Harbor

3. **Les mises à jour de manifestes ne sont pas appliquées**
   - Vérifiez que le job de mise à jour a les permissions nécessaires pour pousser vers le dépôt
   - Vérifiez que les commandes sed ciblent correctement les bonnes lignes
   - Vérifiez les commit logs dans le dépôt de configuration
   - Essayez d'exécuter les commandes manuellement pour tester le processus

4. **Erreurs de construction d'image**
   - Vérifiez l'espace disponible pour les actions GitHub
   - Examinez le Dockerfile pour repérer d'éventuelles erreurs
   - Vérifiez si les dépendances sont accessibles pendant la construction
   - Utilisez la stratégie de mise en cache pour accélérer les constructions

5. **Problèmes de sécurité dans le workflow**
   - Évitez d'exposer les secrets directement dans les logs
   - Utilisez des environnements GitHub pour isoler les secrets sensibles
   - Limitez les permissions des tokens GitHub au strict nécessaire
   - Utilisez des jobs conditionnels pour les déploiements en production

### 3. Dépannage de l'Intégration CI/CD

1. **Le pipeline complet ne fonctionne pas**
   - Vérifiez chaque étape individuellement
   - Assurez-vous que les dépendances entre les jobs sont correctement définies
   - Testez le workflow localement lorsque possible
   - Utilisez des timeouts appropriés pour éviter les blocages indéfinis

2. **ArgoCD ne détecte pas les changements**
   - Vérifiez la configuration du polling d'ArgoCD
   - Configurez des webhooks pour les notifications immédiates
   - Vérifiez que les branches surveillées sont correctes
   - Vérifiez les logs d'ArgoCD pour les erreurs de synchronisation
   - Assurez-vous que le format des manifestes est correct
   
3. **Problèmes avec les secrets et les accès**
   - Vérifiez que les PAT GitHub et autres tokens ont les bonnes permissions
   - Assurez-vous que les secrets sont correctement référencés dans les workflows
   - Renouvelez les tokens expirés
   - Utilisez des secrets à durée limitée lorsque possible
   - Rotez régulièrement les credentials pour maintenir la sécurité

4. **Problèmes spécifiques à Harbor**
   - Vérifiez l'état du service Harbor : `curl -k https://$HARBOR_URL/api/v2.0/health`
   - Examinez les quotas de stockage Harbor
   - Vérifiez les règles de rétention et de nettoyage
   - Diagnostiquez les problèmes de performance du registry
   ```bash
   # Vérification du temps de réponse de Harbor
   time curl -k -s -o /dev/null https://$HARBOR_URL/v2/
   
   # Vérification de la disponibilité de l'image
   curl -k -s https://$HARBOR_URL/v2/project-name/demo-app/manifests/latest
   ```

5. **Correction des problèmes de synchronisation persistants**
   - Essayez la synchronisation avec remise à zéro : `argocd app sync <app-name> --force --prune`
   - Vérifiez les hooks de synchronisation personnalisés qui pourraient échouer
   - Vérifiez les erreurs de validation des schémas Kubernetes
   - Si nécessaire, supprimez et recréez l'application ArgoCD
   
6. **Optimisation des performances**
   - Utilisez des stratégies de mise en cache pour les builds Docker
   - Configurez des images de base communes pour réduire le temps de build
   - Utilisez des runners auto-hébergés pour GitHub Actions si les builds sont lents
   - Optimisez la taille des images Docker en utilisant des images multi-étages

### 4. Stratégies de Résolution Avancée

Pour les problèmes complexes impliquant Harbor, ArgoCD et GitHub Actions, utilisez ces approches systématiques :

1. **Création d'un environnement de debugging**
   - Créez un namespace dédié pour tester les déploiements : `kubectl create namespace debug`
   - Déployez une version simplifiée de votre application pour isoler les problèmes
   - Utilisez des outils comme `ksniff` pour capturer le trafic réseau entre les composants

2. **Récupération après échec catastrophique**
   - Maintenez des sauvegardes de vos configurations ArgoCD :
   ```bash
   # Sauvegarde des configurations ArgoCD
   kubectl -n argocd get applications -o yaml > argocd-apps-backup.yaml
   kubectl -n argocd get appprojects -o yaml > argocd-projects-backup.yaml
   ```
   - Documentez les étapes de restauration complète du pipeline
   - Préparez des scripts d'urgence pour réinitialiser les accès et permissions

3. **Analyse détaillée des problèmes persistants**
   - Utilisez des outils comme `kubectl-debug` pour analyser les conteneurs en cours d'exécution
   - Activez le mode debug d'ArgoCD en modifiant le niveau de log
   ```bash
   kubectl -n argocd patch configmap/argocd-cmd-params-cm \
     --type=merge \
     -p='{"data":{"repo-server.log.level":"debug", "controller.log.level":"debug"}}'
   ```
   - Créez un conteneur éphémère pour tester l'interaction directe avec Harbor
   ```bash
   kubectl run harbor-debug --rm -it --image=curlimages/curl -- sh
   # Dans le conteneur
   curl -k -u "$HARBOR_USER:$HARBOR_PASSWORD" https://harbor.example.com/api/v2.0/projects
   ```

4. **Audit de sécurité du pipeline**
   - Vérifiez régulièrement les permissions dans GitHub, ArgoCD et Harbor
   - Auditez les secrets utilisés dans le pipeline
   - Utilisez l'outil `cosign` pour vérifier les signatures d'images
   ```bash
   cosign verify --key cosign.pub harbor.example.com/project-name/demo-app:latest
   ```
   - Exécutez des scans de vulnérabilités réguliers sur l'infrastructure CI/CD

5. **Documentation et partage des solutions**
   - Maintenez un document de "connaissances" pour l'équipe
   - Créez des runbooks pour les problèmes courants
   - Organisez régulièrement des sessions de partage d'expérience
   - Automatisez la détection et la résolution des problèmes récurrents

Cette approche structurée aide à résoudre efficacement les problèmes complexes et à améliorer progressivement la stabilité de votre pipeline CI/CD.

### 5. Gestion des Environnements Multi-Cloud avec ArgoCD et Harbor

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

Cette architecture permet de maintenir la cohérence des déploiements à travers différents fournisseurs cloud tout en tirant parti des avantages spécifiques de chaque plateforme.### 6.8 Configuration de Harbor pour l'intégration avec ArgoCD et GitHub Actions



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

Cette configuration complète assure un flux de travail sécurisé et automatisé entre votre code source, le registre Harbor et le déploiement sur Kubernetes via ArgoCD.# Gestion des Déploiements avec ArgoCD et GitHub Workflows