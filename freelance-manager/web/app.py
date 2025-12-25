#!/usr/bin/env python3
"""
Freelance Manager - Interface Web
Application Flask pour gérer devis, factures et contrats.
"""

import os
import sys
from pathlib import Path
from datetime import date, datetime, timedelta
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, jsonify, send_file, send_from_directory
)

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import Database, load_config, Client, Devis, Facture, Contrat
from generators.devis import DevisGenerator
from generators.facture import FactureGenerator
from generators.contrat import ContratGenerator

# Configuration
BASE_DIR = Path(__file__).parent.parent
CONFIG_PATH = BASE_DIR / "config.yaml"
DB_PATH = BASE_DIR / "freelance.db"
OUTPUT_DIR = BASE_DIR / "output"

app = Flask(__name__,
            template_folder='templates',
            static_folder='static')
app.secret_key = 'freelance-manager-secret-key-change-in-production'


def get_db():
    """Retourne une instance de la base de données."""
    return Database(str(DB_PATH))


def get_config():
    """Charge la configuration avec chemins absolus."""
    config = load_config(str(CONFIG_PATH))
    # Forcer le chemin absolu pour output
    if 'paths' not in config:
        config['paths'] = {}
    config['paths']['output'] = str(OUTPUT_DIR)
    # Créer le dossier si nécessaire
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return config


# ==================== ROUTES PRINCIPALES ====================

@app.route('/')
def dashboard():
    """Page d'accueil - Dashboard."""
    db = get_db()
    config = get_config()
    stats = db.get_stats()
    factures_impayees = db.get_factures_impayees()[:5]

    # Enrichir avec noms clients
    for f in factures_impayees:
        client = db.get_client(f.client_id)
        f.client_nom = client.nom if client else "Client inconnu"
        if f.date_echeance and f.date_echeance < date.today():
            f.en_retard = True
            f.jours_retard = (date.today() - f.date_echeance).days
        else:
            f.en_retard = False

    # Derniers devis
    derniers_devis = db.list_devis()[:5]
    for d in derniers_devis:
        client = db.get_client(d.client_id)
        d.client_nom = client.nom if client else "Client inconnu"

    seuil_ca = config.get('seuils', {}).get('ca_services', 77700)
    pct_seuil = (stats['ca_annuel'] / seuil_ca) * 100 if seuil_ca else 0

    db.close()

    return render_template('dashboard.html',
                          stats=stats,
                          factures_impayees=factures_impayees,
                          derniers_devis=derniers_devis,
                          seuil_ca=seuil_ca,
                          pct_seuil=pct_seuil,
                          config=config)


# ==================== ROUTES CLIENTS ====================

@app.route('/clients')
def clients_list():
    """Liste des clients."""
    db = get_db()
    clients = db.list_clients()
    db.close()
    return render_template('clients/list.html', clients=clients)


@app.route('/clients/new', methods=['GET', 'POST'])
def client_new():
    """Créer un nouveau client."""
    if request.method == 'POST':
        db = get_db()
        client_id = db.add_client(
            nom=request.form['nom'],
            siret=request.form.get('siret', ''),
            adresse=request.form.get('adresse', ''),
            code_postal=request.form.get('code_postal', ''),
            ville=request.form.get('ville', ''),
            email=request.form.get('email', ''),
            telephone=request.form.get('telephone', ''),
            contact_nom=request.form.get('contact_nom', '')
        )
        db.close()
        flash(f'Client créé avec succès (ID: {client_id})', 'success')
        return redirect(url_for('clients_list'))

    return render_template('clients/form.html', client=None)


@app.route('/clients/<int:client_id>')
def client_view(client_id):
    """Voir un client."""
    db = get_db()
    client = db.get_client(client_id)
    if not client:
        flash('Client introuvable', 'error')
        db.close()
        return redirect(url_for('clients_list'))

    # Récupérer devis et factures du client
    devis = db.list_devis(client_id=client_id)
    factures = db.list_factures(client_id=client_id)
    contrats = db.list_contrats(client_id=client_id)
    db.close()

    return render_template('clients/view.html',
                          client=client,
                          devis=devis,
                          factures=factures,
                          contrats=contrats)


