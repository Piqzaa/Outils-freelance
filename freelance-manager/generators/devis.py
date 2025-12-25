"""
Générateur de devis PDF pour freelance.
Conforme à la réglementation française.
Optimisé pour tenir sur une seule page A4.
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
    """Génère des devis PDF professionnels sur une page."""

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
        """Configure les styles personnalisés (compacts)."""
        self.styles.add(ParagraphStyle(
            name='TitleDoc',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=6,
            spaceBefore=0,
            alignment=TA_CENTER
        ))

        self.styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=self.styles['Heading2'],
            fontSize=10,
            textColor=colors.HexColor('#2C3E50'),
            spaceBefore=8,
            spaceAfter=4,
        ))

        self.styles.add(ParagraphStyle(
            name='Info',
            parent=self.styles['Normal'],
            fontSize=9,
            leading=11
        ))

        self.styles.add(ParagraphStyle(
            name='InfoSmall',
            parent=self.styles['Normal'],
            fontSize=8,
            leading=10
        ))

        self.styles.add(ParagraphStyle(
            name='InfoRight',
            parent=self.styles['Normal'],
            fontSize=9,
            leading=11,
            alignment=TA_RIGHT
        ))

        self.styles.add(ParagraphStyle(
            name='SmallText',
            parent=self.styles['Normal'],
            fontSize=7,
            textColor=colors.HexColor('#666666'),
            leading=9
        ))

        self.styles.add(ParagraphStyle(
            name='Mention',
            parent=self.styles['Normal'],
            fontSize=7,
            textColor=colors.HexColor('#555555'),
            leading=9,
        ))

    def generate(self, devis: Devis, client: Client) -> str:
        """Génère le PDF du devis sur une page."""
        filename = f"{devis.numero}.pdf"
        filepath = self.output_dir / filename

        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=A4,
            rightMargin=1.5*cm,
            leftMargin=1.5*cm,
            topMargin=1.2*cm,
            bottomMargin=1.2*cm
        )

        elements = []

        # En-tête avec infos freelance + client côte à côte
        elements.extend(self._build_header(devis, client))

        # Tableau des prestations
        elements.extend(self._build_prestations_table(devis))

        # Totaux
        elements.extend(self._build_totals(devis))

        # Conditions + Mentions légales (combinés)
        elements.extend(self._build_conditions_and_mentions(devis))

        # Signature compacte
        elements.extend(self._build_signature())

        doc.build(elements)
        return str(filepath)

    def _build_header(self, devis: Devis, client: Client) -> list:
        """Construit l'en-tête compact avec freelance, client et infos devis."""
        elements = []

        # Titre centré
        elements.append(Paragraph(f"DEVIS N° {devis.numero}", self.styles['TitleDoc']))

        date_creation = devis.date_creation or date.today()
        date_validite = date_creation + timedelta(days=devis.validite_jours)

        # Sous-titre avec dates
        date_info = f"Date : {date_creation.strftime('%d/%m/%Y')} | Validité : {devis.validite_jours} jours (jusqu'au {date_validite.strftime('%d/%m/%Y')})"
        elements.append(Paragraph(date_info, ParagraphStyle(
            'DateInfo', parent=self.styles['Normal'],
            fontSize=8, alignment=TA_CENTER, textColor=colors.HexColor('#666666')
        )))

        elements.append(Spacer(1, 0.4*cm))

        # Infos freelance (gauche) et client (droite)
        freelance_info = f"""
        <b>{self.freelance.get('nom', 'Nom Prénom')}</b><br/>
        {self.freelance.get('statut', 'Micro-entrepreneur')}<br/>
        SIRET : {self.freelance.get('siret', 'N/A')}<br/>
        {self.freelance.get('adresse', '')}<br/>
        {self.freelance.get('code_postal', '')} {self.freelance.get('ville', '')}<br/>
        {self.freelance.get('email', '')} | {self.freelance.get('telephone', '')}
        """

        client_info = f"""
        <b>CLIENT : {client.nom}</b><br/>
        {f'SIRET : {client.siret}' if client.siret else ''}<br/>
        {client.adresse or ''}<br/>
        {client.code_postal or ''} {client.ville or ''}<br/>
        {f'Contact : {client.contact_nom}' if client.contact_nom else ''}<br/>
        {client.email or ''}
        """

        header_data = [[
            Paragraph(freelance_info.strip(), self.styles['InfoSmall']),
            Paragraph(client_info.strip(), self.styles['InfoSmall'])
        ]]

        header_table = Table(header_data, colWidths=[9*cm, 9*cm])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#F8F9FA')),
            ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#E8F4FD')),
            ('BOX', (0, 0), (0, 0), 0.5, colors.HexColor('#DEE2E6')),
            ('BOX', (1, 0), (1, 0), 0.5, colors.HexColor('#DEE2E6')),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))

        elements.append(header_table)
        elements.append(Spacer(1, 0.4*cm))

        return elements

    def _build_prestations_table(self, devis: Devis) -> list:
        """Construit le tableau des prestations compact."""
        elements = []

        elements.append(Paragraph("PRESTATIONS", self.styles['SectionTitle']))

        type_tarif = getattr(devis, 'type_tarif', 'tjm') or 'tjm'

        if type_tarif == 'forfait':
            headers = ['Description', 'Montant HT (€)']
            data = [
                headers,
                [
                    Paragraph(devis.description or "Prestation de service", self.styles['Info']),
                    f"{devis.total_ht:,.2f}".replace(',', ' ')
                ]
            ]
            table = Table(data, colWidths=[14.5*cm, 3.5*cm])
        else:
            headers = ['Description', 'TJM (€)', 'Jours', 'Total HT (€)']
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
            table = Table(data, colWidths=[10*cm, 2.8*cm, 2.2*cm, 3*cm])

        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8F9FA')),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#DEE2E6')),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 0.3*cm))

        return elements

    def _build_totals(self, devis: Devis) -> list:
        """Construit la section des totaux compacte."""
        elements = []

        total_ht = devis.total_ht

        if self.freelance.get('tva_applicable', False):
            taux_tva = 20
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

        totals_table = Table(totals_data, colWidths=[3.5*cm, 3.5*cm])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E8F4FD')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#2C3E50')),
        ]))

        wrapper_data = [['', totals_table]]
        wrapper = Table(wrapper_data, colWidths=[11*cm, 7*cm])
        elements.append(wrapper)

        if not self.freelance.get('tva_applicable', False):
            elements.append(Paragraph(
                f"* {self.mentions.get('tva_non_applicable', 'TVA non applicable, art. 293 B du CGI')}",
                self.styles['SmallText']
            ))

        elements.append(Spacer(1, 0.3*cm))

        return elements

    def _build_conditions_and_mentions(self, devis: Devis) -> list:
        """Construit conditions et mentions légales en un bloc compact."""
        elements = []

        elements.append(HRFlowable(
            width="100%", thickness=0.5,
            color=colors.HexColor('#DEE2E6'),
            spaceBefore=4, spaceAfter=4
        ))

        # Conditions
        conditions_text = f"""
        <b>Validité :</b> {devis.validite_jours} jours |
        <b>Paiement :</b> {self.mentions.get('conditions_paiement', 'Virement à 30 jours')} |
        <b>Acompte :</b> 30% à la commande<br/>
        <b>Acceptation :</b> Retourner signé avec mention "Bon pour accord" et date.
        """
        elements.append(Paragraph(conditions_text.strip(), self.styles['InfoSmall']))

        elements.append(Spacer(1, 0.2*cm))

        # Mentions légales
        assurance = self.mentions.get('assurance_rcp', 'Non soumis à obligation d\'assurance professionnelle')
        mentions_text = f"""
        <b>Mentions légales :</b> Dispensé d'immatriculation RCS/RM. {assurance}
        """
        elements.append(Paragraph(mentions_text.strip(), self.styles['Mention']))

        elements.append(Spacer(1, 0.3*cm))

        return elements

    def _build_signature(self) -> list:
        """Construit la zone de signature compacte."""
        elements = []

        sig_data = [
            [
                Paragraph("<b>Le prestataire</b>", self.styles['InfoSmall']),
                Paragraph("<b>Le client</b> (Signature + \"Bon pour accord\" + date)", self.styles['InfoSmall'])
            ],
            ['', ''],
        ]

        sig_table = Table(sig_data, colWidths=[9*cm, 9*cm], rowHeights=[None, 2*cm])
        sig_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOX', (0, 0), (0, -1), 0.5, colors.HexColor('#DEE2E6')),
            ('BOX', (1, 0), (1, -1), 0.5, colors.HexColor('#DEE2E6')),
        ]))

        elements.append(sig_table)

        # Coordonnées bancaires en ligne
        elements.append(Spacer(1, 0.2*cm))
        bank_info = f"""
        <b>Coordonnées bancaires :</b> {self.freelance.get('banque', 'N/A')} |
        IBAN : {self.freelance.get('iban', 'N/A')} |
        BIC : {self.freelance.get('bic', 'N/A')}
        """
        elements.append(Paragraph(bank_info.strip(), self.styles['SmallText']))

        return elements
