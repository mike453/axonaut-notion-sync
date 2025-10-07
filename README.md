# Axonaut to Notion Sync

Script de synchronisation automatique des factures et paiements depuis Axonaut vers Notion.

## 🎯 Fonctionnalités

- ✅ Synchronise les factures Axonaut → Notion
- ✅ Synchronise les paiements Axonaut → Notion
- ✅ Détection automatique des doublons (mise à jour au lieu de création)
- ✅ Gestion d'erreurs complète
- ✅ Logs détaillés
- ✅ Exécution automatique via CRON

## 🚀 Déploiement sur Railway

### Prérequis

- Compte Railway (gratuit : https://railway.app)
- Clé API Axonaut
- IDs des bases Notion (Factures et Paiements)

### Étapes

1. **Créer un nouveau projet sur Railway**
   - Allez sur https://railway.app
   - Cliquez sur "New Project"
   - Choisissez "Deploy from GitHub repo"
   - Sélectionnez ce repository

2. **Configurer les variables d'environnement**
   
   Dans Railway, ajoutez ces 3 variables :
   
   | Variable | Description |
   |----------|-------------|
   | `AXONAUT_CABA_API_KEY` | Votre clé API Axonaut |
   | `NOTION_INVOICES_DB_ID` | ID de votre base Factures dans Notion |
   | `NOTION_PAYMENTS_DB_ID` | ID de votre base Paiements dans Notion |

3. **Déployer**
   
   Railway va automatiquement :
   - Installer Python et les dépendances
   - Configurer le CRON job (toutes les 30 min, 9h-18h, lundi-vendredi)
   - Démarrer le service

## ⚙️ Configuration

### Modifier le Schedule CRON

Éditez `railway.json` :

```json
{
  "deploy": {
    "cronSchedule": "*/30 9-18 * * 1-5"
  }
}
```

**Exemples de schedules :**

| Schedule | Description |
|----------|-------------|
| `*/15 * * * *` | Toutes les 15 minutes, 24/7 |
| `0 8 * * *` | Tous les jours à 8h |
| `0 */2 * * *` | Toutes les 2 heures |
| `0 9-17 * * 1-5` | Toutes les heures de 9h à 17h, lundi-vendredi |

### Mode Dry Run

Pour tester sans modifier Notion :

```bash
export DRY_RUN=true
python3 sync_axonaut_notion.py
```

## 📊 Structure des Données

### Base Factures (Notion)

| Propriété | Type | Source Axonaut |
|-----------|------|----------------|
| Numéro | Title | `number` |
| ID Facture Axonaut | Number | `id` |
| Montant TTC | Number | `amount_ttc` |
| Montant HT | Number | `amount_ht` |
| Date Facture | Date | `date` |
| Date Échéance | Date | `due_date` |
| Statut | Select | `status` |
| Référence Client | Text | `client_reference` |

### Base Paiements (Notion)

| Propriété | Type | Source Axonaut |
|-----------|------|----------------|
| Référence | Title | `reference` |
| ID Paiement Axonaut | Number | `id` |
| ID Facture Axonaut | Number | `invoice_id` |
| Montant | Number | `amount` |
| Date Paiement | Date | `date` |
| Méthode | Select | `nature` |

## 📝 Logs

Le script génère des logs détaillés :

```
[2025-10-07 14:30:00] INFO: ============================================================
[2025-10-07 14:30:00] INFO: Démarrage de la synchronisation Axonaut → Notion
[2025-10-07 14:30:00] INFO: ============================================================
[2025-10-07 14:30:01] INFO: Récupération des factures depuis Axonaut...
[2025-10-07 14:30:02] INFO: ✓ 10 factures récupérées
[2025-10-07 14:30:03] ✅ SUCCESS: Facture INV-001 créée
[2025-10-07 14:30:04] ✅ SUCCESS: Facture INV-002 mise à jour
...
[2025-10-07 14:30:15] INFO: ============================================================
[2025-10-07 14:30:15] INFO: Synchronisation terminée
[2025-10-07 14:30:15] INFO: Factures synchronisées : 10
[2025-10-07 14:30:15] INFO: Paiements synchronisés : 5
[2025-10-07 14:30:15] INFO: ============================================================
```

## 🛠️ Développement Local

### Installation

```bash
pip install -r requirements.txt
```

### Configuration

Créez un fichier `.env` :

```env
AXONAUT_CABA_API_KEY=votre_cle_api
NOTION_INVOICES_DB_ID=id_base_factures
NOTION_PAYMENTS_DB_ID=id_base_paiements
DRY_RUN=true
```

### Exécution

```bash
python3 sync_axonaut_notion.py
```

## 💰 Coûts

**Railway Plan Gratuit :**
- 500 heures d'exécution/mois
- Votre usage : ~1 heure/mois
- **= GRATUIT ! ✅**

## 📞 Support

En cas de problème :
1. Vérifiez les logs dans Railway
2. Vérifiez que les variables d'environnement sont correctes
3. Vérifiez que vos clés API sont valides

## 📄 Licence

MIT

## 👤 Auteur

Mickaël Chartier - 2025