@app.route('/clients/<int:client_id>/edit', methods=['GET', 'POST'])
def client_edit(client_id):
    """Modifier un client."""
    db = get_db()
    client = db.get_client(client_id)

    if not client:
        flash('Client introuvable', 'error')
        db.close()
        return redirect(url_for('clients_list'))

    if request.method == 'POST':
        db.update_client(
            client_id,
            nom=request.form['nom'],
            siret=request.form.get('siret', ''),
            adresse=request.form.get('adresse', ''),
            code_postal=request.form.get('code_postal', ''),
            ville=request.form.get('ville', ''),
            email=request.form.get('email', ''),
            telephone=request.form.get('telephone', ''),
            contact_nom=request.form.get('contact_nom', '')
        )
        db.close()
        flash('Client mis à jour', 'success')
        return redirect(url_for('client_view', client_id=client_id))

    db.close()
    return render_template('clients/form.html', client=client)


@app.route('/clients/<int:client_id>/delete', methods=['POST'])
def client_delete(client_id):
    """Supprimer un client."""
    db = get_db()
    db.delete_client(client_id)
    db.close()
    flash('Client supprimé', 'success')
    return redirect(url_for('clients_list'))


# ==================== ROUTES DEVIS ====================

@app.route('/devis')
def devis_list():
    """Liste des devis."""
    db = get_db()
    devis = db.list_devis()

    # Enrichir avec noms clients
    for d in devis:
        client = db.get_client(d.client_id)
        d.client_nom = client.nom if client else "Client inconnu"

    db.close()
    return render_template('devis/list.html', devis=devis)


@app.route('/devis/new', methods=['GET', 'POST'])
def devis_new():
    """Créer un nouveau devis."""
    db = get_db()
    config = get_config()

    if request.method == 'POST':
        client_id = int(request.form['client_id'])
        description = request.form.get('description', 'Prestation de service')
        validite = int(request.form.get('validite', 30))
        type_tarif = request.form.get('type_tarif', 'tjm')

        if type_tarif == 'forfait':
            montant_forfait = float(request.form.get('montant_forfait', 0))
            tjm = 0
            jours = 0
        else:
            tjm = float(request.form.get('tjm', 0))
            jours = float(request.form.get('jours', 0))
            montant_forfait = 0

        # Créer le devis
        devis = db.add_devis(
            client_id=client_id,
            description=description,
            tjm=tjm,
            jours=jours,
            validite_jours=validite,
            type_tarif=type_tarif,
            montant_forfait=montant_forfait
        )

        # Générer le PDF
        client = db.get_client(client_id)
        generator = DevisGenerator(config)
        pdf_path = generator.generate(devis, client)

        db.close()
        flash(f'Devis {devis.numero} créé avec succès', 'success')
        return redirect(url_for('devis_view', devis_id=devis.id))

    clients = db.list_clients()
    defaults = config.get('defaults', {})
    db.close()

    return render_template('devis/form.html',
                          devis=None,
                          clients=clients,
                          defaults=defaults)


@app.route('/devis/<int:devis_id>')
def devis_view(devis_id):
    """Voir un devis."""
    db = get_db()
    devis = db.get_devis(devis_id)

    if not devis:
        flash('Devis introuvable', 'error')
        db.close()
        return redirect(url_for('devis_list'))

    client = db.get_client(devis.client_id)
    db.close()

    # Vérifier si PDF existe
    pdf_path = OUTPUT_DIR / f"{devis.numero}.pdf"
    pdf_exists = pdf_path.exists()

    return render_template('devis/view.html',
                          devis=devis,
                          client=client,
                          pdf_exists=pdf_exists)


@app.route('/devis/<int:devis_id>/statut', methods=['POST'])
def devis_update_statut(devis_id):
    """Mettre à jour le statut d'un devis."""
    db = get_db()
    nouveau_statut = request.form['statut']
    db.update_devis_statut(devis_id, nouveau_statut)
    db.close()
    flash(f'Statut mis à jour: {nouveau_statut}', 'success')
    return redirect(url_for('devis_view', devis_id=devis_id))


@app.route('/devis/<int:devis_id>/pdf')
def devis_pdf(devis_id):
    """Télécharger/régénérer le PDF d'un devis."""
    db = get_db()
    config = get_config()

    devis = db.get_devis(devis_id)
    if not devis:
        flash('Devis introuvable', 'error')
        db.close()
        return redirect(url_for('devis_list'))

    client = db.get_client(devis.client_id)

    # Générer le PDF
    generator = DevisGenerator(config)
    pdf_path = generator.generate(devis, client)

    db.close()

    return send_file(pdf_path, as_attachment=True)


