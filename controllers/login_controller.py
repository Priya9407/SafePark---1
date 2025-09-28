from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models.model import db, User,Parking_lot,Parking_spot,Reservation

main = Blueprint('main', __name__)

@main.route('/')
def home():
    return render_template("home/home.html")

@main.route('/error404')
def error404():
    return render_template("home/404.html")

@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        name = request.form['name'].strip()
        address = request.form['address']
        email = request.form['email'].strip()
        password = request.form['password'].strip()
        pwda = request.form['pwda']
        pin_code=request.form['pincode']
        import re
        if not re.match(r'^[a-zA-Z0-9_.]+$', username):
            flash("Username should not contain special characters.")
            return redirect(url_for('main.register'))
        if not re.match(r'^[a-zA-Z\s]+$', name):
            flash("Name should not contain special characters or numbers.")
            return redirect(url_for('main.register'))
        if User.query.filter_by(username=username).first():
            flash("Username already exists!")
            return redirect(url_for('main.register'))
        if User.query.filter_by(email=email).first():
            flash("An account with this email already exists!")
            return redirect(url_for('main.register'))
        if '@' not in email:
            flash("Invalid email address! '@' is missing.")
            return redirect(url_for('main.register'))
        if not (pin_code.isdigit() and len(pin_code) == 6):
            flash("PIN code must be a 6-digit number.")
            return redirect(url_for('main.register'))
        if password != pwda:
            flash("Passwords do not match!")
            return redirect(url_for('main.register'))
        if not (password.isdigit() and len(password) >= 8):
            flash("Password length must be atleast 8.")
            return redirect(url_for('main.register'))
        
        new_user = User(
            name=name,
            email=email,
            address=address,
            username=username,
            pin_code=pin_code,
            password=generate_password_hash(password),
            role="user"
        )

        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('main.dashboard',username=new_user.username,role=new_user.role))
    return render_template("home/register.html")


