import os
from flask import Flask, flash, render_template, jsonify, request, redirect, url_for,session
from database import  engine,add_transfered_balance_to_user_db, balance_recharge_to_user_db
from sqlalchemy import create_engine,text
# from sqlalchemy.orm import Session,sessionmaker
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
from enum import Enum
from decimal import Decimal
from datetime import datetime, timezone
from pytz import timezone
from flask_mail import Mail, Message
from itsdangerous.url_safe import URLSafeTimedSerializer
from itsdangerous import BadSignature, SignatureExpired
import json



# from sqlalchemy.ext.declarative import declarative_base
# Base = declarative_base()

db_connection_string = os.environ['DB_CONNECTION_STRING']
app = Flask(__name__)

#mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'tsfoodies23@gmail.com'
app.config['MAIL_PASSWORD'] = 'wqyixcortpipnaal'
# os.environ['EMAIL_PASSWORD']
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)


# create the extension
# db = SQLAlchemy()
# configure the SQLite database, relative to the app instance folder
app.config['SQLALCHEMY_DATABASE_URI'] = db_connection_string
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
      'connect_args': {'ssl': {
              'ssl_ca': '/etc/ssl/cert.pem'
          }
      }
  }
app.config['SECRET_KEY'] = 'helloall'
# initialize the app with the extension
db = SQLAlchemy(app)

s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
# Session that is used to perform sql requests to the engine -> here MariaDB


bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
  return User.query.get(int(user_id))

class Object:
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

class UserRole(Enum):
    User = "user"
    Admin = "admin"
  
class Object:
  def toJSON(self):
    return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

class UserStatus(Enum):
    Active = "Active"
    Inactive = "Inactive"
  
class User(db.Model, UserMixin):
  id = db.Column(db.Integer, primary_key=True)
  user_name = db.Column(db.String(20), nullable=False, unique=True)
  user_phone = db.Column(db.String(20), nullable=False)
  user_email = db.Column(db.String(50), nullable=False, unique=True)
  user_password = db.Column(db.String(80), nullable=False)
  user_balance = db.Column(db.Numeric(10,2), nullable=False , default= 0)
  user_volt_balance = db.Column(db.Numeric(10,2), default= 0)
  user_admin = db.Column(db.Boolean, default=False)
  user_active = db.Column(db.Boolean, default=True)
  
