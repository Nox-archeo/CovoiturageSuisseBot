from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .db_manager import Base
from datetime import datetime  # Ajout de l'import manquant

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Profil conducteur
    is_driver = Column(Boolean, default=False, nullable=False)
    driver_rating = Column(Float, default=5.0, nullable=False)
    car_model = Column(String, nullable=True)
    license_verified = Column(Boolean, default=False, nullable=False)
    
    # Profil passager
    is_passenger = Column(Boolean, default=False, nullable=False)
    passenger_rating = Column(Float, default=5.0, nullable=False)
    
    # Commun - Retrait de subscription_end qui n'est pas utilisé
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
    stripe_account_id = Column(String, nullable=True)  # ID du compte Stripe Connect Express pour les conducteurs
    is_admin = Column(Boolean, default=False)
    language = Column(String, default='fr')
    phone = Column(String)
    license_plate = Column(String)
    
    # Informations de vérification
    id_verified = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    phone_verified = Column(Boolean, default=False)
    gender = Column(String)  # 'F' pour femme, 'M' pour homme
    identity_verified = Column(Boolean, default=False)  # Vérification d'identité
    
    # Préférences générales
    preferred_language = Column(String, default='fr')
    notification_preferences = Column(String)
    female_only = Column(Boolean, default=False)
    
    # Stats et réputation
    trips_completed = Column(Integer, default=0)
    average_delay = Column(Integer, default=0)
    response_rate = Column(Float, default=0.0)

    # Ajout du champ pour le nom complet
    full_name = Column(String)

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
    departure_city = Column(String)
    arrival_city = Column(String)
    departure_time = Column(DateTime)
    seats_available = Column(Integer)
    price_per_seat = Column(Float)
    additional_info = Column(String)
    driver = relationship("User")
    bookings = relationship("Booking")
    
    # Nouvelles colonnes
    smoking = Column(String, default="no_smoking")
    music = Column(String, default="music_ok")
    talk_preference = Column(String, default="depends")
    pets_allowed = Column(String, default="no_pets")
    luggage_size = Column(String, default="medium")
    stops = Column(String)  # Liste de villes intermédiaires
    highway = Column(Boolean, default=True)  # Trajet par autoroute
    flexible_time = Column(Boolean, default=False)  # Horaire flexible
    women_only = Column(Boolean, default=False)  # Option "Entre femmes"
    instant_booking = Column(Boolean, default=True)  # Réservation instantanée
    is_published = Column(Boolean, default=False)  # Trajet publié dans l'annuaire public

    # Ajout de fonctionnalités essentielles
    recurring = Column(Boolean, default=False)  # Trajet régulier
    return_trip_id = Column(Integer, ForeignKey('trips.id'), nullable=True)  # Pour les allers-retours
    booking_deadline = Column(DateTime)  # Délai de réservation
    meeting_point = Column(String)  # Point de rendez-vous précis
    car_description = Column(String)  # Description du véhicule
    available_seats = Column(Integer)  # Places restantes (mise à jour automatique)
    total_distance = Column(Float)  # Distance en km
    estimated_duration = Column(Integer)  # Durée estimée en minutes
    is_cancelled = Column(Boolean, default=False)  # Annulation du trajet

class Booking(Base):
    __tablename__ = 'bookings'
    id = Column(Integer, primary_key=True)
    trip_id = Column(Integer, ForeignKey('trips.id'))
    passenger_id = Column(Integer, ForeignKey('users.id'))
    status = Column(String)  # 'pending', 'confirmed', 'completed', 'cancelled'
    payment_id = Column(String)
    seats = Column(Integer, default=1)  # Nombre de places réservées
    booking_date = Column(DateTime, default=datetime.utcnow)
    amount = Column(Float)  # Montant total payé
    is_paid = Column(Boolean, default=False)  # Indique si le paiement a été effectué
    stripe_session_id = Column(String)  # ID de la session de paiement Stripe
    stripe_payment_intent_id = Column(String)  # ID de l'intent de paiement Stripe
    passenger = relationship("User")
    trip = relationship("Trip")

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
