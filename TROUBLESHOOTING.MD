## Guide de Dépannage

### 1. Dépannage d'ArgoCD

Problèmes courants d'ArgoCD et leurs solutions :

1. **Application désynchronisée**
   - Vérifiez le statut de l'application : `argocd app get <nomapp>`
   - Comparez avec Git : `argocd app diff <nomapp>`
   - Forcez la synchronisation si nécessaire : `argocd app sync <nomapp> --force`
   - Vérifiez si des hooks sont bloqués : `argocd app terminate-op <nomapp>`

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

4. **Correction des problèmes de synchronisation persistants**
   - Essayez la synchronisation avec remise à zéro : `argocd app sync <app-name> --force --prune`
   - Vérifiez les hooks de synchronisation personnalisés qui pourraient échouer
   - Vérifiez les erreurs de validation des schémas Kubernetes
   - Si nécessaire, supprimez et recréez l'application ArgoCD
   
5. **Optimisation des performances**
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