@app.route('/devis/<int:devis_id>/facturer', methods=['GET', 'POST'])
def devis_to_facture(devis_id):
    """Créer une facture à partir d'un devis."""
    db = get_db()
    config = get_config()

    devis = db.get_devis(devis_id)
    if not devis:
        flash('Devis introuvable', 'error')
        db.close()
        return redirect(url_for('devis_list'))

    client = db.get_client(devis.client_id)

    if request.method == 'POST':
        date_debut_str = request.form.get('date_debut', '')
        date_fin_str = request.form.get('date_fin', '')

        date_debut = datetime.strptime(date_debut_str, '%Y-%m-%d').date() if date_debut_str else None
        date_fin = datetime.strptime(date_fin_str, '%Y-%m-%d').date() if date_fin_str else None

        # Créer la facture selon le type de tarif
        if devis.type_tarif == 'forfait':
            montant_forfait = float(request.form.get('montant_forfait', devis.total_ht))
            facture = db.add_facture(
                client_id=devis.client_id,
                description=devis.description,
                tjm=0,
                jours_effectifs=0,
                devis_id=devis_id,
                date_debut_mission=date_debut,
                date_fin_mission=date_fin,
                type_tarif='forfait',
                montant_forfait=montant_forfait
            )
        else:
            jours_effectifs = float(request.form.get('jours_effectifs', 0))
            facture = db.add_facture(
                client_id=devis.client_id,
                description=devis.description,
                tjm=devis.tjm,
                jours_effectifs=jours_effectifs,
                devis_id=devis_id,
                date_debut_mission=date_debut,
                date_fin_mission=date_fin,
                type_tarif='tjm'
            )

        # Mettre à jour le statut du devis
        db.update_devis_statut(devis_id, 'accepté')

        # Générer le PDF
        generator = FactureGenerator(config)
        pdf_path = generator.generate(facture, client, devis)

        db.close()
        flash(f'Facture {facture.numero} créée avec succès', 'success')
        return redirect(url_for('facture_view', facture_id=facture.id))

    db.close()
    return render_template('devis/to_facture.html', devis=devis, client=client)


# ==================== ROUTES FACTURES ====================

@app.route('/factures')
def factures_list():
    """Liste des factures."""
    db = get_db()

    # Filtres
    statut = request.args.get('statut')
    annee = request.args.get('annee', type=int)

    factures = db.list_factures(statut=statut, annee=annee)

    # Enrichir avec noms clients
    for f in factures:
        client = db.get_client(f.client_id)
        f.client_nom = client.nom if client else "Client inconnu"
        if f.date_echeance and f.date_echeance < date.today() and f.statut not in ['payée', 'annulée']:
            f.en_retard = True
        else:
            f.en_retard = False

    db.close()
    return render_template('factures/list.html', factures=factures,
                          filtre_statut=statut, filtre_annee=annee)


@app.route('/factures/new', methods=['GET', 'POST'])
def facture_new():
    """Créer une nouvelle facture."""
    db = get_db()
    config = get_config()

    if request.method == 'POST':
        client_id = int(request.form['client_id'])
        description = request.form.get('description', 'Prestation de service')
        type_tarif = request.form.get('type_tarif', 'tjm')

        date_debut_str = request.form.get('date_debut', '')
        date_fin_str = request.form.get('date_fin', '')
        date_debut = datetime.strptime(date_debut_str, '%Y-%m-%d').date() if date_debut_str else None
        date_fin = datetime.strptime(date_fin_str, '%Y-%m-%d').date() if date_fin_str else None

        if type_tarif == 'forfait':
            montant_forfait = float(request.form.get('montant_forfait', 0))
            tjm = 0
            jours = 0
        else:
            tjm = float(request.form.get('tjm', 0))
            jours = float(request.form.get('jours_effectifs', 0))
            montant_forfait = 0

        # Créer la facture
        facture = db.add_facture(
            client_id=client_id,
            description=description,
            tjm=tjm,
            jours_effectifs=jours,
            date_debut_mission=date_debut,
            date_fin_mission=date_fin,
            type_tarif=type_tarif,
            montant_forfait=montant_forfait
        )

        # Générer le PDF
        client = db.get_client(client_id)
        generator = FactureGenerator(config)
        pdf_path = generator.generate(facture, client)

        db.close()
        flash(f'Facture {facture.numero} créée avec succès', 'success')
        return redirect(url_for('facture_view', facture_id=facture.id))

    clients = db.list_clients()
    defaults = config.get('defaults', {})
    db.close()

    return render_template('factures/form.html',
                          facture=None,
                          clients=clients,
                          defaults=defaults)