class Transaction(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  transaction_from_user = db.Column(db.String(20))
  transaction_from_user_balance_before = db.Column(db.Numeric(10,2))
  transaction_from_user_balance_after = db.Column(db.Numeric(10,2))
  transaction_to_user = db.Column(db.String(20))
  transaction_to_user_balance_before = db.Column(db.Numeric(10,2))
  transaction_to_user_balance_after = db.Column(db.Numeric(10,2))
  transaction_amount = db.Column(db.Numeric(10,2), nullable=False)
  transaction_reason = db.Column(db.String(200), nullable=False)
  transaction_performed_by = db.Column(db.String(20), nullable=False)
  transaction_date = db.Column(db.String(200), nullable=False)

with app.app_context():

  db.create_all()


# # SqlAlchemy :: Session setup
# Session = sessionmaker(bind=engine)

# Create all tables that do not already exist
# Base.metadata.create_all(engine)
# session = Session()
# session.commit()
def load_orders_from_db():
  with engine.connect() as conn:
    result = conn.execution_options(stream_results=True).execute(
      text("select * from orders"))
    result_all = result.all()
    column_names = result.keys()
    orders = []
    for idx, r in enumerate(result_all):
      orders.append(dict(zip(column_names, r)))

  return orders




def load_all_users():
    return User.query.all()
def load_all_transcations():
    return Transaction.query.all()
def load_transactions_from_db():
  with engine.connect() as conn:
    result = conn.execution_options(stream_results=True).execute(
      text("select * from transactions"))
    result_all = result.all()
    column_names = result.keys()
    transactions = []
    for idx, r in enumerate(result_all):
      transactions.append(dict(zip(column_names, r)))
  return transactions


@app.route("/home", methods=['GET', 'POST'])
@login_required
def home():
  orders_from_db = load_orders_from_db()
  users_from_db = load_all_users()
  sheet_balance = sum(sub.user_balance for sub in users_from_db)
  return render_template('home.html',
                         orders=orders_from_db,
                         sheet_balance=sheet_balance,
                         users=users_from_db,
                         currentUser = current_user)


#this function populates the transaction history
@app.route("/transaction_history")
@login_required
def transaction_history():
  transactions_from_db = load_all_transcations()
  # transactions_from_db_descending = sorted(
  #   transactions_from_db,
  #   key=lambda item: item['transaction_id'],
  #   reverse=True)
  return render_template('transaction_history.html',
                         transactions=transactions_from_db,
                         currentUser = current_user)


@app.route("/money_transfer", methods=['get','post'])
@login_required
def transfer_money():
  now_utc = datetime.now(timezone('UTC'))

  # Converting to Asia/Kolkata time zone
  now_cairo = now_utc.astimezone(timezone('Africa/Cairo'))
  datetime_string = now_cairo.strftime("%d/%m/%Y %I:%M:%S")

  data = request.form
  # add_transfered_balance_to_user_db(data)
  print(data)
  user_from = User.query.filter_by(user_name=data['from_user']).first()

  user_to = User.query.filter_by(user_name=data['to_user']).first()



  new_transaction = Transaction(transaction_from_user=user_from.user_name,
  transaction_from_user_balance_before=user_from.user_balance,
  transaction_from_user_balance_after=float(user_from.user_balance) - float(data['transfer_amount']),
  transaction_to_user=user_to.user_name,
  transaction_to_user_balance_before=user_to.user_balance,
  transaction_to_user_balance_after=float(user_to.user_balance) + float(data['transfer_amount']) ,
  transaction_amount=float(data['transfer_amount']),
  transaction_reason=data['transfer_reason'],
  transaction_performed_by=current_user.user_name,
  transaction_date=datetime_string)

  
  user_from.user_balance = float(user_from.user_balance) - float(data['transfer_amount'])


  user_to.user_balance = float(user_to.user_balance) + float(data['transfer_amount'])
  
  if(current_user.user_email != user_to.user_email and current_user.user_email != user_from.user_email ):
    msg = Message("TE-Foodies Transaction", sender='noreply@tsfoodies', recipients = [user_from.user_email,user_to.user_email,current_user.user_email])
  else:
    msg = Message("TE-Foodies Transaction", sender='noreply@tsfoodies', recipients = [user_from.user_email,user_to.user_email])
  msg.body = "Dears,\n\nKindly be noted that the following transaction was performed on your account:\n\nFrom User : "+ user_from.user_name + "\n\nTo User : "+ user_to.user_name + "\n\nTransaction Amount : " + data['transfer_amount'] + "\n\nPerfomed By : "+current_user.user_name+ "\n\nRegards,\nTE-Foodies"
  mail.send(msg)
  db.session.add(new_transaction)
  
  db.session.commit()




  return redirect("home")


@app.route("/balance_recharge", methods=['post'])
@login_required
def balance_recharge():
  now_utc = datetime.now(timezone('UTC'))

  # Converting to Asia/Kolkata time zone
  now_cairo = now_utc.astimezone(timezone('Africa/Cairo'))
  datetime_string = now_cairo.strftime("%d/%m/%Y %I:%M:%S")

  data = request.form
  
  user_to = User.query.filter_by(user_name=request.form['to_user'].upper()).first()
  new_transaction = Transaction(           transaction_to_user=user_to.user_name,
  transaction_to_user_balance_before=user_to.user_balance,
  transaction_to_user_balance_after=float(user_to.user_balance) + float(request.form['transfer_amount']) ,
  transaction_amount=float(request.form['transfer_amount']),
  transaction_reason=request.form['transfer_reason'],
  transaction_performed_by=current_user.user_name,
  transaction_date=datetime_string)
  
  
  user_to.user_balance = float(user_to.user_balance) + float(request.form['transfer_amount'])


  
  if(current_user.user_email != user_to.user_email ):
    msg = Message("TE-Foodies Transaction", sender='noreply@tsfoodies', recipients = [user_to.user_email,current_user.user_email])
  else:
    msg = Message("TE-Foodies Transaction", sender='noreply@tsfoodies', recipients = [user_to.user_email])
  
  msg.body = "Dears,\n\nKindly be noted that the following transaction was performed on your account:\n\nTo User : "+ user_to.user_name + "\n\nTransaction Amount : " + data['transfer_amount'] + "\n\nPerfomed By : "+current_user.user_name+ "\n\nTransfer Reason : " + data['transfer_reason'] + "\n\nRegards,\nTE-Foodies"
  mail.send(msg)
  db.session.add(new_transaction)
  
  db.session.commit()

  return redirect("home")



@app.route("/api/orders")
def list_jobs():
  return jsonify(ORDERS)


@app.route("/", methods=['GET', 'POST'])
def login():
  # users_from_db = load_all_users()

  if request.method == "POST":
    
    user = User.query.filter_by(user_email=request.form['email'].upper()).first()
    if user:
      if bcrypt.check_password_hash(user.user_password, request.form['password']):
        login_user(user)
        return redirect(url_for('home'))
      else:
        flash("Incorrect User Name Or Password")
    else:
      flash("Incorrect User Name Or Password")
      # else:
      #   db.session['user_id'] = user.id  # makes more sense than storing just a bool
  return render_template('login_main.html')


@app.route("/logout", methods=['GET', 'POST'])
@login_required
def logout():

  logout_user()
  return redirect(url_for('login'))


@app.route("/registration", methods=['GET', 'POST'])
def registration():
  # form = RegisterForm()
  if request.method == "POST":

    useremail = User.query.filter_by(user_email=request.form['email'].upper()).first()
    username = User.query.filter_by(user_name=request.form['name'].upper()).first()
    if not username:
      if not useremail:
        if request.form['password'] == request.form['confirmpassword']:
          hashed_password = bcrypt.generate_password_hash(request.form['password'])

          # new_user = User(user_name=request.form['name'],
          #                 user_phone=request.form['phonenumber'],
          #                 user_email=request.form['email'],
          #                 user_password=hashed_password,
          #                 user_balance=0,
          #                 user_admin = False,
          #                 user_active = True )

          user_data = {'user_name': request.form['name'],
                      'user_phone': request.form['phonenumber'],
                      'user_email': request.form['email'],
                      'user_password': hashed_password.decode("utf-8") }
          # user_auth = json.dumps(dict(new_user))
          # json_string = new_user.toJSON()
          token = s.dumps(dict(user_data), salt='email-confirm')
          
          msg = Message("TE-Foodies Mail Verification", sender='noreply@tsfoodies', recipients = [request.form['email']])

          link = url_for('verify_email', token=token, _external = True)
          msg.body = "Dear "+ request.form['name'] + ",\n\nKindly click the link below to verify your account.\n\n" + link + "\n\nRegards,\nTE-Foodies"
          mail.send(msg)
          
          # session['data'] = new_user
          
          return redirect(url_for('registration_complete'))
          # return redirect(f'/verify_email/{token}')
        else :
          flash("Passwords Don't Match")
      else:
        flash("User Email is already used")
    else:
      flash("User Name is already used")
  return render_template('registration.html')


@app.route("/verify_email/<token>", methods=['GET', 'POST'])
def verify_email(token):
  try:
    token_user = s.loads(token,  salt = 'email-confirm', max_age=3600)


    # print(bytes(token_user['user_password'], 'utf-8'))
    new_user = User(user_name=token_user['user_name'],
                user_phone=token_user['user_phone'],
                user_email=token_user['user_email'],
                user_password=bytes(token_user['user_password'], 'utf-8'), 
                user_balance=0,
                user_admin = False,
                user_active = True )
    print("\n\n\n\nToken Valid\n\n\n\n\n")
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('login'))
  except SignatureExpired:
    # print("Token has Expired")
    return "Token has Expired"
  except BadSignature:
    # print("Token is Invalid")
    return "Token is Invalid"
    
  
  
  # return render_template('confirm_email.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
      # Check if the email exists in the user database

      user = User.query.filter_by(user_email=request.form['email'].upper()).first()

      # Check if the email exists in the user database
      if user:

          # Generate a password reset token
          token = s.dumps(request.form['email'], salt='change-password')

          # Send the password reset email with the token
          msg = Message("TE-Foodies Mail Verification", sender='noreply@tsfoodies', recipients = [request.form['email']])

          link = url_for('reset_password', token=token, _external = True)
          msg.body = "Dear "+ user.user_name + ",\n\nKindly click the link below to reset your password.\n\n" + link + "\n\nRegards,\nTE-Foodies"
          mail.send(msg)

      # Always display a success message to prevent email enumeration attacks
      flash("Check Your Email")
      return redirect(url_for('forgot_password'))

    return render_template('forgot_password.html')


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        # Verify and load the user from the token
        useremail = s.loads(token,  salt = 'change-password', max_age=3600)

        if request.method == 'POST':
            # Get the new password from the form
            new_password = request.form['new_password']
            confirm_password = request.form['confirm_password']
            if(new_password == confirm_password):
            # Update the user's password
              hashed_password = bcrypt.generate_password_hash(new_password)
              user = User.query.filter_by(user_email=useremail).first()
              user.user_password = hashed_password
            # Provide feedback to the user that the password has been reset
              # print(user.user_name)
              db.session.commit()
            return redirect(url_for('login'))

        # Display the password reset form
        return render_template('reset_password.html')

    except SignatureExpired:
        return 'Reset Password Expired'
    except BadSignature:
        return 'Reset Password Invalid'


@app.route('/registration_complete')
def registration_complete():
  return render_template('registration_complete.html')




if __name__ == "__main__":
  app.run(host='0.0.0.0', debug=True)
