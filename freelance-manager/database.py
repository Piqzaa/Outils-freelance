"""
Gestion de la base de données SQLite pour Freelance Manager.
Stocke les clients, devis, factures et contrats.
"""

import sqlite3
from pathlib import Path
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import yaml


@dataclass
class Client:
    id: Optional[int]
    nom: str
    siret: str
    adresse: str
    code_postal: str
    ville: str
    email: str
    telephone: str
    contact_nom: str
    created_at: Optional[datetime] = None

    @classmethod
    def from_row(cls, row: tuple) -> 'Client':
        return cls(
            id=row[0],
            nom=row[1],
            siret=row[2],
            adresse=row[3],
            code_postal=row[4],
            ville=row[5],
            email=row[6],
            telephone=row[7],
            contact_nom=row[8],
            created_at=datetime.fromisoformat(row[9]) if row[9] else None
        )


@dataclass
class Devis:
    id: Optional[int]
    numero: str
    client_id: int
    description: str
    tjm: float
    jours: float
    total_ht: float
    total_ttc: float
    statut: str  # brouillon, envoyé, accepté, refusé, expiré
    validite_jours: int
    date_creation: Optional[date] = None
    date_envoi: Optional[date] = None
    notes: str = ""
    type_tarif: str = "tjm"  # 'tjm' (TJM × jours) ou 'forfait' (prix fixe)
    acompte: bool = True  # Demander un acompte de 30% (False pour missions régie)

    @classmethod
    def from_row(cls, row: tuple) -> 'Devis':
        return cls(
            id=row[0],
            numero=row[1],
            client_id=row[2],
            description=row[3],
            tjm=row[4],
            jours=row[5],
            total_ht=row[6],
            total_ttc=row[7],
            statut=row[8],
            validite_jours=row[9],
            date_creation=date.fromisoformat(row[10]) if row[10] else None,
            date_envoi=date.fromisoformat(row[11]) if row[11] else None,
            notes=row[12] if len(row) > 12 else "",
            type_tarif=row[13] if len(row) > 13 and row[13] else "tjm",
            acompte=bool(row[14]) if len(row) > 14 and row[14] is not None else True
        )


@dataclass
class Facture:
    id: Optional[int]
    numero: str
    devis_id: Optional[int]
    client_id: int
    description: str
    tjm: float
    jours_effectifs: float
    total_ht: float
    total_ttc: float
    statut: str  # brouillon, envoyée, payée, impayée, annulée
    date_creation: Optional[date] = None
    date_envoi: Optional[date] = None
    date_echeance: Optional[date] = None
    date_paiement: Optional[date] = None
    date_debut_mission: Optional[date] = None
    date_fin_mission: Optional[date] = None
    notes: str = ""
    type_tarif: str = "tjm"  # 'tjm' (TJM × jours) ou 'forfait' (prix fixe)

    @classmethod
    def from_row(cls, row: tuple) -> 'Facture':
        return cls(
            id=row[0],
            numero=row[1],
            devis_id=row[2],
            client_id=row[3],
            description=row[4],
            tjm=row[5],
            jours_effectifs=row[6],
            total_ht=row[7],
            total_ttc=row[8],
            statut=row[9],
            date_creation=date.fromisoformat(row[10]) if row[10] else None,
            date_envoi=date.fromisoformat(row[11]) if row[11] else None,
            date_echeance=date.fromisoformat(row[12]) if row[12] else None,
            date_paiement=date.fromisoformat(row[13]) if row[13] else None,
            date_debut_mission=date.fromisoformat(row[14]) if row[14] else None,
            date_fin_mission=date.fromisoformat(row[15]) if row[15] else None,
            notes=row[16] if len(row) > 16 else "",
            type_tarif=row[17] if len(row) > 17 and row[17] else "tjm"
        )