@app.route('/factures/<int:facture_id>')
def facture_view(facture_id):
    """Voir une facture."""
    db = get_db()
    facture = db.get_facture(facture_id)

    if not facture:
        flash('Facture introuvable', 'error')
        db.close()
        return redirect(url_for('factures_list'))

    client = db.get_client(facture.client_id)
    devis = db.get_devis(facture.devis_id) if facture.devis_id else None
    db.close()

    # Vérifier si PDF existe
    pdf_path = OUTPUT_DIR / f"{facture.numero}.pdf"
    pdf_exists = pdf_path.exists()

    return render_template('factures/view.html',
                          facture=facture,
                          client=client,
                          devis=devis,
                          pdf_exists=pdf_exists)


@app.route('/factures/<int:facture_id>/statut', methods=['POST'])
def facture_update_statut(facture_id):
    """Mettre à jour le statut d'une facture."""
    db = get_db()
    nouveau_statut = request.form['statut']

    date_paiement = None
    if nouveau_statut == 'payée':
        date_paiement_str = request.form.get('date_paiement', '')
        if date_paiement_str:
            date_paiement = datetime.strptime(date_paiement_str, '%Y-%m-%d').date()
        else:
            date_paiement = date.today()

    db.update_facture_statut(facture_id, nouveau_statut, date_paiement)
    db.close()
    flash(f'Statut mis à jour: {nouveau_statut}', 'success')
    return redirect(url_for('facture_view', facture_id=facture_id))


@app.route('/factures/<int:facture_id>/pdf')
def facture_pdf(facture_id):
    """Télécharger le PDF d'une facture."""
    db = get_db()
    config = get_config()

    facture = db.get_facture(facture_id)
    if not facture:
        flash('Facture introuvable', 'error')
        db.close()
        return redirect(url_for('factures_list'))

    client = db.get_client(facture.client_id)
    devis = db.get_devis(facture.devis_id) if facture.devis_id else None

    # Générer le PDF
    generator = FactureGenerator(config)
    pdf_path = generator.generate(facture, client, devis)

    db.close()

    return send_file(pdf_path, as_attachment=True)


# ==================== ROUTES CONTRATS ====================

@app.route('/contrats')
def contrats_list():
    """Liste des contrats."""
    db = get_db()
    contrats = db.list_contrats()

    # Enrichir avec noms clients
    for c in contrats:
        client = db.get_client(c.client_id)
        c.client_nom = client.nom if client else "Client inconnu"

    db.close()
    return render_template('contrats/list.html', contrats=contrats)


@app.route('/contrats/new', methods=['GET', 'POST'])
def contrat_new():
    """Créer un nouveau contrat."""
    db = get_db()
    config = get_config()

    if request.method == 'POST':
        client_id = int(request.form['client_id'])
        type_contrat = request.form['type_contrat']
        tjm = float(request.form['tjm'])

        duree_jours = request.form.get('duree_jours')
        duree_jours = int(duree_jours) if duree_jours else None

        duree_mois = int(request.form.get('duree_mois', 3))

        montant_forfait = request.form.get('montant_forfait')
        montant_forfait = float(montant_forfait) if montant_forfait else None

        date_debut_str = request.form.get('date_debut', '')
        date_fin_str = request.form.get('date_fin', '')
        date_debut = datetime.strptime(date_debut_str, '%Y-%m-%d').date() if date_debut_str else None
        date_fin = datetime.strptime(date_fin_str, '%Y-%m-%d').date() if date_fin_str else None

        objet = request.form.get('objet', '')
        description = request.form.get('description', '')
        lieu = request.form.get('lieu', '')

        # Créer le contrat en base
        contrat = db.add_contrat(
            client_id=client_id,
            type_contrat=type_contrat,
            tjm=tjm,
            duree_jours=duree_jours,
            montant_forfait=montant_forfait,
            date_debut=date_debut,
            date_fin=date_fin
        )

        # Générer le document Word
        client = db.get_client(client_id)
        generator = ContratGenerator(config)
        doc_path = generator.generate(
            contrat, client,
            description=description,
            duree_mois=duree_mois,
            lieu_mission=lieu,
            objet=objet
        )

        db.close()
        flash(f'Contrat {contrat.numero} créé avec succès', 'success')
        return redirect(url_for('contrat_view', contrat_id=contrat.id))

    clients = db.list_clients()
    defaults = config.get('defaults', {})
    db.close()

    return render_template('contrats/form.html',
                          contrat=None,
                          clients=clients,
                          defaults=defaults)


