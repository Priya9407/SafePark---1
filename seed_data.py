def seed_data():
    from models.model import db, User, Parking_lot, Parking_spot, Reservation
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo
    import random
    from werkzeug.security import generate_password_hash
    from faker import Faker

    fake = Faker()
    Zone = ZoneInfo("Asia/Kolkata")

    # ---- Seed Users ----
    for i in range(5):
        username = f"user{i}"
        if not User.query.filter_by(username=username).first():
            db.session.add(User(
                name=fake.name(),
                email=f"{username}@example.com",
                address=fake.address(),
                username=username,
                password=generate_password_hash("user"),
                role="user",
                pin_code=random.randint(600000, 699999)
            ))
    db.session.commit()

    # ---- Seed Lots & Spots ----
    for i in range(10):  # fewer for simplicity
        lot_name = fake.street_name()
        if not Parking_lot.query.filter_by(lot_location=lot_name).first():
            lot = Parking_lot(
                lot_location=lot_name,
                address=fake.address(),
                pin_code=random.randint(600000, 699999),
                price=random.randint(10, 20),
                max_spots=3
            )
            db.session.add(lot)
            db.session.flush()

            for j in range(1, lot.max_spots + 1):
                spot_id = f"P{lot.id}S{j}"
                if not Parking_spot.query.get(spot_id):
                    db.session.add(Parking_spot(
                        id=spot_id,
                        lot_id=lot.id,
                        status="active"
                    ))
    db.session.commit()

    # ---- Seed Reservations ----
    users = User.query.filter(User.username.like("user%")).all()
    lots = Parking_lot.query.all()
    print(users)
    for lot in lots:
        for spot in lot.spots:
            if not Reservation.query.filter_by(spot_id=spot.id).first():
                user = random.choice(users)
                status = random.choice(["occupied", "released"])
                start_time = datetime.now(Zone) - timedelta(hours=random.randint(1, 5))
                end_time = None

                if status == "released":
                    end_time = start_time + timedelta(hours=random.randint(1, 5))
                    duration_hours = (end_time - start_time).total_seconds() / 3600
                else:
                    duration_hours = (datetime.now(Zone) - start_time).total_seconds() / 3600

                earned = int(duration_hours * lot.price)

                reservation = Reservation(
                    spot_id=spot.id,
                    lot_id=lot.id,
                    customer_id=user.id,
                    vehicle_no=f"TN{random.randint(10,99)}{random.choice(['AA','AB','BA'])}{random.randint(1000,9999)}",
                    start_time=start_time,
                    end_time=end_time,
                    price_earned=earned,
                    status=status
                )

                if status == "occupied":
                    spot.status = "occupied"

                lot.total_price += earned
                db.session.add(reservation)

    db.session.commit()
    print("Data added without clashes.")
