from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, BigInteger
from sqlalchemy.orm import relationship
from .db_manager import Base
from datetime import datetime  # Ajout de l'import manquant

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)  # ← CORRECTION CRITIQUE
    username = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Profil conducteur
    is_driver = Column(Boolean, default=False, nullable=False)
    driver_rating = Column(Float, default=5.0, nullable=False)
    car_model = Column(String(100), nullable=True)
    license_verified = Column(Boolean, default=False, nullable=False)
    
    # Profil passager
    is_passenger = Column(Boolean, default=False, nullable=False)
    passenger_rating = Column(Float, default=5.0, nullable=False)
    
    # Commun - Retrait de subscription_end qui n'est pas utilisé
    stripe_customer_id = Column(String(100), nullable=True)
    stripe_subscription_id = Column(String(100), nullable=True)
    stripe_account_id = Column(String(100), nullable=True)  # ID du compte Stripe Connect Express pour les conducteurs
    is_admin = Column(Boolean, default=False)
    language = Column(String(10), default='fr')
    phone = Column(String(20))
    license_plate = Column(String(20))
    
    # Informations de vérification
    id_verified = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    phone_verified = Column(Boolean, default=False)
    gender = Column(String(1))  # 'F' pour femme, 'M' pour homme
    identity_verified = Column(Boolean, default=False)  # Vérification d'identité
    
    # Préférences générales
    preferred_language = Column(String(10), default='fr')
    notification_preferences = Column(Text)
    female_only = Column(Boolean, default=False)
    
    # Stats et réputation
    trips_completed = Column(Integer, default=0)
    average_delay = Column(Integer, default=0)
    response_rate = Column(Float, default=0.0)

    # Ajout du champ pour le nom complet
    full_name = Column(String(100))
    age = Column(Integer, nullable=True)
    
    # Champ PayPal
    paypal_email = Column(String(254), nullable=True)  # Email PayPal pour recevoir les paiements

    def __init__(self, **kwargs):
        # S'assurer que les champs requis ont des valeurs par défaut
        kwargs.setdefault('is_driver', False)
        kwargs.setdefault('is_passenger', False)
        kwargs.setdefault('driver_rating', 5.0)
        kwargs.setdefault('passenger_rating', 5.0)
        kwargs.setdefault('trips_completed', 0)
        kwargs.setdefault('response_rate', 0.0)
        super().__init__(**kwargs)

class Trip(Base):
    __tablename__ = 'trips'
    id = Column(Integer, primary_key=True)
    driver_id = Column(Integer, ForeignKey('users.id'))
    departure_city = Column(String(100))
    arrival_city = Column(String(100))
    departure_time = Column(DateTime)
    seats_available = Column(Integer)
    price_per_seat = Column(Float)
    additional_info = Column(Text)
    driver = relationship("User", foreign_keys=[driver_id])
    bookings = relationship("Booking", back_populates="trip")
    
    # CORRECTION CRITIQUE: Ajout du prix total du trajet
    total_trip_price = Column(Float, nullable=True)  # Prix total théorique du trajet
    
    # Nouvelles colonnes
    smoking = Column(String(20), default="no_smoking")
    music = Column(String(20), default="music_ok")
    talk_preference = Column(String(20), default="depends")
    pets_allowed = Column(String(20), default="no_pets")
    luggage_size = Column(String(20), default="medium")
    stops = Column(Text)  # Liste de villes intermédiaires
    highway = Column(Boolean, default=True)  # Trajet par autoroute
    flexible_time = Column(Boolean, default=False)  # Horaire flexible
    women_only = Column(Boolean, default=False)  # Option "Entre femmes"
    instant_booking = Column(Boolean, default=True)  # Réservation instantanée
    is_published = Column(Boolean, default=False)  # Trajet publié dans l'annuaire public

    # Ajout de fonctionnalités essentielles
    recurring = Column(Boolean, default=False)  # Trajet régulier
    group_id = Column(String, nullable=True)  # ID de groupe pour trajets réguliers/aller-retour
    return_trip_id = Column(Integer, ForeignKey('trips.id'), nullable=True)  # Pour les allers-retours
    booking_deadline = Column(DateTime)  # Délai de réservation
    meeting_point = Column(String)  # Point de rendez-vous précis
    car_description = Column(String)  # Description du véhicule
    total_distance = Column(Float)  # Distance en km
    estimated_duration = Column(Integer)  # Durée estimée en minutes
    
    # NOUVELLE FONCTIONNALITÉ: Support rôle conducteur/passager
    trip_role = Column(String, default="driver")  # "driver" ou "passenger"
    creator_id = Column(Integer, ForeignKey('users.id'))  # Créateur du trajet (peut être différent du conducteur)
    creator = relationship("User", foreign_keys=[creator_id])  # Relation vers le créateur
    is_cancelled = Column(Boolean, default=False)  # Annulation du trajet
    
    # Champs pour PayPal
    status = Column(String, default='active')  # 'active', 'completed', 'cancelled', 'completed_payment_pending'
    payout_batch_id = Column(String, nullable=True)  # ID du paiement envoyé au conducteur
    last_paypal_reminder = Column(DateTime, nullable=True)  # Dernière date d'envoi du rappel PayPal
    
    # Champs pour la double confirmation
    confirmed_by_driver = Column(Boolean, default=False)  # Confirmation du conducteur
    confirmed_by_passengers = Column(Boolean, default=False)  # Confirmation des passagers
    driver_amount = Column(Float, nullable=True)  # Montant versé au conducteur (88%)
    commission_amount = Column(Float, nullable=True)  # Commission de la plateforme (12%)

