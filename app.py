from flask import Flask,request,redirect,url_for,session,render_template,flash
from flask_sqlalchemy import SQLAlchemy 
from dotenv import load_dotenv
from models import User,db,ParkingLot,ParkingSpot,Reservation
import os
from datetime import datetime,timezone
from sqlalchemy import func
load_dotenv()

admin_username = os.getenv('admin_username')
admin_email = os.getenv('admin_email')
admin_password = os.getenv('admin_password')

app = Flask(__name__)

app.secret_key ='MohanSai'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vehicle.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)


@app.route('/')
def home():
    return render_template('base.html')

@app.route('/adminpage')
def admin():
    if session.get('username') != admin_username:
        flash('Access Denied!')
        return redirect('/login')
    
    action = request.args.get('action', '')
    if(action == 'delete'):
        return render_template('adminpage.html',action=action,del_lots=ParkingLot.query.all())
    if(action == 'edit'):
        return redirect(url_for('admin_edit_lot'))
    if(action == 'view'):
        return redirect(url_for('admin_view_lot'))
    if(action == 'viewusers'):
        return redirect(url_for('admin_view_users'))
    if(action == 'summary'):
        return redirect(url_for('admin_pie_chart'))
    if(action == 'status'):
        return redirect(url_for('admin_view_spots'))
    return render_template('adminpage.html', action=action)

@app.route('/admin_add_lot', methods=['POST'])
def admin_add_lot():
    if(session.get('username')!=admin_username):
        flash('Access Denied!')
        return redirect('/')
    
    location = request.form.get('prime_location_name')
    price = request.form.get('price')
    address = request.form.get('address')
    pincode = request.form.get('pincode')
    max_spots = (int)(request.form.get('maximum_number_of_spots'))
    
    new_parking_lot= ParkingLot(
        prime_location_name=location,price=price,
        address=address,pincode=pincode,
        maximum_number_of_spots=max_spots
    )
    db.session.add(new_parking_lot)
    db.session.commit()
    flash('New Parking Lot Added')

    for x in range(max_spots):
        new_parking_spot = ParkingSpot(lot_id=new_parking_lot.id,status='A')
        db.session.add(new_parking_spot)
    db.session.commit()
    
    flash('Parking Spots Added')
    return redirect('/adminpage')

@app.route('/admin_delete_lot',methods=['POST', 'GET'])
def admin_delete_lot():
        if (session.get('username')!=admin_username):
            flash('Access Denied!')
            return redirect('/')
        
        lot_id = request.form.get('lot_id')
        lot=ParkingLot.query.get(lot_id)
        
        if not lot:
            flash('Parking Lot not found!')
            return redirect('/adminpage')
        else:
            occ_spots = ParkingSpot.query.filter_by(lot_id=lot_id, status='O').count()
            
            if occ_spots > 0:
                flash('Cannot delete this lot, there are occupied spots!')
                return redirect('/adminpage')
            else:
                ParkingSpot.query.filter_by(lot_id=lot.id).delete()
                db.session.delete(lot)
                db.session.commit()
                flash('Parking Lot Deleted Successfully')
        return redirect('/adminpage')

@app.route('/admin_edit_lot',methods=['GET','POST'])
def admin_edit_lot():
    if session.get('username')!=admin_username:
        flash('access denied')
        return redirect('/login')
    
    lot_id=request.form.get('lot_id')
    selected_lot=ParkingLot.query.get(lot_id)
    
    lots=ParkingLot.query.all()
    return render_template('adminpage.html',action='edit',lots=lots,selected_lot=selected_lot)