@app.route('/contrats/<int:contrat_id>')
def contrat_view(contrat_id):
    """Voir un contrat."""
    db = get_db()
    contrat = db.get_contrat(contrat_id)

    if not contrat:
        flash('Contrat introuvable', 'error')
        db.close()
        return redirect(url_for('contrats_list'))

    client = db.get_client(contrat.client_id)
    db.close()

    # Vérifier si document existe
    type_suffix = {'regie': '_regie', 'forfait': '_forfait', 'mission': '_mission'}
    doc_path = OUTPUT_DIR / f"{contrat.numero}{type_suffix.get(contrat.type_contrat, '')}.docx"
    doc_exists = doc_path.exists()

    return render_template('contrats/view.html',
                          contrat=contrat,
                          client=client,
                          doc_exists=doc_exists)


@app.route('/contrats/<int:contrat_id>/download')
def contrat_download(contrat_id):
    """Télécharger un contrat."""
    db = get_db()
    contrat = db.get_contrat(contrat_id)

    if not contrat:
        flash('Contrat introuvable', 'error')
        db.close()
        return redirect(url_for('contrats_list'))

    db.close()

    type_suffix = {'regie': '_regie', 'forfait': '_forfait', 'mission': '_mission'}
    filename = f"{contrat.numero}{type_suffix.get(contrat.type_contrat, '')}.docx"
    doc_path = OUTPUT_DIR / filename

    if doc_path.exists():
        return send_file(str(doc_path), as_attachment=True)
    else:
        flash('Document introuvable, veuillez le régénérer', 'error')
        return redirect(url_for('contrat_view', contrat_id=contrat_id))


# ==================== ROUTES CONFIGURATION ====================

@app.route('/config', methods=['GET', 'POST'])
def config_view():
    """Voir et modifier la configuration."""
    import yaml

    if request.method == 'POST':
        # Sauvegarder la config
        new_config = {
            'freelance': {
                'nom': request.form.get('nom', ''),
                'siret': request.form.get('siret', ''),
                'adresse': request.form.get('adresse', ''),
                'code_postal': request.form.get('code_postal', ''),
                'ville': request.form.get('ville', ''),
                'email': request.form.get('email', ''),
                'telephone': request.form.get('telephone', ''),
                'statut': request.form.get('statut', 'Micro-entrepreneur'),
                'tva_applicable': request.form.get('tva_applicable') == 'on',
                'banque': request.form.get('banque', ''),
                'iban': request.form.get('iban', ''),
                'bic': request.form.get('bic', ''),
            },
            'defaults': {
                'tjm': int(request.form.get('tjm_default', 300)),
                'validite_devis_jours': int(request.form.get('validite_devis', 30)),
                'delai_paiement_jours': int(request.form.get('delai_paiement', 30)),
            },
            'seuils': {
                'ca_services': int(request.form.get('seuil_ca', 77700)),
                'alerte_pourcentage': int(request.form.get('alerte_pct', 80)),
            },
            'mentions_legales': {
                'tva_non_applicable': 'TVA non applicable, art. 293 B du CGI',
                'penalites_retard': request.form.get('penalites_retard', ''),
                'escompte': request.form.get('escompte', "Pas d'escompte pour paiement anticipé."),
                'conditions_paiement': request.form.get('conditions_paiement', ''),
            },
            'paths': {
                'output': 'output',
                'database': 'freelance.db',
            }
        }

        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            yaml.dump(new_config, f, default_flow_style=False, allow_unicode=True)

        flash('Configuration sauvegardée', 'success')
        return redirect(url_for('config_view'))

    config = get_config()
    return render_template('config.html', config=config)


# ==================== API JSON ====================

@app.route('/api/stats')
def api_stats():
    """API JSON pour les statistiques."""
    db = get_db()
    stats = db.get_stats()
    db.close()
    return jsonify(stats)


@app.route('/api/ca_mensuel/<int:annee>')
def api_ca_mensuel(annee):
    """API JSON pour le CA mensuel."""
    db = get_db()
    ca = db.get_ca_mensuel(annee)
    db.close()
    return jsonify(ca)


# ==================== MAIN ====================

if __name__ == '__main__':
    # Créer le dossier output si nécessaire
    OUTPUT_DIR.mkdir(exist_ok=True)

    print("=" * 50)
    print("  Freelance Manager - Interface Web")
    print("=" * 50)
    print(f"\n  Ouvrir: http://localhost:5000\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