@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_input = request.form['password']

        user = User.query.filter_by(username=username).first()
        email= User.query.filter_by(email=username).first()
        print(user, email)
        if user and check_password_hash(user.password, password_input):
            login_user(user)
            return redirect(url_for('main.dashboard',username=user.username,role=user.role))
        elif email and check_password_hash(email.password, password_input):
            login_user(email)
            return redirect(url_for('main.dashboard',username=email.username,role=email.role))
        else:
            flash("User does not exists.")
            return redirect(url_for('main.login'))
    return render_template('home/login.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

#dashboard
@main.route('/<role>/<username>', methods=['GET', 'POST'])
@main.route('/<role>/<username>/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard(role,username):
    lots=Parking_lot.query.all()
    if current_user.role=='admin':
        total_lots=len(lots)
        amount=0
        dict={}
        dict2={}
        active=0
        occupied=0
        for lot in lots:
            amount=amount+lot.total_price
            dict[lot.id]=lot.total_price
            dict2[lot.id]=len(lot.reservation)
        spots=Parking_spot.query.all()
        for spot in spots:
            if spot.status=="active":
                active+=1
            elif spot.status=="occupied":
                occupied+=1
        reservations=list(Reservation.query.order_by(Reservation.id.desc()).limit(3).all())
        print(reservations)
        return render_template("/admin/admin_dashboard.html",dict=dict,dict2=dict2,user=current_user,lots=lots,total=total_lots,reservations=reservations,amount=amount,active=active,occupied=occupied)
    if current_user.username!=username:
        return redirect(url_for('main.login'))
    active_spot_counts = {}
    for lot in lots:
        active_count = sum(1 for spot in lot.spots if spot.status.lower() == 'active')
        active_spot_counts[lot.id] = active_count
    if request.method == 'POST' and role=='user':
        lot_id=request.form.get('lot_id')
        spot_id=request.form.get('spot_id')
        vehicle_no=request.form.get('vehicle')
        if not(vehicle_no and spot_id):
            return redirect(url_for('main.error404'))
        spot=Parking_spot.query.get(spot_id)
        if not spot or spot.status=="occupied":
            return redirect(url_for('main.book_spot',current_lot=lot_id,user=current_user,role=current_user.role,username=current_user.username))
        user=User.query.filter_by(username=username).first()
        user_id=user.id
        new_reservation=Reservation(
                lot_id=lot_id,spot_id=spot_id,vehicle_no=vehicle_no,customer_id=user_id
                )
        spot.status="occupied"
        db.session.add(new_reservation)
        db.session.commit()
        lots=Parking_lot.query.all()
        return render_template('user/dashboard.html', user=current_user,lots=lots,active_spot_counts=active_spot_counts)
    
    return render_template('user/dashboard.html', user=current_user,lots=lots,active_spot_counts=active_spot_counts)

@main.route('/<role>/<username>/lots', methods=['GET', 'POST'])
@login_required
def lots(role,username):
    lots=Parking_lot.query.all()
    if current_user.role=="admin":
        return render_template("/admin/admin_lot.html",user=current_user,lots=lots,search=0)
    return redirect(url_for('main.error404'))

#for admin 
@main.route('/<role>/<username>/users')
@login_required
def admin_users(role,username):
    print("here")
    if role=="admin":
        users=User.query.filter_by(role="user").all()
        return render_template("admin/admin_users.html",user=current_user,users=users)
    return redirect(url_for('main.dashboard',username=current_user.username,role=current_user.role))

@main.route('/<role>/<username>/search_user', methods=['GET', 'POST'])
@login_required
def search_user(role,username):
    from sqlalchemy import or_,and_
    users=User.query.filter(User.role!='admin').all()
    if request.method == 'POST':
        search=0
        q = request.form['search'].strip()
        querys=("%"+q+"%")
        if(q!=""):
            search=1
            users=User.query.filter(
            and_(
                User.role != 'admin',
                or_(
                    User.id.like(querys),
                    User.address.like(querys),
                    User.pin_code.like(querys),
                    User.username.like(querys),
                    User.name.like(querys),
                    User.email.like(querys)
                )
            )
                ).all()

        if role=="admin":
            return render_template('admin/admin_users.html', user=current_user,users=users,search=search,q=q)
        else:
            return redirect(url_for('main.dashboard',role=current_user.role,username=current_user.username))
    return redirect(url_for('main.dashboard',role=current_user.role,username=current_user.username))
 
@main.route('/<role>/<username>/search', methods=['GET', 'POST'])
@login_required
def search_all(role,username):
    if current_user.role=="admin":
        return render_template("admin/search.html")
    return redirect(url_for('main.dashboard',username=current_user.username,role=current_user.role))

@main.route('/<role>/<username>/search_admin', methods=['GET', 'POST'])
@login_required
def search_admin(role, username):
    if(role=='admin'):
        if request.method == 'POST':
            search_value = request.form.get('search_value').strip()
            search_by = request.form.get('search_by')
            search=1
            if not search_by or search_value=="":
                return redirect(url_for('main.search_admin', role=role, username=username))
            
            results = []

            if search_by == 'spot':
                results = Parking_spot.query.filter(Parking_spot.id.like(f"%{search_value}%")).all()

            elif search_by == 'lot':
                results = Parking_lot.query.filter(Parking_lot.id.like(f"%{search_value}%")).all()

            elif search_by == 'user':
                results = User.query.filter(
                    User.username.like(f"%{search_value}%"),
                    User.role != 'admin'
                ).all()

            elif search_by == 'reservation':
                results = Reservation.query.filter(Reservation.id.like(f"%{search_value}%")).all()

            elif search_by == 'vehicle':
                results = Reservation.query.filter(Reservation.vehicle_no.like(f"%{search_value}%")).all()

            return render_template("admin/search.html", results=results, search_by=search_by,search=search,role=role, username=username,search_value=search_value)

        return render_template("admin/search.html", results=None, search_by=None, role=role, username=username)
    return redirect(url_for('main.dashboard',username=current_user.username,role=current_user.role))

@main.route('/<role>/<username>/summary', methods=['GET', 'POST'])
@login_required
def summary(role,username):
    lots=Parking_lot.query.all()
    if current_user.role=='admin':
        total_lots=len(lots)
        amount=0
        dict={}
        dict2={}
        active=0
        occupied=0
        for lot in lots:
            amount=amount+lot.total_price
            dict[lot.id]=lot.total_price
            dict2[lot.id]=len(lot.reservation)
        spots=Parking_spot.query.all()
        for spot in spots:
            if spot.status=="active":
                active+=1
            elif spot.status=="occupied":
                occupied+=1
        reservations=list(Reservation.query.order_by(Reservation.id.desc()).all())
        return render_template("/admin/admin_summary.html",dict=dict,dict2=dict2,user=current_user,lots=lots,total=total_lots,reservations=reservations,amount=amount,active=active,
        occupied=occupied)
    elif(role=='user'):
        reservations=Reservation.query.filter_by(customer_id=current_user.id).all()
        total=0
        released=0
        occupied=0
        lot_reservation_count = {}
        for i in reservations:
            total=total+i.price_earned
            if(i.status=="released"):
                released+=1
            elif(i.status=="occupied"):
                occupied+=1
            if i.lot_id in lot_reservation_count:
                lot_reservation_count[i.lot_id] += 1
            else:
                lot_reservation_count[i.lot_id] = 1

        return render_template("user/summary.html",released=released,occupied=occupied,total=total,
        lot_reservation_count=lot_reservation_count)
    return redirect(url_for('main.dashboard',username=current_user.username,role=current_user.role))


@main.route('/<role>/<username>/new_lot', methods=['GET', 'POST'])
@login_required
def new_lot(role,username):
    if current_user.role=="admin":
        used_ids = [lot.id for lot in Parking_lot.query.order_by(Parking_lot.id).all()]
        expected = 1
        for id in used_ids:
            if id != expected:
                expected=id-1
                break
            expected += 1
        new_id = expected
        if request.method == 'POST':
            lot_location = request.form['name'].strip()
            address = request.form['address'].strip()
            pin_code = request.form['pin_code'].strip()
            price = request.form['price'].strip()
            max_spots = request.form['max_spots'].strip()

            new_lot=Parking_lot(id=new_id,lot_location=lot_location,address=address,pin_code=pin_code,price=price,max_spots=max_spots)
            db.session.add(new_lot)
            db.session.commit()

            for i in range(int(max_spots)):
                new_spot=Parking_spot(
                    id=f"P{new_lot.id}S{i+1}",lot_id=new_lot.id,status='active'
                )
                db.session.add(new_spot)
            db.session.commit()
            return redirect(url_for('main.lots',role=current_user.role,username=current_user.username))
        return render_template("admin/new_lot.html",new_id=new_id)
    return redirect(url_for('main.dashboard',username=current_user.username,role=current_user.role))    

@main.route('/<role>/<username>/delete_lot/lot/<int:lot_id>/delete',methods=['POST'])
@login_required
def delete_lot(role,username,lot_id):
    if current_user.role=="admin":
        lot=Parking_lot.query.get(lot_id)
        for spot in lot.spots:
            for res in spot.reservation:
                db.session.delete(res)
            db.session.delete(spot)
        db.session.delete(lot)
        db.session.commit()
        return redirect(url_for('main.lots',role=current_user.role, username=current_user.username))
    return redirect(url_for('main.dashboard',username=current_user.username,role=current_user.role))   


@main.route('/<role>/<username>/view_lot',methods=['GET','POST'])
@login_required
def view_lot(role,username):
    if current_user.role=="admin":
        lot_id=request.args.get('current_lot')
        lot=Parking_lot.query.get(lot_id)
        if not lot_id or not lot:
            return redirect(url_for('main.error404'))
        if request.method=='POST':
            spot_id=request.args.get('spot_id')
            print(spot_id)
            spot=Parking_spot.query.get(spot_id)
            
            if spot:   
                reservations = Reservation.query.filter_by(spot_id=spot.id).all()
                for res in reservations:
                    db.session.delete(res) 
                db.session.delete(spot)
                db.session.commit()
        lots=Parking_lot.query.all()
        active_spots=[]
        occupied=[]
        deleted=[]
        first_lot=Parking_lot.query.first()
        last_lot = Parking_lot.query.order_by(Parking_lot.id.desc()).first()
        for i in range(1,lot.max_spots+1):
            s="P"+str(lot.id)+"S"+str(i)
            spot=Parking_spot.query.get(s)
            if not spot:
                deleted.append(s)
            elif spot.status=="active":
                active_spots.append(spot.id)
            elif spot.status=="occupied":
                occupied.append(spot.id)
        return render_template("admin/view_lot.html",lot=lot,lots=lots,active_spots=active_spots,occupied=occupied,deleted=deleted,user=current_user,first_lot_id=first_lot,last_lot_id=last_lot)
    return redirect(url_for('main.dashboard',username=current_user.username,role=current_user.role))   

@main.route('/<role>/<username>/view_spot')
@login_required
def view_spot(role,username):
    lots=Parking_lot.query.all()
    spot_id=request.args.get('current_spot')
    lot_id=request.args.get('current_lot')
    lot=Parking_lot.query.get(lot_id)
    spot=Parking_spot.query.get(spot_id)
    if(role=="admin"):
        if not spot_id or not spot or not lot or not lot_id:
            return redirect(url_for('main.error404'))
        return render_template("admin/view_spot.html",spot=spot,lot=lot,lots=lots)
    return redirect(url_for('main.dashboard',username=current_user.username,role=current_user.role))


@main.route('/<role>/<username>/lot/<int:lot_id>/spot/<spot_id>/readd', methods=['GET','POST'])
@login_required
def readd_spot(role, username, lot_id, spot_id):
    if current_user.role == "admin":
        if spot_id:
            new_spot = Parking_spot(id=spot_id, lot_id=lot_id, status='active')
            db.session.add(new_spot)
            db.session.commit()
    return redirect(url_for('main.view_lot', role=role, username=username,current_lot=lot_id))

@main.route('/<role>/<username>/edit_lot', methods=['GET', 'POST'])
@login_required
def edit_lot(role,username):
    if(role=="admin"):
        lot_id=request.args.get('current_lot')
        lot=Parking_lot.query.get(lot_id)
        
        if not lot_id or not lot:
            return redirect(url_for('main.error404'))
        lot_spots=int(lot.max_spots)

        if request.method == 'POST':
            lot.lot_location = request.form['name']
            lot.address = request.form['address']
            lot.pin_code = request.form['pin_code']
            lot.price = request.form['price']
            lot.max_spots = request.form['max_spots']
            db.session.commit()
            if int(lot.max_spots)>=lot_spots:
                for i in range(lot_spots,int(lot.max_spots)):
                    new_id = f"P{lot.id}S{i+1}"
                    existing = Parking_spot.query.get(new_id)
                    if not existing:
                        new_spot = Parking_spot(id=new_id, lot_id=lot.id, status='active')
                        db.session.add(new_spot)
                db.session.commit()

            else:
                return "cannot be done"
            
            return redirect(url_for('main.lots',role=current_user.role,username=current_user.username))
        return render_template("admin/edit_lot.html",lot=lot,user=current_user)
    return redirect(url_for('main.dashboard',username=current_user.username,role=current_user.role))

@main.route('/<role>/<username>/book_spot', methods=['GET', 'POST'])
@login_required
def book_spot(role,username):
    if current_user.role=="user":
        lot_id=request.args.get('current_lot')
        user_name=request.args.get('username')
        lot=Parking_lot.query.get(lot_id)
        user=User.query.filter_by(username=user_name).first()
        if not lot or not username:
            return redirect(url_for('main.error404'))
        active_spots=[]
        for i  in range(1,lot.max_spots+1):
            s="P"+str(lot.id)+"S"+str(i)
            spot=Parking_spot.query.filter_by(id=s).first()
            if spot:
                print(spot)
                if spot.status=="active":
                    print(spot.status)
                    active_spots.append(spot.id)
        return render_template("user/book_spot.html",lot=lot,active_spots=active_spots,user=current_user)
    return redirect(url_for('main.dashboard',username=current_user.username,role=current_user.role))      


@main.route('/<role>/<username>/search_lot', methods=['GET', 'POST'])
@login_required
def search(role,username):
    from sqlalchemy import or_
    lots=Parking_lot.query.all()
    active_spot_counts = {}
    for lot in lots:
        active_count = sum(1 for spot in lot.spots if spot.status.lower() == 'active')
        active_spot_counts[lot.id] = active_count
    if request.method == 'POST':
        search=0
        q = request.form['search'].strip()
        query="%"+q+"%"
        if(q!=""):
            search=1
            lots=Parking_lot.query.filter(
            or_(
                Parking_lot.lot_location.like(query),
                Parking_lot.address.like(query),
                Parking_lot.pin_code.like(query)
            )
        ).all()

        if current_user.role=="admin":
            return render_template('admin/admin_lot.html', user=current_user,lots=lots,search=search,q=q)
        else:
            return render_template('user/dashboard.html', user=current_user,lots=lots,search=search,q=q,active_spot_counts=active_spot_counts)
    return redirect(url_for('main.dashboard',username=current_user.username,role=current_user.role,search=search,q=q,active_spot_counts=active_spot_counts))      

@main.route('/<role>/<username>/history',methods=['GET','POST'])
@login_required
def history(role,username):
    if current_user.role=="user":
        print('hello')
        from datetime import datetime
        user=User.query.filter_by(username=username).first()
        reservation=Reservation.query.filter_by(customer_id=user.id).all()
        dict={}
        for i in reservation:
            list=[]
            start_date=i.start_time.strftime("%d-%m-%Y")
            start_time=i.start_time.strftime("%I:%M %p")
            list.append(start_date)
            list.append(start_time)
            lot=Parking_lot.query.filter_by(id=i.lot_id).first()
            list.append(lot)
            dict[i.id]=list
        if request.method=="POST":
            from datetime import datetime
            from zoneinfo import ZoneInfo
            reservation_id=request.args.get("reservation")
            reser=Reservation.query.get(reservation_id)
            lot=Parking_lot.query.get(reser.lot_id)
            spot=Parking_spot.query.get(reser.spot_id)
            reser.end_time=datetime.now(ZoneInfo("Asia/Kolkata")).replace(tzinfo=None)
            reser.status="released"
            reser.price_earned=request.args.get("price")
            spot.status="active"
            lot.total_price+=int(request.args.get("price"))
            db.session.commit()
            reservation=Reservation.query.filter_by(customer_id=user.id).all()
            return render_template('user/history.html',reservation=reservation,dict=dict)
        return render_template('user/history.html',reservation=reservation,dict=dict)
    return redirect(url_for('main.dashboard',username=current_user.username,role=current_user.role))  
    
@main.route("/<role>/<username>/profile")
@login_required
def profile(role,username):
    if(role=="user"):
        return render_template('user/profile.html')
    if(role=="admin"):
        return render_template('admin/profile.html')


@main.route("/<role>/<username>/release")
@login_required
def release(role,username):
    if current_user.role=="user":
        from datetime import datetime
        from zoneinfo import ZoneInfo
        end_time=datetime.now(ZoneInfo("Asia/Kolkata")).replace(tzinfo=None)
        user=User.query.filter_by(username=username).first()
        reservation_id=request.args.get("reservation_id")

        reservation=Reservation.query.get(reservation_id)
        lot=Parking_lot.query.get(reservation.lot_id)
        time=(end_time - reservation.start_time).total_seconds()/3600
        price=f'{(time*lot.price):.0f}'
        return render_template('user/release.html',reservation=reservation,user=user,end_time=end_time,price=price,lot=lot)
    return redirect(url_for('main.dashboard',username=current_user.username,role=current_user.role))  


@main.route('/<role>/<username>/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile(role,username):
    if request.method == 'POST':
        current_user.name=request.form['name'].strip()
        current_user.email=request.form['email'].strip()
        current_user.username=request.form['username'].strip()
        current_user.address=request.form['address'].strip()
        current_user.pin_code=request.form['pincode'].strip()

        db.session.commit()
        return redirect(url_for('main.profile',role=current_user.role,username=current_user.username))
    if(role=="user"):
        return render_template("user/edit_profile.html")
    else:
        return render_template("admin/edit_profile.html")


@main.route('/<role>/<username>/view_spot_details',methods=['GET','POST'])
def view_spot_details(role,username):
    if role=="admin":
        spot_id=request.args.get('current_spot')
        spot=Parking_spot.query.get(spot_id)
        return render_template("admin/view_spot_dets.html",spot=spot)
    