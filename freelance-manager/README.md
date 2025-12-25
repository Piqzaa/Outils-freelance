# Freelance Manager

Outil complet pour la gestion des **devis**, **factures** et **contrats** pour freelances en France.

Disponible en :
- **Interface Web** (recommandée) - Dashboard visuel avec graphiques
- **CLI** (ligne de commande) - Pour automatisation et usage rapide

---

## Prérequis

- **Python 3.10+** installé sur votre machine
- **pip** (gestionnaire de paquets Python)

### Vérifier votre version de Python

```bash
python --version
```

Si Python n'est pas installé, téléchargez-le sur : https://www.python.org/downloads/

---

## Installation (étape par étape)

### 1. Ouvrir un terminal

- **Windows** : Ouvrir PowerShell ou CMD
- **Mac** : Ouvrir Terminal
- **Linux** : Ouvrir votre terminal

### 2. Se placer dans le dossier du projet

```bash
cd chemin/vers/freelance-manager
```

Exemple Windows :
```bash
cd "C:\Users\VotreNom\Documents\freelance-manager"
```

### 3. Installer les dépendances Python

```bash
pip install -r requirements.txt
```

Cette commande installe automatiquement :
- `Flask` - Serveur web
- `ReportLab` - Génération de PDF
- `python-docx` - Génération de documents Word
- `PyYAML` - Lecture de la configuration
- `Click` - Interface en ligne de commande
- `tabulate` - Affichage de tableaux
- `openpyxl` - Export Excel

### 4. Configurer vos informations

Ouvrez le fichier `config.yaml` et remplacez les valeurs par vos informations :

```yaml
freelance:
  nom: "Votre Prénom NOM"
  siret: "123 456 789 00012"
  adresse: "123 Rue de Exemple"
  code_postal: "75001"
  ville: "Paris"
  email: "votre@email.com"
  telephone: "+33 6 12 34 56 78"
  statut: "Micro-entrepreneur"
  tva_applicable: false  # false pour micro-entreprise

  # Coordonnées bancaires (pour les factures)
  banque: "Nom de votre banque"
  iban: "FR76 1234 5678 9012 3456 7890 123"
  bic: "BNPAFRPP"
```

---

## Lancer l'Interface Web

### 1. Démarrer le serveur

```bash
python web/app.py
```

Vous devriez voir :
```
==================================================
  Freelance Manager - Interface Web
==================================================

  Ouvrir: http://localhost:5000

 * Running on http://0.0.0.0:5000
```

### 2. Ouvrir dans le navigateur

Allez sur : **http://localhost:5000**

### 3. Arrêter le serveur

Appuyez sur `Ctrl + C` dans le terminal.

---

## Utilisation de l'Interface Web

### Dashboard
- Vue d'ensemble de votre activité
- CA annuel avec graphique mensuel
- Alerte si vous approchez du seuil micro-entreprise (77 700 €)
- Factures impayées et en retard

### Clients
1. Cliquez sur **Clients** dans le menu
2. Cliquez sur **Nouveau client**
3. Remplissez le formulaire
4. Cliquez sur **Créer le client**

### Créer un Devis
1. Cliquez sur **Devis** > **Nouveau devis**
2. Sélectionnez le client
3. Entrez la description, le TJM et le nombre de jours
4. Cliquez sur **Créer le devis**
5. Le PDF est généré automatiquement dans le dossier `output/`

### Créer une Facture
**Depuis un devis :**
1. Allez sur le devis
2. Cliquez sur **Convertir en facture**
3. Entrez les jours effectivement travaillés
4. Le PDF est généré automatiquement

**Sans devis :**
1. Cliquez sur **Factures** > **Nouvelle facture**
2. Remplissez le formulaire
3. Cliquez sur **Créer la facture**

### Générer un Contrat
1. Cliquez sur **Contrats** > **Nouveau contrat**
2. Sélectionnez le client et le type :
   - **Régie** : Facturation au temps passé
   - **Forfait** : Prix fixe avec livrables
   - **Mission** : Contrat court (1-5 jours)
3. Le document Word est généré dans `output/`

### Configuration
1. Cliquez sur **Config** dans le menu
2. Modifiez vos informations
3. Cliquez sur **Enregistrer**

---

## Utilisation en Ligne de Commande (CLI)

### Commandes principales

```bash
# Aide générale
python cli.py --help

# Ajouter un client
python cli.py client add "Nom Client" --siret "123456789" --email "client@email.com"

# Créer un devis
python cli.py devis create 1 --tjm 300 --jours 5 --description "Mission dev"

# Créer une facture depuis un devis
python cli.py facture create --devis 1 --jours-effectifs 5

# Générer un contrat
python cli.py contrat generate 1 --type regie --tjm 300

# Voir les statistiques
python cli.py stats

# Exporter en Excel
python cli.py export excel --annee 2024
```

---

## Structure des fichiers générés

```
output/
├── DEVIS-2024-001.pdf       # Devis numérotés
├── DEVIS-2024-002.pdf
├── FACT-2024-001.pdf        # Factures numérotées
├── FACT-2024-002.pdf
├── CONT-2024-001_regie.docx # Contrats Word
├── comptabilite_2024.xlsx   # Export Excel
└── clients_20241224.csv     # Export CSV
```

---

## Conformité légale française

Les documents générés incluent automatiquement :

✅ **Numérotation chronologique** (obligatoire) : DEVIS-2024-001, FACT-2024-001

✅ **Mentions TVA** : "TVA non applicable, art. 293 B du CGI" (micro-entreprise)

✅ **Pénalités de retard** (obligatoire sur factures) : Taux légal + 40€ frais de recouvrement

✅ **Escompte** (obligatoire) : "Pas d'escompte pour paiement anticipé"

✅ **Coordonnées bancaires** sur les factures

✅ **Conditions de paiement** : 30 jours fin de mois par défaut

---

## Réinitialisation (Mode Test)

Si vous avez fait des tests et souhaitez remettre les compteurs à zéro :

```bash
# Réinitialiser uniquement les compteurs (garde les données)
python cli.py reset --compteurs

# OU supprimer TOUTES les données (clients, devis, factures, contrats)
python cli.py reset --all
```

⚠️ **ATTENTION** : En production, ne jamais réinitialiser les compteurs !
Les numéros de devis/factures doivent rester séquentiels pour la conformité fiscale.

---

## Dépannage

### "ModuleNotFoundError: No module named 'flask'"

Installez les dépendances :
```bash
pip install -r requirements.txt
```

### "python: command not found"

Essayez avec `python3` :
```bash
python3 web/app.py
```

### Le serveur ne démarre pas

Vérifiez qu'aucune autre application n'utilise le port 5000 :
```bash
# Windows
netstat -ano | findstr :5000

# Mac/Linux
lsof -i :5000
```

### Les PDF ne se génèrent pas

Vérifiez que le dossier `output/` existe :
```bash
mkdir output
```

---

## Support

En cas de problème, vérifiez :
1. Python 3.10+ est installé
2. Les dépendances sont installées (`pip install -r requirements.txt`)
3. Le fichier `config.yaml` est correctement configuré
4. Vous êtes dans le bon dossier (`freelance-manager/`)