@app.route('/admin_update_lot',methods=['GET','POST'])
def admin_update_lot():
    if session.get('username')!=admin_username:
        flash('access denied')
        return redirect('/login')
    lot_id=request.form.get('lot_id')
    lot=ParkingLot.query.get(lot_id)
    
    if not lot:
        flash('No parking lot found')
        return redirect('/login')
    
    
    new_max_spots = int(request.form.get('maximum_number_of_spots'))
    curr_max_spots=lot.maximum_number_of_spots
    occ_spots = lot.spots.filter_by(status='O').count()
    aval_spots = lot.spots.filter_by(status='A').count()
    if new_max_spots < occ_spots:
        flash('Cannot reduce total spots below occ spots')
        return redirect(url_for('admin',action='edit'))
    
    diff=new_max_spots - curr_max_spots
    if diff > 0 :
        for i in range(diff):
            new_spot=ParkingSpot(lot_id=lot.id,status='A')
            db.session.add(new_spot)
    elif diff<0:
        newdiff=-1*diff
        rem_spots=lot.spots.filter_by(status='A').limit(newdiff).all()
        if new_max_spots < occ_spots:
            flash(f"Cannot reduce total spots below occupied spots ({occ_spots}).")
            return redirect(url_for('admin', action='edit'))
        for spot in rem_spots:
            if spot.reservations:  
                flash(f"Cannot delete spot {spot.id}, it has reservation")
                return redirect(url_for('admin', action='edit'))
            db.session.delete(spot)
    
    
    lot.prime_location_name = request.form.get('prime_location_name')
    lot.price = request.form.get('price')
    lot.address = request.form.get('address')
    lot.pincode = request.form.get('pincode')
    lot.maximum_number_of_spots=new_max_spots
    
    db.session.commit()
    flash('Update Success !')
    
    return redirect(url_for('admin',action='edit'))
    
@app.route('/admin_view_lot')
def admin_view_lot():
    if session.get('username')!=admin_username:
        flash('access denied')
        return redirect('/login')
    
    lots=ParkingLot.query.all()
    lot_info=[]
    
    for lot in lots:
        total_spots=lot.maximum_number_of_spots
        avail_spots=lot.spots.filter_by(status='A').count()
        occ_spots=lot.spots.filter_by(status='O').count()
        
        lot_info.append({'id':lot.id,'prime_location_name':lot.prime_location_name,'address':lot.address,
                         'price':lot.price,'maximum_number_of_spots':total_spots,'available_spots':avail_spots,
                         'occ_spots':occ_spots,'pincode':lot.pincode
                         })
    
    return render_template('adminpage.html',action='view',lot_info=lot_info)
    
@app.route('/admin_view_users')
def admin_view_users():
    if session.get('username')!=admin_username:
        flash('access denied')
        return redirect('/login')
    users=User.query.filter(User.username != admin_username).all()
    return render_template('adminpage.html',users=users,action='viewusers')

@app.route('/admin_view_spots')
def admin_view_spots():
    if session.get('username')!=admin_username:
        flash('access denied')
        return redirect('/login')
    
    occ_spots=ParkingSpot.query.filter_by(status='O').all()
    return render_template('adminpage.html',action='parkingstatus',spots=occ_spots)
    
@app.route('/admin_pie_chart')
def admin_pie_chart():
    if session.get('username')!=admin_username:
        flash('access denied')
        return redirect('/login')
    
    data=db.session.query(ParkingLot.prime_location_name,func.count(Reservation.id)).select_from(ParkingLot).join(ParkingSpot,ParkingSpot.lot_id == ParkingLot.id).join(Reservation,Reservation.spot_id  == ParkingSpot.id).group_by(ParkingLot.prime_location_name).all()
    
    labels=[]
    values=[]
    for m,n in data:
        labels.append(m)
        values.append(n)
    return render_template('admincharts.html',labels=labels,values=values)
       
@app.route('/userpage')
def userpage():
    if 'username' not in session or session['username'] == admin_username:
        flash('Access  Denied!')
        return redirect('/login')
    
    action=request.args.get('action','')
    user=User.query.filter_by(username=session.get('username')).first()
    
    if action == 'reserve':
        return render_template('userpage.html',action=action,parking_lots=ParkingLot.query.all())
    if action == 'release' :
        active_reserv=Reservation.query.filter_by(user_id=user.id,leaving_timestamp=None).all()
        return render_template('userpage.html',action=action,active_reserv=active_reserv)
    if action == 'summary':
        all_reservs = Reservation.query.filter_by(user_id=user.id).order_by(Reservation.leaving_timestamp.desc()).all()
        return render_template('userpage.html', action=action, all_reservs=all_reservs)
    
    return render_template('userpage.html',action=action)



