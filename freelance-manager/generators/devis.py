"""
Générateur de devis PDF pour freelance.
Conforme à la réglementation française.
"""

from pathlib import Path
from datetime import date, timedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable
)
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER

from database import Devis, Client


class DevisGenerator:
    """Génère des devis PDF professionnels."""

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
            spaceAfter=20,
            alignment=TA_CENTER
        ))

        self.styles.add(ParagraphStyle(
            name='Subtitle',
            parent=self.styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#7F8C8D'),
            alignment=TA_CENTER,
            spaceAfter=30
        ))

        self.styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#2C3E50'),
            spaceBefore=15,
            spaceAfter=10,
            borderPadding=5
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
            fontSize=8,
            textColor=colors.HexColor('#555555'),
            leading=10,
            spaceBefore=5
        ))

    def generate(self, devis: Devis, client: Client) -> str:
        """
        Génère le PDF du devis.

        Returns:
            Chemin du fichier PDF généré.
        """
        filename = f"{devis.numero}.pdf"
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
        elements.extend(self._build_header(devis))

        # Infos client et devis
        elements.extend(self._build_client_info(devis, client))

        # Tableau des prestations
        elements.extend(self._build_prestations_table(devis))

        # Totaux
        elements.extend(self._build_totals(devis))

        # Conditions
        elements.extend(self._build_conditions(devis))

        # Mentions légales
        elements.extend(self._build_mentions())

        # Signature
        elements.extend(self._build_signature())

        doc.build(elements)
        return str(filepath)

    def _build_header(self, devis: Devis) -> list:
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
        date_creation = devis.date_creation or date.today()
        date_validite = date_creation + timedelta(days=devis.validite_jours)

        devis_info = f"""
        <b>DEVIS N° {devis.numero}</b><br/>
        <br/>
        Date : {date_creation.strftime('%d/%m/%Y')}<br/>
        Validité : {devis.validite_jours} jours<br/>
        Expire le : {date_validite.strftime('%d/%m/%Y')}
        """

        # Tableau d'en-tête
        header_data = [[
            Paragraph(freelance_info.strip(), self.styles['Info']),
            Paragraph(devis_info.strip(), self.styles['InfoRight'])
        ]]

        header_table = Table(header_data, colWidths=[9*cm, 8*cm])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ]))

        elements.append(header_table)
        elements.append(Spacer(1, 1*cm))

        # Titre
        elements.append(Paragraph("DEVIS", self.styles['TitleDoc']))

        return elements

    def _build_client_info(self, devis: Devis, client: Client) -> list:
        """Construit la section informations client."""
        elements = []

        elements.append(Paragraph("CLIENT", self.styles['SectionTitle']))

        client_info = f"""
        <b>{client.nom}</b><br/>
        {f'SIRET : {client.siret}' if client.siret else ''}<br/>
        {client.adresse or ''}<br/>
        {client.code_postal or ''} {client.ville or ''}<br/>
        {f'Contact : {client.contact_nom}' if client.contact_nom else ''}<br/>
        {client.email or ''}
        """

        elements.append(Paragraph(client_info.strip(), self.styles['Info']))
        elements.append(Spacer(1, 0.5*cm))

        return elements

    def _build_prestations_table(self, devis: Devis) -> list:
        """Construit le tableau des prestations."""
        elements = []

        elements.append(Paragraph("PRESTATIONS", self.styles['SectionTitle']))

        # En-têtes du tableau
        headers = ['Description', 'TJM (€)', 'Jours', 'Total HT (€)']

        # Données
        total_ht = devis.tjm * devis.jours
        data = [
            headers,
            [
                Paragraph(devis.description or "Prestation de service", self.styles['Info']),
                f"{devis.tjm:,.2f}".replace(',', ' '),
                f"{devis.jours:,.1f}".replace(',', ' '),
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
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),

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
        elements.append(Spacer(1, 0.5*cm))

        return elements

    def _build_totals(self, devis: Devis) -> list:
        """Construit la section des totaux."""
        elements = []

        total_ht = devis.tjm * devis.jours

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
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E8F4FD')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#2C3E50')),
        ]))

        # Wrapper pour aligner à droite
        wrapper_data = [['', totals_table]]
        wrapper = Table(wrapper_data, colWidths=[9*cm, 8*cm])
        elements.append(wrapper)

        if not self.freelance.get('tva_applicable', False):
            elements.append(Spacer(1, 0.3*cm))
            elements.append(Paragraph(
                f"* {self.mentions.get('tva_non_applicable', 'TVA non applicable, art. 293 B du CGI')}",
                self.styles['SmallText']
            ))

        elements.append(Spacer(1, 0.5*cm))

        return elements

    def _build_conditions(self, devis: Devis) -> list:
        """Construit la section conditions."""
        elements = []

        elements.append(HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor('#DEE2E6'),
            spaceBefore=10,
            spaceAfter=10
        ))

        elements.append(Paragraph("CONDITIONS", self.styles['SectionTitle']))

        conditions_text = f"""
        <b>Validité du devis :</b> Ce devis est valable {devis.validite_jours} jours à compter de sa date d'émission.<br/><br/>
        <b>Conditions de paiement :</b> {self.mentions.get('conditions_paiement', 'Paiement par virement bancaire à 30 jours fin de mois')}<br/><br/>
        <b>Acompte :</b> Un acompte de 30% pourra être demandé à la commande.<br/><br/>
        <b>Acceptation :</b> Pour accepter ce devis, merci de le retourner signé avec la mention "Bon pour accord" et la date.
        """

        elements.append(Paragraph(conditions_text.strip(), self.styles['Info']))
        elements.append(Spacer(1, 0.5*cm))

        return elements

    def _build_mentions(self) -> list:
        """Construit les mentions légales."""
        elements = []

        elements.append(HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor('#DEE2E6'),
            spaceBefore=10,
            spaceAfter=10
        ))

        elements.append(Paragraph("MENTIONS LÉGALES", self.styles['SectionTitle']))

        assurance_default = "Non soumis à obligation d'assurance professionnelle"
        mentions_text = f"""
        Dispensé d'immatriculation au registre du commerce et des sociétés (RCS) et au répertoire des métiers (RM).<br/>
        {self.mentions.get('assurance_rcp', assurance_default)}<br/>
        {self.mentions.get('garantie_financiere', '')}
        """

        elements.append(Paragraph(mentions_text.strip(), self.styles['Mention']))

        return elements

    def _build_signature(self) -> list:
        """Construit la zone de signature."""
        elements = []

        elements.append(Spacer(1, 1*cm))

        sig_data = [
            [
                Paragraph("<b>Le prestataire</b>", self.styles['Info']),
                Paragraph("<b>Le client</b><br/>(Signature précédée de la mention<br/>\"Bon pour accord\" et date)", self.styles['Info'])
            ],
            ['', ''],
            ['', ''],
            ['', '']
        ]

        sig_table = Table(sig_data, colWidths=[8.5*cm, 8.5*cm], rowHeights=[None, 1*cm, 1*cm, 1*cm])
        sig_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOX', (0, 0), (0, -1), 0.5, colors.HexColor('#DEE2E6')),
            ('BOX', (1, 0), (1, -1), 0.5, colors.HexColor('#DEE2E6')),
        ]))

        elements.append(sig_table)

        # Coordonnées bancaires
        elements.append(Spacer(1, 0.5*cm))
        bank_info = f"""
        <b>Coordonnées bancaires :</b><br/>
        Banque : {self.freelance.get('banque', 'N/A')}<br/>
        IBAN : {self.freelance.get('iban', 'N/A')}<br/>
        BIC : {self.freelance.get('bic', 'N/A')}
        """
        elements.append(Paragraph(bank_info.strip(), self.styles['SmallText']))

        return elements