@dataclass
class Contrat:
    id: Optional[int]
    numero: str
    client_id: int
    type_contrat: str  # regie, forfait, mission
    tjm: float
    duree_jours: Optional[int]
    montant_forfait: Optional[float]
    date_debut: Optional[date]
    date_fin: Optional[date]
    statut: str  # brouillon, envoyé, signé, terminé, annulé
    date_creation: Optional[date] = None
    fichier_path: str = ""

    @classmethod
    def from_row(cls, row: tuple) -> 'Contrat':
        return cls(
            id=row[0],
            numero=row[1],
            client_id=row[2],
            type_contrat=row[3],
            tjm=row[4],
            duree_jours=row[5],
            montant_forfait=row[6],
            date_debut=date.fromisoformat(row[7]) if row[7] else None,
            date_fin=date.fromisoformat(row[8]) if row[8] else None,
            statut=row[9],
            date_creation=date.fromisoformat(row[10]) if row[10] else None,
            fichier_path=row[11] if len(row) > 11 else ""
        )


class Database:
    """Gestionnaire de base de données SQLite."""

    def __init__(self, db_path: str = "freelance.db"):
        self.db_path = Path(db_path)
        self.conn = None
        self._connect()
        self._create_tables()

    def _connect(self):
        """Connexion à la base de données."""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row

    def _create_tables(self):
        """Création des tables si elles n'existent pas."""
        cursor = self.conn.cursor()

        # Table clients
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                siret TEXT,
                adresse TEXT,
                code_postal TEXT,
                ville TEXT,
                email TEXT,
                telephone TEXT,
                contact_nom TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Table devis
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS devis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero TEXT UNIQUE NOT NULL,
                client_id INTEGER NOT NULL,
                description TEXT,
                tjm REAL NOT NULL,
                jours REAL NOT NULL,
                total_ht REAL NOT NULL,
                total_ttc REAL NOT NULL,
                statut TEXT DEFAULT 'brouillon',
                validite_jours INTEGER DEFAULT 30,
                date_creation DATE DEFAULT CURRENT_DATE,
                date_envoi DATE,
                notes TEXT,
                type_tarif TEXT DEFAULT 'tjm',
                acompte INTEGER DEFAULT 1,
                FOREIGN KEY (client_id) REFERENCES clients(id)
            )
        ''')

        # Migration: ajouter colonnes si elles n'existent pas
        try:
            cursor.execute("ALTER TABLE devis ADD COLUMN type_tarif TEXT DEFAULT 'tjm'")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE devis ADD COLUMN acompte INTEGER DEFAULT 1")
        except sqlite3.OperationalError:
            pass

        # Table factures
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS factures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero TEXT UNIQUE NOT NULL,
                devis_id INTEGER,
                client_id INTEGER NOT NULL,
                description TEXT,
                tjm REAL NOT NULL,
                jours_effectifs REAL NOT NULL,
                total_ht REAL NOT NULL,
                total_ttc REAL NOT NULL,
                statut TEXT DEFAULT 'brouillon',
                date_creation DATE DEFAULT CURRENT_DATE,
                date_envoi DATE,
                date_echeance DATE,
                date_paiement DATE,
                date_debut_mission DATE,
                date_fin_mission DATE,
                notes TEXT,
                type_tarif TEXT DEFAULT 'tjm',
                FOREIGN KEY (devis_id) REFERENCES devis(id),
                FOREIGN KEY (client_id) REFERENCES clients(id)
            )
        ''')

        # Migration: ajouter colonne type_tarif si elle n'existe pas
        try:
            cursor.execute("ALTER TABLE factures ADD COLUMN type_tarif TEXT DEFAULT 'tjm'")
        except sqlite3.OperationalError:
            pass  # La colonne existe déjà

        # Table contrats
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contrats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero TEXT UNIQUE NOT NULL,
                client_id INTEGER NOT NULL,
                type_contrat TEXT NOT NULL,
                tjm REAL,
                duree_jours INTEGER,
                montant_forfait REAL,
                date_debut DATE,
                date_fin DATE,
                statut TEXT DEFAULT 'brouillon',
                date_creation DATE DEFAULT CURRENT_DATE,
                fichier_path TEXT,
                FOREIGN KEY (client_id) REFERENCES clients(id)
            )
        ''')

        # Table compteurs pour numérotation
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compteurs (
                type TEXT PRIMARY KEY,
                annee INTEGER NOT NULL,
                compteur INTEGER NOT NULL
            )
        ''')

        self.conn.commit()

    def close(self):
        """Fermeture de la connexion."""
        if self.conn:
            self.conn.close()

    # ==================== GESTION DES COMPTEURS ====================

    def get_next_number(self, doc_type: str) -> str:
        """
        Génère le prochain numéro de document (DEVIS-2024-001, FACT-2024-001, etc.)
        Réinitialise le compteur chaque année.
        """
        cursor = self.conn.cursor()
        current_year = datetime.now().year

        cursor.execute(
            "SELECT annee, compteur FROM compteurs WHERE type = ?",
            (doc_type,)
        )
        row = cursor.fetchone()

        if row is None:
            # Premier document de ce type
            compteur = 1
            cursor.execute(
                "INSERT INTO compteurs (type, annee, compteur) VALUES (?, ?, ?)",
                (doc_type, current_year, compteur)
            )
        elif row['annee'] != current_year:
            # Nouvelle année, réinitialisation
            compteur = 1
            cursor.execute(
                "UPDATE compteurs SET annee = ?, compteur = ? WHERE type = ?",
                (current_year, compteur, doc_type)
            )
        else:
            # Même année, incrémentation
            compteur = row['compteur'] + 1
            cursor.execute(
                "UPDATE compteurs SET compteur = ? WHERE type = ?",
                (compteur, doc_type)
            )

        self.conn.commit()

        prefixes = {
            'devis': 'DEVIS',
            'facture': 'FACT',
            'contrat': 'CONT'
        }
        prefix = prefixes.get(doc_type, doc_type.upper())
        return f"{prefix}-{current_year}-{compteur:03d}"

    # ==================== GESTION DES CLIENTS ====================

    def add_client(self, nom: str, siret: str = "", adresse: str = "",
                   code_postal: str = "", ville: str = "", email: str = "",
                   telephone: str = "", contact_nom: str = "") -> int:
        """Ajoute un nouveau client."""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO clients (nom, siret, adresse, code_postal, ville, email, telephone, contact_nom)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (nom, siret, adresse, code_postal, ville, email, telephone, contact_nom))
        self.conn.commit()
        return cursor.lastrowid

    def get_client(self, client_id: int) -> Optional[Client]:
        """Récupère un client par son ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
        row = cursor.fetchone()
        if row:
            return Client.from_row(tuple(row))
        return None

    def list_clients(self) -> List[Client]:
        """Liste tous les clients."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM clients ORDER BY nom")
        return [Client.from_row(tuple(row)) for row in cursor.fetchall()]

    def update_client(self, client_id: int, **kwargs) -> bool:
        """Met à jour un client."""
        if not kwargs:
            return False

        valid_fields = ['nom', 'siret', 'adresse', 'code_postal', 'ville',
                        'email', 'telephone', 'contact_nom']
        updates = {k: v for k, v in kwargs.items() if k in valid_fields}

        if not updates:
            return False

        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [client_id]

        cursor = self.conn.cursor()
        cursor.execute(f"UPDATE clients SET {set_clause} WHERE id = ?", values)
        self.conn.commit()
        return cursor.rowcount > 0

    def delete_client(self, client_id: int) -> bool:
        """Supprime un client."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM clients WHERE id = ?", (client_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    # ==================== GESTION DES DEVIS ====================

    def add_devis(self, client_id: int, description: str, tjm: float = 0,
                  jours: float = 0, validite_jours: int = 30, notes: str = "",
                  type_tarif: str = "tjm", montant_forfait: float = 0,
                  acompte: bool = True) -> Devis:
        """
        Crée un nouveau devis.

        Args:
            type_tarif: 'tjm' pour TJM × jours, 'forfait' pour prix fixe
            montant_forfait: Montant forfaitaire si type_tarif == 'forfait'
            acompte: True pour demander 30% d'acompte, False sinon (ex: mission régie)
        """
        numero = self.get_next_number('devis')

        if type_tarif == 'forfait':
            total_ht = montant_forfait
            # Pour forfait, tjm et jours sont à 0
            tjm = 0
            jours = 0
        else:
            total_ht = tjm * jours

        total_ttc = total_ht  # Micro-entreprise sans TVA

        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO devis (numero, client_id, description, tjm, jours,
                              total_ht, total_ttc, validite_jours, notes, type_tarif, acompte)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (numero, client_id, description, tjm, jours, total_ht, total_ttc,
              validite_jours, notes, type_tarif, 1 if acompte else 0))
        self.conn.commit()

        return self.get_devis(cursor.lastrowid)

    def get_devis(self, devis_id: int) -> Optional[Devis]:
        """Récupère un devis par son ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM devis WHERE id = ?", (devis_id,))
        row = cursor.fetchone()
        if row:
            return Devis.from_row(tuple(row))
        return None

    def get_devis_by_numero(self, numero: str) -> Optional[Devis]:
        """Récupère un devis par son numéro."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM devis WHERE numero = ?", (numero,))
        row = cursor.fetchone()
        if row:
            return Devis.from_row(tuple(row))
        return None

    def list_devis(self, client_id: Optional[int] = None,
                   statut: Optional[str] = None) -> List[Devis]:
        """Liste les devis avec filtres optionnels."""
        cursor = self.conn.cursor()
        query = "SELECT * FROM devis WHERE 1=1"
        params = []

        if client_id:
            query += " AND client_id = ?"
            params.append(client_id)
        if statut:
            query += " AND statut = ?"
            params.append(statut)

        query += " ORDER BY date_creation DESC"
        cursor.execute(query, params)
        return [Devis.from_row(tuple(row)) for row in cursor.fetchall()]

    def update_devis_statut(self, devis_id: int, statut: str) -> bool:
        """Met à jour le statut d'un devis."""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE devis SET statut = ? WHERE id = ?",
            (statut, devis_id)
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def delete_devis(self, devis_id: int) -> bool:
        """Supprime un devis par son ID."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM devis WHERE id = ?", (devis_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    # ==================== GESTION DES FACTURES ====================

    def add_facture(self, client_id: int, description: str, tjm: float = 0,
                    jours_effectifs: float = 0, devis_id: Optional[int] = None,
                    date_debut_mission: Optional[date] = None,
                    date_fin_mission: Optional[date] = None,
                    delai_paiement: int = 30, notes: str = "",
                    type_tarif: str = "tjm", montant_forfait: float = 0) -> Facture:
        """
        Crée une nouvelle facture.

        Args:
            type_tarif: 'tjm' pour TJM × jours, 'forfait' pour prix fixe
            montant_forfait: Montant forfaitaire si type_tarif == 'forfait'
        """
        numero = self.get_next_number('facture')

        if type_tarif == 'forfait':
            total_ht = montant_forfait
            # Pour forfait, tjm et jours sont à 0
            tjm = 0
            jours_effectifs = 0
        else:
            total_ht = tjm * jours_effectifs

        total_ttc = total_ht  # Micro-entreprise sans TVA

        # Calcul date d'échéance (30 jours fin de mois par défaut)
        today = date.today()
        if today.month == 12:
            date_echeance = date(today.year + 1, 1, 1)
        else:
            date_echeance = date(today.year, today.month + 1, 1)
        from datetime import timedelta
        date_echeance = date_echeance + timedelta(days=delai_paiement - 1)

        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO factures (numero, devis_id, client_id, description, tjm,
                                 jours_effectifs, total_ht, total_ttc,
                                 date_echeance, date_debut_mission, date_fin_mission, notes, type_tarif)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (numero, devis_id, client_id, description, tjm, jours_effectifs,
              total_ht, total_ttc, date_echeance.isoformat(),
              date_debut_mission.isoformat() if date_debut_mission else None,
              date_fin_mission.isoformat() if date_fin_mission else None, notes, type_tarif))
        self.conn.commit()

        return self.get_facture(cursor.lastrowid)

    def add_facture_from_devis(self, devis_id: int, jours_effectifs: float = 0,
                               date_debut_mission: Optional[date] = None,
                               date_fin_mission: Optional[date] = None,
                               montant_forfait: float = 0) -> Facture:
        """Crée une facture à partir d'un devis."""
        devis = self.get_devis(devis_id)
        if not devis:
            raise ValueError(f"Devis {devis_id} introuvable")

        # Utiliser le même type de tarif que le devis
        type_tarif = devis.type_tarif
        if type_tarif == 'forfait':
            montant = montant_forfait if montant_forfait else devis.total_ht
        else:
            montant = 0

        return self.add_facture(
            client_id=devis.client_id,
            description=devis.description,
            tjm=devis.tjm,
            jours_effectifs=jours_effectifs,
            devis_id=devis_id,
            date_debut_mission=date_debut_mission,
            date_fin_mission=date_fin_mission,
            type_tarif=type_tarif,
            montant_forfait=montant
        )

    def get_facture(self, facture_id: int) -> Optional[Facture]:
        """Récupère une facture par son ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM factures WHERE id = ?", (facture_id,))
        row = cursor.fetchone()
        if row:
            return Facture.from_row(tuple(row))
        return None

    def get_facture_by_numero(self, numero: str) -> Optional[Facture]:
        """Récupère une facture par son numéro."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM factures WHERE numero = ?", (numero,))
        row = cursor.fetchone()
        if row:
            return Facture.from_row(tuple(row))
        return None

    def list_factures(self, client_id: Optional[int] = None,
                      statut: Optional[str] = None,
                      annee: Optional[int] = None) -> List[Facture]:
        """Liste les factures avec filtres optionnels."""
        cursor = self.conn.cursor()
        query = "SELECT * FROM factures WHERE 1=1"
        params = []

        if client_id:
            query += " AND client_id = ?"
            params.append(client_id)
        if statut:
            query += " AND statut = ?"
            params.append(statut)
        if annee:
            query += " AND strftime('%Y', date_creation) = ?"
            params.append(str(annee))

        query += " ORDER BY date_creation DESC"
        cursor.execute(query, params)
        return [Facture.from_row(tuple(row)) for row in cursor.fetchall()]

    def update_facture_statut(self, facture_id: int, statut: str,
                              date_paiement: Optional[date] = None) -> bool:
        """Met à jour le statut d'une facture."""
        cursor = self.conn.cursor()
        if statut == 'payée' and date_paiement:
            cursor.execute(
                "UPDATE factures SET statut = ?, date_paiement = ? WHERE id = ?",
                (statut, date_paiement.isoformat(), facture_id)
            )
        else:
            cursor.execute(
                "UPDATE factures SET statut = ? WHERE id = ?",
                (statut, facture_id)
            )
        self.conn.commit()
        return cursor.rowcount > 0

    def delete_facture(self, facture_id: int) -> bool:
        """Supprime une facture par son ID."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM factures WHERE id = ?", (facture_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    # ==================== GESTION DES CONTRATS ====================

    def add_contrat(self, client_id: int, type_contrat: str, tjm: float = 0,
                    duree_jours: Optional[int] = None,
                    montant_forfait: Optional[float] = None,
                    date_debut: Optional[date] = None,
                    date_fin: Optional[date] = None,
                    fichier_path: str = "") -> Contrat:
        """Crée un nouveau contrat."""
        numero = self.get_next_number('contrat')

        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO contrats (numero, client_id, type_contrat, tjm, duree_jours,
                                 montant_forfait, date_debut, date_fin, fichier_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (numero, client_id, type_contrat, tjm, duree_jours, montant_forfait,
              date_debut.isoformat() if date_debut else None,
              date_fin.isoformat() if date_fin else None, fichier_path))
        self.conn.commit()

        return self.get_contrat(cursor.lastrowid)

    def get_contrat(self, contrat_id: int) -> Optional[Contrat]:
        """Récupère un contrat par son ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM contrats WHERE id = ?", (contrat_id,))
        row = cursor.fetchone()
        if row:
            return Contrat.from_row(tuple(row))
        return None

    def list_contrats(self, client_id: Optional[int] = None,
                      type_contrat: Optional[str] = None) -> List[Contrat]:
        """Liste les contrats avec filtres optionnels."""
        cursor = self.conn.cursor()
        query = "SELECT * FROM contrats WHERE 1=1"
        params = []

        if client_id:
            query += " AND client_id = ?"
            params.append(client_id)
        if type_contrat:
            query += " AND type_contrat = ?"
            params.append(type_contrat)

        query += " ORDER BY date_creation DESC"
        cursor.execute(query, params)
        return [Contrat.from_row(tuple(row)) for row in cursor.fetchall()]

    def delete_contrat(self, contrat_id: int) -> bool:
        """Supprime un contrat par son ID."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM contrats WHERE id = ?", (contrat_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    # ==================== STATISTIQUES ====================

    def get_ca_annuel(self, annee: Optional[int] = None) -> float:
        """Calcule le CA annuel (factures payées)."""
        if annee is None:
            annee = datetime.now().year

        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT COALESCE(SUM(total_ht), 0)
            FROM factures
            WHERE strftime('%Y', date_creation) = ?
            AND statut = 'payée'
        ''', (str(annee),))

        result = cursor.fetchone()
        return float(result[0]) if result else 0.0

    def get_ca_mensuel(self, annee: Optional[int] = None) -> Dict[int, float]:
        """Retourne le CA par mois."""
        if annee is None:
            annee = datetime.now().year

        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT strftime('%m', date_creation) as mois, SUM(total_ht)
            FROM factures
            WHERE strftime('%Y', date_creation) = ?
            AND statut = 'payée'
            GROUP BY mois
            ORDER BY mois
        ''', (str(annee),))

        result = {}
        for row in cursor.fetchall():
            result[int(row[0])] = float(row[1])
        return result

    def get_factures_impayees(self) -> List[Facture]:
        """Retourne les factures impayées."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM factures
            WHERE statut IN ('envoyée', 'impayée')
            ORDER BY date_echeance
        ''')
        return [Facture.from_row(tuple(row)) for row in cursor.fetchall()]

    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques globales."""
        annee = datetime.now().year
        cursor = self.conn.cursor()

        # CA annuel
        ca_annuel = self.get_ca_annuel(annee)

        # Nombre de clients actifs (au moins une facture cette année)
        cursor.execute('''
            SELECT COUNT(DISTINCT client_id)
            FROM factures
            WHERE strftime('%Y', date_creation) = ?
        ''', (str(annee),))
        clients_actifs = cursor.fetchone()[0]

        # Factures en attente
        cursor.execute('''
            SELECT COUNT(*), COALESCE(SUM(total_ht), 0)
            FROM factures
            WHERE statut IN ('envoyée', 'impayée')
        ''')
        row = cursor.fetchone()
        factures_impayees_count = row[0]
        factures_impayees_montant = float(row[1])

        # Devis en attente
        cursor.execute('''
            SELECT COUNT(*)
            FROM devis
            WHERE statut IN ('brouillon', 'envoyé')
        ''')
        devis_en_attente = cursor.fetchone()[0]

        # CA mensuel
        ca_mensuel = self.get_ca_mensuel(annee)

        return {
            'annee': annee,
            'ca_annuel': ca_annuel,
            'clients_actifs': clients_actifs,
            'factures_impayees_count': factures_impayees_count,
            'factures_impayees_montant': factures_impayees_montant,
            'devis_en_attente': devis_en_attente,
            'ca_mensuel': ca_mensuel
        }


def load_config(config_path: str = "config.yaml") -> dict:
    """Charge la configuration depuis le fichier YAML."""
    config_file = Path(config_path)
    if not config_file.exists():
        # Chercher dans le répertoire du script
        script_dir = Path(__file__).parent
        config_file = script_dir / "config.yaml"

    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    return {}


def get_db(config: Optional[dict] = None) -> Database:
    """Retourne une instance de la base de données."""
    if config is None:
        config = load_config()

    db_path = config.get('paths', {}).get('database', 'freelance.db')
    return Database(db_path)