class Booking(Base):
    __tablename__ = 'bookings'
    id = Column(Integer, primary_key=True)
    trip_id = Column(Integer, ForeignKey('trips.id'))
    passenger_id = Column(Integer, ForeignKey('users.id'))
    status = Column(String)  # 'pending', 'confirmed', 'completed', 'cancelled'
    booking_status = Column(String, default='pending')  # 'pending', 'confirmed', 'pending_payment', 'completed', 'cancelled'
    payment_id = Column(String)
    seats = Column(Integer, default=1)  # Nombre de places réservées
    seats_booked = Column(Integer, default=1)  # Alias pour compatibilité
    booking_date = Column(DateTime, default=datetime.utcnow)
    amount = Column(Float)  # Montant total payé
    is_paid = Column(Boolean, default=False)  # Indique si le paiement a été effectué
    stripe_session_id = Column(String)  # ID de la session de paiement Stripe
    stripe_payment_intent_id = Column(String)  # ID de l'intent de paiement Stripe
    
    # Champs PayPal
    paypal_payment_id = Column(String, nullable=True)  # ID du paiement PayPal
    payment_status = Column(String, default='unpaid')  # 'unpaid', 'pending', 'completed', 'cancelled'
    total_price = Column(Float, nullable=True)  # Montant total (calculé dynamiquement)
    
    # CORRECTION CRITIQUE: Champs pour les remboursements automatiques
    refund_id = Column(String, nullable=True)  # ID du remboursement PayPal
    refund_amount = Column(Float, nullable=True)  # Montant remboursé
    refund_date = Column(DateTime, nullable=True)  # Date du remboursement
    original_price = Column(Float, nullable=True)  # Prix original payé
    
    passenger = relationship("User", foreign_keys=[passenger_id])
    trip = relationship("Trip", foreign_keys=[trip_id], back_populates="bookings")

class DriverProposal(Base):
    """Modèle pour les propositions de conducteurs aux trajets de passagers"""
    __tablename__ = 'driver_proposals'
    id = Column(Integer, primary_key=True)
    trip_id = Column(Integer, ForeignKey('trips.id'))  # Trajet du passager
    driver_id = Column(Integer, ForeignKey('users.id'))  # Conducteur qui propose
    status = Column(String, default='pending')  # 'pending', 'accepted', 'rejected', 'cancelled'
    proposal_date = Column(DateTime, default=datetime.utcnow)
    accepted_at = Column(DateTime, nullable=True)  # Date d'acceptation
    rejected_at = Column(DateTime, nullable=True)  # Date de refus
    message = Column(String)  # Message du conducteur
    proposed_price = Column(Float)  # Prix proposé par le conducteur
    car_info = Column(String)  # Infos sur le véhicule
    pickup_point = Column(String)  # Point de ramassage proposé
    
    # Relations
    trip = relationship("Trip")
    driver = relationship("User", foreign_keys=[driver_id])
    
    # Champs pour le suivi du paiement (réutilise la logique existante)
    payment_id = Column(String, nullable=True)
    payment_status = Column(String, default='unpaid')  # 'unpaid', 'pending', 'paid', 'completed'

class Message(Base):
    """Pour la messagerie entre utilisateurs"""
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    sender_id = Column(Integer, ForeignKey('users.id'))
    recipient_id = Column(Integer, ForeignKey('users.id'))
    trip_id = Column(Integer, ForeignKey('trips.id'))
    content = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    read = Column(Boolean, default=False)

class Review(Base):
    """Système d'évaluation détaillé"""
    __tablename__ = 'reviews'
    id = Column(Integer, primary_key=True)
    trip_id = Column(Integer, ForeignKey('trips.id'))
    reviewer_id = Column(Integer, ForeignKey('users.id'))
    reviewed_id = Column(Integer, ForeignKey('users.id'))
    rating = Column(Integer)  # 1-5
    punctuality = Column(Integer)  # 1-5
    cleanliness = Column(Integer)  # 1-5
    communication = Column(Integer)  # 1-5
    comment = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
