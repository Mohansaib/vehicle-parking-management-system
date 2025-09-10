from flask_sqlalchemy import SQLAlchemy
from datetime import datetime,timezone
db = SQLAlchemy()

class User(db.Model):
    id= db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(50), nullable=False,unique=True)
    email=db.Column(db.String(60),nullable=False,unique=True)
    password=db.Column(db.String(100),nullable=False)

class ParkingLot(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    prime_location_name=db.Column(db.String(100),nullable=False)
    price=db.Column(db.Integer,nullable=False)
    address=db.Column(db.String(200),nullable=False)
    pincode=db.Column(db.String(8),nullable=False)
    maximum_number_of_spots=db.Column(db.Integer,nullable=False)
    
    spots = db.relationship('ParkingSpot', backref='lot', lazy='dynamic')

class ParkingSpot(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    lot_id = db.Column(db.Integer,db.ForeignKey("parking_lot.id"),nullable=False)
    status = db.Column(db.String(1),nullable=False,default='A')
    
class Reservation(db.Model):
    id =db.Column(db.Integer,primary_key=True)
    spot_id=db.Column(db.Integer,db.ForeignKey('parking_spot.id'),nullable=False)
    user_id=db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)
    parking_timestamp=db.Column(db.DateTime,default= lambda:datetime.now(timezone.utc))
    leaving_timestamp=db.Column(db.DateTime,nullable=True)
    
    cost_per_unit_time=db.Column(db.Integer,nullable=False,default=10)
    user=db.relationship('User',backref='reservations')
    spot=db.relationship('ParkingSpot',backref='reservations')