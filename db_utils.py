"""
Utilitaires pour la gestion de la base de données SQLite
Gestion des paiements, utilisateurs et répartition des revenus
"""

import sqlite3
import logging
import os
from typing import Optional, Dict, List, Tuple, Any
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Gestionnaire pour les opérations de base de données"""
    
    def __init__(self, db_path: str = None):
        """
        Initialise le gestionnaire de base de données
        
        Args:
            db_path: Chemin vers la base de données SQLite (ignoré si DATABASE_URL est définie)
        """
        # Vérifier si on utilise PostgreSQL ou SQLite
        database_url = os.getenv('DATABASE_URL')
        
        if database_url:
            # Production : PostgreSQL via DATABASE_URL
            logger.info("🚀 Utilisation PostgreSQL pour production")
            self.use_postgresql = True
            self.db_url = database_url
            if self.db_url.startswith('postgres://'):
                self.db_url = self.db_url.replace('postgres://', 'postgresql://', 1)
        else:
            # Local : SQLite
            logger.info("🏠 Utilisation SQLite pour développement local")
            self.use_postgresql = False
            if db_path is None:
                self.db_path = Path(__file__).parent / "covoiturage.db"
            else:
                self.db_path = Path(db_path)
        
        self.commission_rate = float(os.getenv('COMMISSION_RATE', '0.12'))
        if hasattr(self, 'db_path'):
            logger.info(f"Base de données SQLite : {self.db_path}")
        else:
            logger.info("Base de données PostgreSQL configurée")
        logger.info(f"Taux de commission : {self.commission_rate * 100}%")
    
    @contextmanager
    def get_connection(self):
        """
        Context manager pour gérer les connexions à la base de données
        """
        if self.use_postgresql:
            # PostgreSQL via SQLAlchemy
            try:
                from database.db_manager import get_db
                db = get_db()
                yield db
            finally:
                if 'db' in locals():
                    db.close()
        else:
            # SQLite
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            try:
                yield conn
            finally:
                conn.close()
    
    def initialize_database(self) -> bool:
        """
        Initialise la base de données avec les tables nécessaires pour les paiements
        Compatible SQLite et PostgreSQL
        """
        try:
            if self.use_postgresql:
                # PostgreSQL : Les tables sont gérées par SQLAlchemy
                logger.info("✅ Base de données PostgreSQL gérée par SQLAlchemy")
                return True
            else:
                # SQLite : Création manuelle des tables
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Table pour stocker les détails des paiements
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS payments (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            booking_id INTEGER NOT NULL,
                            trip_id INTEGER NOT NULL,
                            passenger_id INTEGER NOT NULL,
                            driver_id INTEGER NOT NULL,
                            amount REAL NOT NULL,
                            commission_amount REAL NOT NULL,
                            driver_amount REAL NOT NULL,
                            payment_method TEXT NOT NULL DEFAULT 'paypal',
                            paypal_payment_id TEXT,
                            paypal_payout_id TEXT,
                            payment_status TEXT NOT NULL DEFAULT 'pending',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            completed_at TIMESTAMP,
                            FOREIGN KEY (booking_id) REFERENCES bookings (id),
                            FOREIGN KEY (trip_id) REFERENCES trips (id),
                            FOREIGN KEY (passenger_id) REFERENCES users (id),
                            FOREIGN KEY (driver_id) REFERENCES users (id)
                        )
                    ''')
                    
                    conn.commit()
                    logger.info("✅ Base de données SQLite initialisée avec succès")
                    return True
                
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de la base de données : {e}")
            return False
    
    def save_payment(self, booking_id: int, trip_id: int, passenger_id: int, 
                    driver_id: int, amount: float, paypal_payment_id: str = None) -> Optional[int]:
        """
        Enregistre un nouveau paiement avec calcul automatique de la répartition
        
        Args:
            booking_id: ID de la réservation
            trip_id: ID du trajet
            passenger_id: ID du passager
            driver_id: ID du conducteur
            amount: Montant total du paiement
            paypal_payment_id: ID du paiement PayPal
            
        Returns:
            ID du paiement créé ou None si erreur
        """
        try:
            # Calcul de la répartition
            commission_amount = round(amount * self.commission_rate, 2)
            driver_amount = round(amount * (1 - self.commission_rate), 2)
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO payments (
                        booking_id, trip_id, passenger_id, driver_id,
                        amount, commission_amount, driver_amount,
                        paypal_payment_id, payment_status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    booking_id, trip_id, passenger_id, driver_id,
                    amount, commission_amount, driver_amount,
                    paypal_payment_id, 'pending'
                ))
                
                payment_id = cursor.lastrowid
                
                # Enregistrement de la transaction initiale
                cursor.execute('''
                    INSERT INTO payment_transactions (
                        payment_id, transaction_type, amount, status, external_id
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (payment_id, 'payment_created', amount, 'pending', paypal_payment_id))
                
                conn.commit()
                
                logger.info(f"Paiement créé : ID {payment_id}, montant {amount} CHF "
                          f"(conducteur: {driver_amount} CHF, commission: {commission_amount} CHF)")
                
                return payment_id
                
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement du paiement : {e}")
            return None
    
    def update_payment_status(self, payment_id: int = None, paypal_payment_id: str = None,
                            new_status: str = None, paypal_payout_id: str = None) -> bool:
        """
        Met à jour le statut d'un paiement
        
        Args:
            payment_id: ID du paiement (optionnel si paypal_payment_id fourni)
            paypal_payment_id: ID PayPal du paiement (optionnel si payment_id fourni)
            new_status: Nouveau statut ('pending', 'paid', 'completed', 'failed', 'cancelled')
            paypal_payout_id: ID du paiement envoyé au conducteur
            
        Returns:
            True si la mise à jour réussit
        """
        if not payment_id and not paypal_payment_id:
            logger.error("payment_id ou paypal_payment_id requis")
            return False
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Construction de la requête de mise à jour
                update_fields = ["updated_at = CURRENT_TIMESTAMP"]
                params = []
                
                if new_status:
                    update_fields.append("payment_status = ?")
                    params.append(new_status)
                    
                    if new_status == 'completed':
                        update_fields.append("completed_at = CURRENT_TIMESTAMP")
                
                if paypal_payout_id:
                    update_fields.append("paypal_payout_id = ?")
                    params.append(paypal_payout_id)
                
                # Condition WHERE
                if payment_id:
                    where_clause = "id = ?"
                    params.append(payment_id)
                else:
                    where_clause = "paypal_payment_id = ?"
                    params.append(paypal_payment_id)
                
                query = f"UPDATE payments SET {', '.join(update_fields)} WHERE {where_clause}"
                
                cursor.execute(query, params)
                
                if cursor.rowcount > 0:
                    # Enregistrement de la transaction de mise à jour
                    if payment_id is None:
                        cursor.execute("SELECT id FROM payments WHERE paypal_payment_id = ?", (paypal_payment_id,))
                        result = cursor.fetchone()
                        payment_id = result['id'] if result else None
                    
                    if payment_id and new_status:
                        cursor.execute('''
                            INSERT INTO payment_transactions (
                                payment_id, transaction_type, status, external_id
                            ) VALUES (?, ?, ?, ?)
                        ''', (payment_id, 'status_update', new_status, paypal_payout_id))
                    
                    conn.commit()
                    logger.info(f"Statut du paiement {payment_id} mis à jour : {new_status}")
                    return True
                else:
                    logger.warning(f"Aucun paiement trouvé pour la mise à jour")
                    return False
                    
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du statut : {e}")
            return False
    
    def calculate_revenue_split(self, amount: float) -> Dict[str, float]:
        """
        Calcule la répartition 88%/12% entre conducteur et plateforme
        
        Args:
            amount: Montant total
            
        Returns:
            Dictionnaire avec les montants calculés
        """
        commission_amount = round(amount * self.commission_rate, 2)
        driver_amount = round(amount * (1 - self.commission_rate), 2)
        
        return {
            'total_amount': amount,
            'driver_amount': driver_amount,
            'commission_amount': commission_amount,
            'driver_percentage': (1 - self.commission_rate) * 100,
            'commission_percentage': self.commission_rate * 100
        }
    
    def save_user_paypal_email(self, user_id: int, paypal_email: str) -> bool:
        """
        Enregistre ou met à jour l'email PayPal d'un utilisateur
        
        Args:
            user_id: ID de l'utilisateur
            paypal_email: Adresse email PayPal
            
        Returns:
            True si l'enregistrement réussit
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Vérifier si l'utilisateur existe déjà
                cursor.execute("SELECT id FROM user_payment_info WHERE user_id = ?", (user_id,))
                existing = cursor.fetchone()
                
                if existing:
                    # Mise à jour
                    cursor.execute('''
                        UPDATE user_payment_info 
                        SET paypal_email = ?, updated_at = CURRENT_TIMESTAMP 
                        WHERE user_id = ?
                    ''', (paypal_email, user_id))
                    logger.info(f"Email PayPal mis à jour pour l'utilisateur {user_id}")
                else:
                    # Insertion
                    cursor.execute('''
                        INSERT INTO user_payment_info (user_id, paypal_email) 
                        VALUES (?, ?)
                    ''', (user_id, paypal_email))
                    logger.info(f"Email PayPal enregistré pour l'utilisateur {user_id}")
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement de l'email PayPal : {e}")
            return False
    
    def get_user_paypal_email(self, user_id: int) -> Optional[str]:
        """
        Récupère l'email PayPal d'un utilisateur
        
        Args:
            user_id: ID de l'utilisateur
            
        Returns:
            Email PayPal ou None si non trouvé
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT paypal_email FROM user_payment_info WHERE user_id = ?", (user_id,))
                result = cursor.fetchone()
                
                return result['paypal_email'] if result else None
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'email PayPal : {e}")
            return None
    
    def get_payment_details(self, payment_id: int = None, paypal_payment_id: str = None) -> Optional[Dict]:
        """
        Récupère les détails d'un paiement
        
        Args:
            payment_id: ID du paiement (optionnel si paypal_payment_id fourni)
            paypal_payment_id: ID PayPal du paiement
            
        Returns:
            Dictionnaire avec les détails du paiement
        """
        if not payment_id and not paypal_payment_id:
            return None
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if payment_id:
                    where_clause = "p.id = ?"
                    param = payment_id
                else:
                    where_clause = "p.paypal_payment_id = ?"
                    param = paypal_payment_id
                
                cursor.execute(f'''
                    SELECT 
                        p.*,
                        u_passenger.telegram_id as passenger_telegram_id,
                        u_driver.telegram_id as driver_telegram_id,
                        t.departure_city, t.arrival_city, t.departure_time,
                        b.seats
                    FROM payments p
                    JOIN users u_passenger ON p.passenger_id = u_passenger.id
                    JOIN users u_driver ON p.driver_id = u_driver.id
                    JOIN trips t ON p.trip_id = t.id
                    JOIN bookings b ON p.booking_id = b.id
                    WHERE {where_clause}
                ''', (param,))
                
                result = cursor.fetchone()
                
                if result:
                    return dict(result)
                return None
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des détails du paiement : {e}")
            return None
    
    def get_user_payment_history(self, user_id: int, role: str = 'all') -> List[Dict]:
        """
        Récupère l'historique des paiements d'un utilisateur
        
        Args:
            user_id: ID de l'utilisateur
            role: 'passenger', 'driver' ou 'all'
            
        Returns:
            Liste des paiements
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                conditions = []
                params = []
                
                if role == 'passenger':
                    conditions.append("p.passenger_id = ?")
                    params.append(user_id)
                elif role == 'driver':
                    conditions.append("p.driver_id = ?")
                    params.append(user_id)
                else:
                    conditions.append("(p.passenger_id = ? OR p.driver_id = ?)")
                    params.extend([user_id, user_id])
                
                where_clause = " AND ".join(conditions)
                
                cursor.execute(f'''
                    SELECT 
                        p.*,
                        t.departure_city, t.arrival_city, t.departure_time,
                        b.seats,
                        CASE 
                            WHEN p.passenger_id = ? THEN 'passenger'
                            WHEN p.driver_id = ? THEN 'driver'
                        END as user_role
                    FROM payments p
                    JOIN trips t ON p.trip_id = t.id
                    JOIN bookings b ON p.booking_id = b.id
                    WHERE {where_clause}
                    ORDER BY p.created_at DESC
                ''', params + [user_id, user_id])
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'historique : {e}")
            return []
    
    def get_platform_revenue_stats(self, start_date: str = None, end_date: str = None) -> Dict:
        """
        Récupère les statistiques de revenus de la plateforme
        
        Args:
            start_date: Date de début (format YYYY-MM-DD)
            end_date: Date de fin (format YYYY-MM-DD)
            
        Returns:
            Dictionnaire avec les statistiques
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                conditions = ["payment_status IN ('paid', 'completed')"]
                params = []
                
                if start_date:
                    conditions.append("DATE(created_at) >= ?")
                    params.append(start_date)
                
                if end_date:
                    conditions.append("DATE(created_at) <= ?")
                    params.append(end_date)
                
                where_clause = " AND ".join(conditions)
                
                cursor.execute(f'''
                    SELECT 
                        COUNT(*) as total_payments,
                        SUM(amount) as total_revenue,
                        SUM(commission_amount) as platform_revenue,
                        SUM(driver_amount) as driver_revenue,
                        AVG(amount) as avg_payment_amount
                    FROM payments
                    WHERE {where_clause}
                ''', params)
                
                result = cursor.fetchone()
                
                return dict(result) if result else {}
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des statistiques : {e}")
            return {}


# Instance globale du gestionnaire de base de données
db_manager = DatabaseManager()


# Fonctions utilitaires pour l'utilisation dans le bot
def init_payment_database() -> bool:
    """
    Initialise la base de données pour les paiements
    
    Returns:
        True si l'initialisation réussit
    """
    return db_manager.initialize_database()


def create_payment_record(booking_id: int, trip_id: int, passenger_id: int,
                         driver_id: int, amount: float, paypal_payment_id: str = None) -> Optional[int]:
    """
    Crée un enregistrement de paiement
    
    Returns:
        ID du paiement créé
    """
    return db_manager.save_payment(booking_id, trip_id, passenger_id, driver_id, amount, paypal_payment_id)


def update_payment_record(payment_id: int = None, paypal_payment_id: str = None,
                         status: str = None, payout_id: str = None) -> bool:
    """
    Met à jour un enregistrement de paiement
    
    Returns:
        True si la mise à jour réussit
    """
    return db_manager.update_payment_status(payment_id, paypal_payment_id, status, payout_id)


def calculate_payment_split(amount: float) -> Dict[str, float]:
    """
    Calcule la répartition des revenus
    
    Returns:
        Dictionnaire avec les montants calculés
    """
    return db_manager.calculate_revenue_split(amount)


def store_user_paypal(user_id: int, email: str) -> bool:
    """
    Stocke l'email PayPal d'un utilisateur
    
    Returns:
        True si l'enregistrement réussit
    """
    return db_manager.save_user_paypal_email(user_id, email)


def get_user_paypal(user_id: int) -> Optional[str]:
    """
    Récupère l'email PayPal d'un utilisateur
    
    Returns:
        Email PayPal ou None
    """
    return db_manager.get_user_paypal_email(user_id)


def get_payment_info(payment_id: int = None, paypal_id: str = None) -> Optional[Dict]:
    """
    Récupère les informations d'un paiement
    
    Returns:
        Dictionnaire avec les détails du paiement
    """
    return db_manager.get_payment_details(payment_id, paypal_id)


def get_user_payments(user_id: int, role: str = 'all') -> List[Dict]:
    """
    Récupère l'historique des paiements d'un utilisateur
    
    Returns:
        Liste des paiements
    """
    return db_manager.get_user_payment_history(user_id, role)


def get_revenue_statistics(start_date: str = None, end_date: str = None) -> Dict:
    """
    Récupère les statistiques de revenus
    
    Returns:
        Dictionnaire avec les statistiques
    """
    return db_manager.get_platform_revenue_stats(start_date, end_date)


if __name__ == "__main__":
    # Tests basiques
    print("🔄 Test du gestionnaire de base de données...")
    
    # Initialisation
    if init_payment_database():
        print("✅ Base de données initialisée")
        
        # Test de calcul de répartition
        split = calculate_payment_split(100.0)
        print(f"✅ Répartition pour 100 CHF : {split}")
        
        # Test de stockage d'email PayPal
        test_user_id = 12345
        test_email = "test@paypal.com"
        
        if store_user_paypal(test_user_id, test_email):
            print(f"✅ Email PayPal stocké pour l'utilisateur {test_user_id}")
            
            # Test de récupération
            retrieved_email = get_user_paypal(test_user_id)
            if retrieved_email == test_email:
                print(f"✅ Email PayPal récupéré : {retrieved_email}")
            else:
                print(f"❌ Erreur de récupération d'email")
        
        print("✅ Tests terminés avec succès !")
    else:
        print("❌ Erreur lors de l'initialisation de la base de données")
