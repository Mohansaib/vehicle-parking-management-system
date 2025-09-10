from models import User,db
import os
def init_db():
    db.create_all()
    admin_username = os.getenv('admin_username')
    admin_email = os.getenv('admin_email')
    admin_password = os.getenv('admin_password')

    already_admin = User.query.filter_by(username=admin_username).first()
    
    if not already_admin:
        admin=User(username=admin_username,email=admin_email,password=admin_password)
        db.session.add(admin)
        db.session.commit()
        