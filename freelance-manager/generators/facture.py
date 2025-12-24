"""
Générateur de factures PDF pour freelance.
Conforme à la réglementation française (mentions obligatoires).
"""

from pathlib import Path
from datetime import date
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable
)
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER

from database import Facture, Client, Devis


class FactureGenerator:
    """Génère des factures PDF conformes à la réglementation française."""

    def __init__(self, config: dict):
        self.config = config
        self.freelance = config.get('freelance', {})
        self.mentions = config.get('mentions_legales', {})
        self.defaults = config.get('defaults', {})
        self.output_dir = Path(config.get('paths', {}).get('output', 'output'))
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Styles
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Configure les styles personnalisés."""
        self.styles.add(ParagraphStyle(
            name='TitleDoc',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=10,
            alignment=TA_CENTER
        ))

        self.styles.add(ParagraphStyle(
            name='Subtitle',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#7F8C8D'),
            alignment=TA_CENTER,
            spaceAfter=20
        ))

        self.styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=self.styles['Heading2'],
            fontSize=11,
            textColor=colors.HexColor('#2C3E50'),
            spaceBefore=12,
            spaceAfter=8,
        ))

        self.styles.add(ParagraphStyle(
            name='Info',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=14
        ))

        self.styles.add(ParagraphStyle(
            name='InfoRight',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=14,
            alignment=TA_RIGHT
        ))

        self.styles.add(ParagraphStyle(
            name='SmallText',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#7F8C8D'),
            leading=10
        ))

        self.styles.add(ParagraphStyle(
            name='Total',
            parent=self.styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#2C3E50'),
            fontName='Helvetica-Bold'
        ))

        self.styles.add(ParagraphStyle(
            name='Mention',
            parent=self.styles['Normal'],
            fontSize=7,
            textColor=colors.HexColor('#555555'),
            leading=9,
            spaceBefore=3
        ))

        self.styles.add(ParagraphStyle(
            name='Important',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#C0392B'),
            fontName='Helvetica-Bold'
        ))

    def generate(self, facture: Facture, client: Client,
                 devis: Devis = None) -> str:
        """
        Génère le PDF de la facture.

        Args:
            facture: Objet Facture
            client: Objet Client
            devis: Objet Devis (optionnel, si facture liée à un devis)

        Returns:
            Chemin du fichier PDF généré.
        """
        filename = f"{facture.numero}.pdf"
        filepath = self.output_dir / filename

        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )

        elements = []

        # En-tête avec infos freelance
        elements.extend(self._build_header(facture, devis))

        # Infos client
        elements.extend(self._build_client_info(client))

        # Période de mission
        elements.extend(self._build_mission_info(facture, devis))

        # Tableau des prestations
        elements.extend(self._build_prestations_table(facture))

        # Totaux
        elements.extend(self._build_totals(facture))

        # Conditions de paiement
        elements.extend(self._build_payment_info(facture))

        # Mentions légales obligatoires
        elements.extend(self._build_mentions_legales())

        # Coordonnées bancaires
        elements.extend(self._build_bank_info())

        doc.build(elements)
        return str(filepath)

    def _build_header(self, facture: Facture, devis: Devis = None) -> list:
        """Construit l'en-tête du document."""
        elements = []

        # Infos freelance (gauche)
        freelance_info = f"""
        <b>{self.freelance.get('nom', 'Nom Prénom')}</b><br/>
        {self.freelance.get('statut', 'Micro-entrepreneur')}<br/>
        SIRET : {self.freelance.get('siret', 'N/A')}<br/>
        {self.freelance.get('adresse', '')}<br/>
        {self.freelance.get('code_postal', '')} {self.freelance.get('ville', '')}<br/>
        <br/>
        {self.freelance.get('email', '')}<br/>
        {self.freelance.get('telephone', '')}
        """

        # Numéro et date (droite)
        date_creation = facture.date_creation or date.today()

        facture_info = f"""
        <b>FACTURE N° {facture.numero}</b><br/>
        <br/>
        Date : {date_creation.strftime('%d/%m/%Y')}<br/>
        """

        if devis:
            facture_info += f"Réf. devis : {devis.numero}<br/>"

        if facture.date_echeance:
            facture_info += f"Échéance : {facture.date_echeance.strftime('%d/%m/%Y')}"

        # Tableau d'en-tête
        header_data = [[
            Paragraph(freelance_info.strip(), self.styles['Info']),
            Paragraph(facture_info.strip(), self.styles['InfoRight'])
        ]]

        header_table = Table(header_data, colWidths=[9*cm, 8*cm])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ]))

        elements.append(header_table)
        elements.append(Spacer(1, 0.8*cm))

        # Titre
        elements.append(Paragraph("FACTURE", self.styles['TitleDoc']))

        # Statut si payée
        if facture.statut == 'payée':
            elements.append(Paragraph("ACQUITTÉE", self.styles['Subtitle']))

        return elements

    def _build_client_info(self, client: Client) -> list:
        """Construit la section informations client."""
        elements = []

        elements.append(Paragraph("FACTURÉ À", self.styles['SectionTitle']))

        contact_line = f"À l'attention de : {client.contact_nom}" if client.contact_nom else ""
        client_info = f"""
        <b>{client.nom}</b><br/>
        {f'SIRET : {client.siret}' if client.siret else ''}<br/>
        {client.adresse or ''}<br/>
        {client.code_postal or ''} {client.ville or ''}<br/>
        {contact_line}<br/>
        {client.email or ''}
        """

        elements.append(Paragraph(client_info.strip(), self.styles['Info']))
        elements.append(Spacer(1, 0.4*cm))

        return elements

    def _build_mission_info(self, facture: Facture, devis: Devis = None) -> list:
        """Construit la section informations de mission."""
        elements = []

        if facture.date_debut_mission or facture.date_fin_mission:
            elements.append(Paragraph("PÉRIODE DE MISSION", self.styles['SectionTitle']))

            periode_info = ""
            if facture.date_debut_mission and facture.date_fin_mission:
                periode_info = f"Du {facture.date_debut_mission.strftime('%d/%m/%Y')} au {facture.date_fin_mission.strftime('%d/%m/%Y')}"
            elif facture.date_debut_mission:
                periode_info = f"À partir du {facture.date_debut_mission.strftime('%d/%m/%Y')}"

            elements.append(Paragraph(periode_info, self.styles['Info']))
            elements.append(Spacer(1, 0.3*cm))

        return elements

    def _build_prestations_table(self, facture: Facture) -> list:
        """Construit le tableau des prestations."""
        elements = []

        elements.append(Paragraph("DÉTAIL DES PRESTATIONS", self.styles['SectionTitle']))

        # En-têtes du tableau
        headers = ['Description', 'TJM (€)', 'Jours', 'Total HT (€)']

        # Données
        total_ht = facture.tjm * facture.jours_effectifs
        data = [
            headers,
            [
                Paragraph(facture.description or "Prestation de service", self.styles['Info']),
                f"{facture.tjm:,.2f}".replace(',', ' '),
                f"{facture.jours_effectifs:,.1f}".replace(',', ' '),
                f"{total_ht:,.2f}".replace(',', ' ')
            ]
        ]

        # Style du tableau
        table = Table(data, colWidths=[9*cm, 3*cm, 2.5*cm, 3*cm])
        table.setStyle(TableStyle([
            # En-tête
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),

            # Corps
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8F9FA')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 10),

            # Bordures
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#DEE2E6')),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 0.4*cm))

        return elements

    def _build_totals(self, facture: Facture) -> list:
        """Construit la section des totaux."""
        elements = []

        total_ht = facture.tjm * facture.jours_effectifs

        # Tableau des totaux (aligné à droite)
        if self.freelance.get('tva_applicable', False):
            taux_tva = 20  # TVA standard
            tva = total_ht * taux_tva / 100
            total_ttc = total_ht + tva
            totals_data = [
                ['Total HT', f"{total_ht:,.2f} €".replace(',', ' ')],
                [f'TVA ({taux_tva}%)', f"{tva:,.2f} €".replace(',', ' ')],
                ['Total TTC', f"{total_ttc:,.2f} €".replace(',', ' ')],
            ]
        else:
            totals_data = [
                ['Total HT', f"{total_ht:,.2f} €".replace(',', ' ')],
                ['Total TTC*', f"{total_ht:,.2f} €".replace(',', ' ')],
            ]

        totals_table = Table(totals_data, colWidths=[4*cm, 4*cm])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E8F4FD')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#2C3E50')),
        ]))

        # Wrapper pour aligner à droite
        wrapper_data = [['', totals_table]]
        wrapper = Table(wrapper_data, colWidths=[9*cm, 8*cm])
        elements.append(wrapper)

        if not self.freelance.get('tva_applicable', False):
            elements.append(Spacer(1, 0.2*cm))
            elements.append(Paragraph(
                f"* {self.mentions.get('tva_non_applicable', 'TVA non applicable, art. 293 B du CGI')}",
                self.styles['SmallText']
            ))

        elements.append(Spacer(1, 0.4*cm))

        return elements

    def _build_payment_info(self, facture: Facture) -> list:
        """Construit la section conditions de paiement."""
        elements = []

        elements.append(HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor('#DEE2E6'),
            spaceBefore=8,
            spaceAfter=8
        ))

        elements.append(Paragraph("CONDITIONS DE RÈGLEMENT", self.styles['SectionTitle']))

        payment_text = f"""
        <b>Mode de paiement :</b> Virement bancaire<br/>
        <b>Délai de paiement :</b> {self.defaults.get('delai_paiement_jours', 30)} jours
        """

        if facture.date_echeance:
            payment_text += f"<br/><b>Date limite de paiement :</b> {facture.date_echeance.strftime('%d/%m/%Y')}"

        elements.append(Paragraph(payment_text.strip(), self.styles['Info']))
        elements.append(Spacer(1, 0.3*cm))

        return elements

    def _build_mentions_legales(self) -> list:
        """Construit les mentions légales obligatoires sur les factures."""
        elements = []

        elements.append(HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor('#DEE2E6'),
            spaceBefore=8,
            spaceAfter=8
        ))

        elements.append(Paragraph("MENTIONS LÉGALES OBLIGATOIRES", self.styles['SectionTitle']))

        # Pénalités de retard (OBLIGATOIRE)
        penalites = self.mentions.get('penalites_retard',
            "En cas de retard de paiement, une pénalité égale à 3 fois le taux d'intérêt légal "
            "sera exigible (décret 2012-1115). Une indemnité forfaitaire de 40€ pour frais de "
            "recouvrement sera également due (art. L.441-10 du Code de commerce)."
        )
        elements.append(Paragraph(f"<b>Pénalités de retard :</b> {penalites}", self.styles['Mention']))

        # Escompte (OBLIGATOIRE)
        escompte = self.mentions.get('escompte', "Pas d'escompte pour paiement anticipé.")
        elements.append(Paragraph(f"<b>Escompte :</b> {escompte}", self.styles['Mention']))

        # Mentions micro-entrepreneur
        elements.append(Paragraph(
            "Dispensé d'immatriculation au RCS et au RM.",
            self.styles['Mention']
        ))

        if self.mentions.get('assurance_rcp'):
            elements.append(Paragraph(
                f"<b>Assurance RC Pro :</b> {self.mentions.get('assurance_rcp')}",
                self.styles['Mention']
            ))

        return elements

    def _build_bank_info(self) -> list:
        """Construit la section coordonnées bancaires."""
        elements = []

        elements.append(Spacer(1, 0.4*cm))
        elements.append(HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor('#DEE2E6'),
            spaceBefore=8,
            spaceAfter=8
        ))

        elements.append(Paragraph("COORDONNÉES BANCAIRES", self.styles['SectionTitle']))

        bank_info = f"""
        <b>Titulaire :</b> {self.freelance.get('nom', 'N/A')}<br/>
        <b>Banque :</b> {self.freelance.get('banque', 'N/A')}<br/>
        <b>IBAN :</b> {self.freelance.get('iban', 'N/A')}<br/>
        <b>BIC :</b> {self.freelance.get('bic', 'N/A')}
        """

        elements.append(Paragraph(bank_info.strip(), self.styles['Info']))

        # Message de remerciement
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph(
            "Merci pour votre confiance.",
            self.styles['Info']
        ))

        return elements
