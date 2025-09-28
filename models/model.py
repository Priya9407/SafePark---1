from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

db = SQLAlchemy()

class User(db.Model, UserMixin):
    
    __tablename__ = 'user' 
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    name=db.Column(db.String(150))
    email=db.Column(db.String(150),nullable=False,unique=True)
    address=db.Column(db.String(150))
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150),nullable=False)
    role = db.Column(db.String(50), default='user')
    pin_code=db.Column(db.Integer,nullable=False)

    reservation=db.relationship('Reservation',backref=db.backref('user',lazy=True))

class Parking_lot(db.Model):

   __tablename__ = 'parking_lot' 
   
   id = db.Column(db.Integer, primary_key=True,autoincrement=True)
   lot_location=db.Column(db.String(150),nullable=False)
   address=db.Column(db.String(150))
   pin_code=db.Column(db.Integer,nullable=False)
   price=db.Column(db.Integer,nullable=False)
   max_spots=db.Column(db.Integer,nullable=False)
   total_price=db.Column(db.Integer,nullable=False,default=0)

   reservation=db.relationship('Reservation',backref=db.backref('lots',lazy=True))

   
class Parking_spot(db.Model):

   __tablename__ = 'parking_spot' 

   id=db.Column(db.String(100),primary_key=True)
   lot_id=db.Column(db.Integer,db.ForeignKey('parking_lot.id'),nullable=False)
   status=db.Column(db.String(10),default='active')

   reservation=db.relationship('Reservation',backref=db.backref('spots',lazy=True))

   lot=db.relationship('Parking_lot',backref=db.backref('spots',lazy=True))

class Reservation(db.Model):

   __tablename__='reservation'

   id = db.Column(db.Integer, primary_key=True,autoincrement=True)
   spot_id=db.Column(db.String(100),db.ForeignKey('parking_spot.id'),nullable=False)
   lot_id=db.Column(db.Integer,db.ForeignKey('parking_lot.id'),nullable=False)
   customer_id=db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)
   vehicle_no=db.Column(db.String(10),nullable=False)
   start_time=db.Column(db.DateTime(timezone=True),nullable=False,default=lambda:datetime.now(ZoneInfo("Asia/Kolkata")))
   end_time=db.Column(db.DateTime(timezone=True))
   price_earned=db.Column(db.Integer,default=0)
   status=db.Column(db.String(20),default='occupied')