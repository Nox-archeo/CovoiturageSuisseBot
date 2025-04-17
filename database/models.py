from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    username = Column(String)
    stripe_account_id = Column(String)
    rating = Column(Float, default=5.0)
    is_admin = Column(Boolean, default=False)

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

class Booking(Base):
    __tablename__ = 'bookings'
    id = Column(Integer, primary_key=True)
    trip_id = Column(Integer, ForeignKey('trips.id'))
    passenger_id = Column(Integer, ForeignKey('users.id'))
    status = Column(String)  # 'pending', 'confirmed', 'completed', 'cancelled'
    payment_id = Column(String)
    passenger = relationship("User")
    trip = relationship("Trip")