@app.route('/reserve_spot',methods=['GET','POST'])
def reserve_spot():
    if 'username' not in session or session['username'] == admin_username:
        flash('Access  Denied!')
        return redirect('/login')
    
    user=User.query.filter_by(username=session.get('username')).first()
    lot_id = request.form.get('lot_id')
    
    avail_spot=ParkingSpot.query.filter_by(lot_id=lot_id,status='A').first()
    
    if not avail_spot:
        flash('No available spots in the Parking lot, Select another')
        return redirect(url_for('userpage',action='reserve'))
    
    avail_spot.status='O'
    lot = ParkingLot.query.get(lot_id)
    reserv=Reservation(user_id=user.id,spot_id=avail_spot.id,cost_per_unit_time=lot.price)
    db.session.add(reserv)
    db.session.commit()
    
    flash(f'Parking Spot #{avail_spot.id} reserved successfully!')
    return render_template('userpage.html')

@app.route('/release_spot',methods=['GET','POST'])
def release_spot():
    if 'username' not in session or session['username'] == admin_username:
        flash('Access  Denied!')
        return redirect('/login')
    
    user=User.query.filter_by(username=session.get('username')).first()
    
    if request.method == 'POST':
        reserv_id=request.form.get('reserv_id')
        reserv = Reservation.query.get(reserv_id)
        
        if not reserv or reserv.user_id!=user.id:
            flash('No Reservation Found')
            return redirect(url_for('userpage',action='release'))
        reserv.leaving_timestamp=datetime.now(timezone.utc)
        reserv.spot.status='A'
        
        park_timstamp= reserv.parking_timestamp.replace(tzinfo=timezone.utc)
        total_time=(reserv.leaving_timestamp-park_timstamp).total_seconds()/3600
        total_cost=(reserv.cost_per_unit_time)*(total_time)
        
        db.session.commit()
        flash(f'Spot {reserv.spot.id} is released at {reserv.leaving_timestamp}, Time is {total_time:.2f} hrs , Cost is Rs.{total_cost:.2f}')
        return redirect(url_for('userpage',action='release'))
    
    active_reserv=Reservation.query.filter_by(user_id=user.id,leaving_timestamp=None).all()
    return render_template('userpage.html', action='release', active_reserv=active_reserv)


@app.route('/user_pie_chart')
def user_pie_chart():
    if 'username' not in session or session['username'] == admin_username:
        flash('Access  Denied!')
        return redirect('/login')
    
    user=User.query.filter_by(username=session.get('username')).first()
    
    pie_data=db.session.query(ParkingLot.prime_location_name,
                              func.count(Reservation.id)
                                ).select_from(Reservation
                                ).join(ParkingSpot, Reservation.spot_id == ParkingSpot.id
                                ).join(ParkingLot, ParkingSpot.lot_id == ParkingLot.id
                                ).filter(Reservation.user_id == user.id
                                ).group_by(ParkingLot.prime_location_name).all()
    labels=[]
    values=[]
    
    for name,count in pie_data:
        labels.append(name)
        values.append(count)
    return render_template('usercharts.html',labels=labels,values=values)
    
@app.route('/register',methods=['GET','POST'])
def register():
    if request.method == 'POST':
        uname=request.form['username']
        email=request.form['email']
        pwd=request.form['password']
        
        if not uname or not email or not pwd:
            flash('All fields are required!')
            return render_template('register.html')
        
        exist_user = User.query.filter_by(username=uname).first()
        
        if exist_user:
            flash('Username already exists! Try again please.')
            return render_template('register.html')
        
        new_user = User(username=uname,email=email,password=pwd)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration Done !!')
        return redirect('/login')
    return render_template('register.html')
        
    
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST' :
        uname= request.form['username']
        pwd= request.form['password']
        
        user=User.query.filter_by(username=uname,password=pwd).first()
        
        if user :
            session['username']=uname
            if( uname == admin_username):
                return redirect('/adminpage')
            else:
                return redirect('/userpage')
        else:
            flash('Invalid username or password')
        
    return render_template('login.html')   

@app.route('/logout')
def logout():
    session.pop('username',None)
    flash('You have logged out')
    return redirect('/login')
from database.db_init import init_db

with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(debug=True)
     