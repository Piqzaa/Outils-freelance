# Freelance Manager CLI

Outil CLI complet pour la gestion des devis, factures et contrats pour freelances en France.

## Installation

```bash
cd freelance-manager
pip install -e .
```

Ou sans installation :
```bash
pip install -r requirements.txt
python cli.py --help
```

## Configuration

Éditez `config.yaml` avec vos informations :

```yaml
freelance:
  nom: "Votre Nom"
  siret: "XXX XXX XXX XXXXX"
  adresse: "Votre adresse"
  email: "votre@email.com"
  # ...
```

## Commandes

### Clients

```bash
# Ajouter un client
freelance client add "ACME Corp" --siret "123456789" --email "contact@acme.com" --ville "Paris"

# Lister les clients
freelance client list

# Voir un client
freelance client show 1

# Modifier un client
freelance client edit 1 --email "nouveau@email.com"

# Supprimer un client
freelance client delete 1
```

### Devis

```bash
# Créer un devis (génère automatiquement le PDF)
freelance devis create 1 --tjm 300 --jours 5 --description "Développement API REST"

# Lister les devis
freelance devis list
freelance devis list --statut accepté

# Changer le statut
freelance devis statut 1 accepté

# Régénérer le PDF
freelance devis pdf 1
```

### Factures

```bash
# Créer une facture à partir d'un devis
freelance facture create --devis 1 --jours-effectifs 5 --date-debut 2024-01-15 --date-fin 2024-01-19

# Créer une facture sans devis
freelance facture create --client 1 --tjm 300 --jours-effectifs 3 --description "Support technique"

# Lister les factures
freelance facture list
freelance facture list --statut impayée

# Marquer comme payée
freelance facture statut 1 payée --date-paiement 2024-02-15
```

### Contrats

```bash
# Contrat en régie (le plus courant)
freelance contrat generate 1 --type regie --tjm 350 --duree-mois 6 --objet "Mission développement"

# Contrat au forfait
freelance contrat generate 1 --type forfait --tjm 300 --duree-jours 20 --montant 6000

# Mission courte (1-5 jours)
freelance contrat generate 1 --type mission --tjm 400 --duree-jours 2
```

### Statistiques

```bash
# Dashboard complet
freelance stats

# Stats pour une année spécifique
freelance stats --annee 2023
```

### Exports

```bash
# Export CSV (pour compta)
freelance export csv --type all

# Export Excel avec récapitulatif
freelance export excel --annee 2024
```

## Structure des documents générés

```
output/
├── DEVIS-2024-001.pdf
├── DEVIS-2024-002.pdf
├── FACT-2024-001.pdf
├── FACT-2024-002.pdf
├── CONT-2024-001_regie.docx
├── clients_20240115.csv
└── comptabilite_2024.xlsx
```

## Mentions légales incluses

- TVA non applicable (art. 293 B du CGI) pour micro-entreprise
- Pénalités de retard (taux légal + 40€ frais recouvrement)
- Escompte pour paiement anticipé
- Numérotation chronologique obligatoire
- Toutes les mentions requises par la loi française

## Seuil micro-entreprise

Le dashboard affiche une alerte quand vous approchez du seuil de CA (77 700 €).
