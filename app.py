import os
from flask import Flask, flash, render_template, jsonify, request, redirect, url_for, session
from database import engine, add_transfered_balance_to_user_db, balance_recharge_to_user_db
from sqlalchemy import create_engine, text, distinct
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
  'connect_args': {
    'ssl': {
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


class UserRole(Enum):
  User = "user"
  Admin = "admin"


class Object:

  def toJSON(self):
    return json.dumps(self,
                      default=lambda o: o.__dict__,
                      sort_keys=True,
                      indent=4)


class UserStatus(Enum):
  Active = "Active"
  Inactive = "Inactive"


class User(db.Model, UserMixin):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(20), nullable=False, unique=True)
  phone = db.Column(db.String(20), nullable=False)
  email = db.Column(db.String(50), nullable=False, unique=True)
  password = db.Column(db.String(80), nullable=False)
  balance = db.Column(db.Numeric(10, 2), nullable=False, default=0)
  volt_balance = db.Column(db.Numeric(10, 2), default=0)
  admin = db.Column(db.Boolean, default=False)
  active = db.Column(db.Boolean, default=True)


class Transaction(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  from_user = db.Column(db.String(20))
  from_user_balance_before = db.Column(db.Numeric(10, 2))
  from_user_balance_after = db.Column(db.Numeric(10, 2))
  to_user = db.Column(db.String(20))
  to_user_balance_before = db.Column(db.Numeric(10, 2))
  to_user_balance_after = db.Column(db.Numeric(10, 2))
  amount = db.Column(db.Numeric(10, 2), nullable=False)
  reason = db.Column(db.String(200), nullable=False)
  performed_by = db.Column(db.String(20), nullable=False)
  date = db.Column(db.String(200), nullable=False)


# Restaurant class
class Restaurant(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(100), nullable=False)
  address = db.Column(db.String(200), nullable=False)
  contact_info = db.Column(db.String(100), nullable=False)
  icon = db.Column(db.BLOB, nullable=True)


# Menu class
class MenuItem(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  restaurant_id = db.Column(db.Integer, nullable=False)
  name = db.Column(db.String(100), nullable=False)
  description = db.Column(db.String(200), nullable=False)
  price = db.Column(db.Float, nullable=False)


# Orders class (order is a reserved word)
class Orders(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  restaurant_id = db.Column(db.Integer, nullable=False)
  order_within_time = db.Column(db.String(20), nullable=False)
  status = db.Column(db.String(20), nullable=False)
  charge = db.Column(db.Numeric(10, 2), nullable=False, default=0)
  taxes = db.Column(db.Numeric(10, 2), nullable=False, default=1)
  service = db.Column(db.Numeric(10, 2), nullable=False, default=1)
  delivery = db.Column(db.Numeric(10, 2), nullable=False, default=0)
  total_charge = db.Column(db.Numeric(10, 2), nullable=False, default=0)
  owner = db.Column(db.String(20), nullable=False)
  date = db.Column(db.String(200), nullable=False)


# OrderItem class
class OrderItem(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  order_id = db.Column(db.Integer, nullable=False)
  menuitem_id = db.Column(db.Integer, nullable=False)
  user_id = db.Column(db.Integer, nullable=False)
  quantity = db.Column(db.Numeric(10, 2), nullable=False)


with app.app_context():

  db.create_all()


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


def load_all_restaurants():
  return Restaurant.query.all()


def load_all_menuitems():
  return MenuItem.query.all()


def load_all_orderitems():
  return OrderItem.query.all()


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

@app.route("/order_history", methods=['GET', 'POST'])
@login_required
def orders_history():
  order_restaurant_name = []
  orders_from_db = load_orders_from_db()
  restaurant_from_db = load_all_restaurants()
  users_from_db = load_all_users()
  sheet_balance = sum(sub.balance for sub in users_from_db)
  orders_restaurant_id = [order["restaurant_id"] for order in orders_from_db]
  for order_restaurant_id in orders_restaurant_id:
    order_restaurant_name.append(
      Restaurant.query.filter_by(id=order_restaurant_id).first())
  # print(order_restaurant_name)
  # print(orders_from_db)
  zipped_data = zip(orders_from_db, order_restaurant_name)
  return render_template('order_history.html',
                         orders=orders_from_db,
                         currentUser=current_user,
                         restaurants=restaurant_from_db,
                         zipped_data=zipped_data)

@app.route("/home", methods=['GET', 'POST'])
@login_required
def home():
  order_restaurant_name = []
  orders_from_db = load_orders_from_db()
  restaurant_from_db = load_all_restaurants()
  users_from_db = load_all_users()
  sheet_balance = sum(sub.balance for sub in users_from_db)
  orders_restaurant_id = [order["restaurant_id"] for order in orders_from_db]
  for order_restaurant_id in orders_restaurant_id:
    order_restaurant_name.append(
      Restaurant.query.filter_by(id=order_restaurant_id).first())
  # print(order_restaurant_name)
  # print(orders_from_db)
  zipped_data = zip(orders_from_db, order_restaurant_name)
  return render_template('home.html',
                         orders=orders_from_db,
                         sheet_balance=sheet_balance,
                         users=users_from_db,
                         currentUser=current_user,
                         restaurants=restaurant_from_db,
                         zipped_data=zipped_data)


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
                         currentUser=current_user)


#this function populates the Users Details
@app.route("/users_details")
@login_required
def users_details():
  users = load_all_users()
  # transactions_from_db_descending = sorted(
  #   transactions_from_db,
  #   key=lambda item: item['transaction_id'],
  #   reverse=True)
  return render_template('users_details.html', users=users)


@app.route("/create_order", methods=['get', 'post'])
@login_required
def create_order():
  data = request.form
  # Converting to Egypt time zone

  now_utc = datetime.now(timezone('UTC'))
  now_cairo = now_utc.astimezone(timezone('Africa/Cairo'))
  datetime_string = now_cairo.strftime("%d/%m/%Y %I:%M:%S")
  restaurant = Restaurant.query.filter_by(name=data['restaurant_name']).first()
  new_order = Orders(restaurant_id=restaurant.id,
                     order_within_time=data['time_to_order'],
                     status='Open',
                     charge=0,
                     taxes=1,
                     service=1,
                     delivery=0,
                     total_charge=0,
                     owner=current_user.name,
                     date=datetime_string)

  db.session.add(new_order)
  db.session.commit()
  return redirect("order_sheet", new_order.id)


@app.route("/order_sheet/<id>", methods=['GET', 'POST'])
@login_required
def order_sheet(id):

  # orderitems = load_all_orderitems()
  cid = id
  users = load_all_users()
  orderitems = OrderItem.query.filter_by(order_id=id).all()
  order = Orders.query.filter_by(id=id).first()
  restaurant_id = order.restaurant_id
  menuitems_restaurant = MenuItem.query.filter_by(
    restaurant_id=restaurant_id).all()
  order_restaurant = Restaurant.query.filter_by(id=restaurant_id).first()
  order_owner = order.owner
  order_status = order.status
  delivery_cost = order.delivery

  # print(menuitems)
  # print(orderitems.user_id)
  users_inorder = []
  menuitems_inorder = []
  menu_items_quantity = []
  user_item_cost = []
  users_items_cost = []
  for user_inorder in orderitems:
    user = User.query.filter_by(id=user_inorder.user_id).first()
    if user not in users_inorder:
      users_inorder.append(user)
  for user in users_inorder:
    user_items = OrderItem.query.filter_by(user_id=user.id, order_id=id)
    for user_item in user_items:
      user_item_cost.append(
        MenuItem.query.filter_by(id=user_item.menuitem_id).first())

    users_items_cost.append(
      sum(sub.price * float(user_item.quantity)
          for sub, user_item in zip(user_item_cost, user_items)))
    user_item_cost = []
  
  if(order_status == 'Paid'):
    order_cost = sum(users_items_cost) +  float(order.delivery)
  else:
    order_cost = sum(users_items_cost)
  for menuitem_inorder in orderitems:
    menuitems = MenuItem.query.filter_by(
      id=menuitem_inorder.menuitem_id).first()
    if menuitems not in menuitems_inorder:
      menuitems_inorder.append(menuitems)
  for menu_item_quantity in menuitems_inorder:
    item_quantity = OrderItem.query.filter_by(
      menuitem_id=menu_item_quantity.id, order_id=id).all()
    menu_items_quantity.append(
      sum(float(sub.quantity) for sub in item_quantity))
  # print(menu_items_quantity)

  menuitems_uniqueorders = menuitems_inorder
  orderitems_uniqueusers = users_inorder
  # for users in orderitems_uniqueusers:
  #   user = User.query.filter_by(id=orderitems_uniqueorders[0]).all()
  #   print(user)
  # exists = db.session.query(User.id).filter_by(name='davidism').first() is not None
  if request.method == "POST":
    action = request.form.get("action")
    if action == "addOrder":

      data = request.form
      menuitem = MenuItem.query.filter_by(description=data['menuitem']).first()

      orderitems = OrderItem.query.filter_by(order_id=id)
      user_exists_inorder = orderitems.filter_by(user_id=current_user.id)
      if (user_exists_inorder):
        order_already_exists_inorder = orderitems.filter_by(
          user_id=current_user.id, menuitem_id=menuitem.id).first()
        if (order_already_exists_inorder):
          if float(data['quantity']) == 0:
            # print('hello word not delete')
            db.session.delete(order_already_exists_inorder)
          else:
            order_already_exists_inorder.quantity = float(data['quantity'])
          db.session.commit()

        else:
          if (float(data['quantity']) == 0):
            flash("Item does not already exist")
          else:
            new_orderitem = OrderItem(order_id=id,
                                      menuitem_id=menuitem.id,
                                      user_id=current_user.id,
                                      quantity=data['quantity'])
            db.session.add(new_orderitem)
            db.session.commit()
        # if (data['menuitem'] == orderitems[])
      return redirect(url_for('order_sheet', id=id))
    elif action == "updateItemPrice":
      data = request.form
      order = Orders.query.filter_by(id=id).first()
      menuitem = MenuItem.query.filter_by(
        description=data['menuitem'],
        restaurant_id=order.restaurant_id).first()
      menuitem.price = float(data['item_new_price'])
      db.session.commit()
      return redirect(url_for('order_sheet', id=id))
    elif action == "addMenuItem":
      data = request.form
      order = Orders.query.filter_by(id=id).first()
      restaurant = Restaurant.query.filter_by(id=order.restaurant_id).first()
      new_menuitem = MenuItem(restaurant_id=order.restaurant_id,
                              name=restaurant.name,
                              description=data['itemName'],
                              price=data['itemPrice'])
      db.session.add(new_menuitem)
      db.session.commit()
      return redirect(url_for('order_sheet', id=id))
    elif action == "payOrder":
      data = request.form
      order = Orders.query.filter_by(id=id).first()
      order.status = "Paid"
      order.delivery = float(data['delivery_fees'])
      order.total_charge = order_cost + float(data['delivery_fees'])
      delivery_per_user="{:.2f}".format(float(data['delivery_fees'])/len(users_inorder))
      for user, cost in zip(users_inorder, users_items_cost):
        user.balance = float(user.balance) - float(cost) - float(delivery_per_user)
        print(delivery_per_user)
      user_vault_paid = User.query.filter_by(name=data['user_name']).first()
      user_vault_paid.volt_balance = float(
        user_vault_paid.volt_balance) - float(order_cost) - float(data['delivery_fees'])
      db.session.commit()
      return redirect(url_for('order_sheet', id=id))
    elif action == "closeOrder":
      order = Orders.query.filter_by(id=id).first()
      order.status = "Closed"
      db.session.commit()
      return redirect(url_for('order_sheet', id=id))
    elif action == "orderArrived":
      order = Orders.query.filter_by(id=id).first()
      order.status = "Arrived"
      db.session.commit()
      return redirect(url_for('order_sheet', id=id))
    elif action == "cancelOrder":
      order = Orders.query.filter_by(id=id).first()
      order.status = "Canceled"
      db.session.commit()
      return redirect(url_for('order_sheet', id=id))
    elif action == "addCollegeOrder":

      data = request.form
      college = User.query.filter_by(name=data['user']).first()
      menuitem = MenuItem.query.filter_by(description=data['menuitem']).first()
      orderitems = OrderItem.query.filter_by(order_id=id)
      user_exists_inorder = orderitems.filter_by(user_id=college.id)
      if (user_exists_inorder):
        order_already_exists_inorder = orderitems.filter_by(
          user_id=college.id, menuitem_id=menuitem.id).first()
        if (order_already_exists_inorder):
          if float(data['quantity']) == 0:
            # print('hello word not delete')
            db.session.delete(order_already_exists_inorder)
          else:
            order_already_exists_inorder.quantity = float(data['quantity'])
          db.session.commit()

        else:
          if (float(data['quantity']) == 0):
            flash("Item does not already exist")
          else:
            new_orderitem = OrderItem(order_id=id,
                                      menuitem_id=menuitem.id,
                                      user_id=college.id,
                                      quantity=data['quantity'])
            db.session.add(new_orderitem)
            db.session.commit()
        # if (data['menuitem'] == orderitems[])
      return redirect(url_for('order_sheet', id=id))

  zipped_data = zip(orderitems_uniqueusers, users_items_cost)
  zipped_data1 = zip(menuitems_uniqueorders, menu_items_quantity)

  users = load_all_users()
  return render_template('order_sheet.html',
                         menuitems_uniqueorders=menuitems_uniqueorders,
                         orderitems_uniqueusers=orderitems_uniqueusers,
                         orderitems=orderitems,
                         menuitems=menuitems_restaurant,
                         menu_items_quantity=menu_items_quantity,
                         users_items_cost=users_items_cost,
                         zipped_data=zipped_data,
                         zipped_data1=zipped_data1,
                         order_cost=order_cost,
                         users=users,
                         order_status=order_status,
                         order_owner=order_owner,
                         order_restaurant=order_restaurant,
                         delivery_cost=delivery_cost,
                         id=id)


@app.route("/money_transfer", methods=['get', 'post'])
@login_required
def transfer_money():

  now_utc = datetime.now(timezone('UTC'))

  # Converting to Egypt time zone
  now_cairo = now_utc.astimezone(timezone('Africa/Cairo'))
  datetime_string = now_cairo.strftime("%d/%m/%Y %I:%M:%S")

  data = request.form
  # add_transfered_balance_to_user_db(data)
  # print(data)
  user_from = User.query.filter_by(name=data['from_user']).first()

  user_to = User.query.filter_by(name=data['to_user']).first()

  new_transaction = Transaction(
    from_user=user_from.name,
    from_user_balance_before=user_from.balance,
    from_user_balance_after=float(user_from.balance) -
    float(data['transfer_amount']),
    to_user=user_to.name,
    to_user_balance_before=user_to.balance,
    to_user_balance_after=float(user_to.balance) +
    float(data['transfer_amount']),
    amount=float(data['transfer_amount']),
    reason=data['transfer_reason'],
    performed_by=current_user.name,
    date=datetime_string)

  user_from.balance = float(user_from.balance) - float(data['transfer_amount'])

  user_to.balance = float(user_to.balance) + float(data['transfer_amount'])

  if (current_user.email != user_to.email
      and current_user.email != user_from.email):
    msg = Message(
      "TE-Foodies Transaction",
      sender='noreply@tsfoodies',
      recipients=[user_from.email, user_to.email, current_user.email])
  else:
    msg = Message("TE-Foodies Transaction",
                  sender='noreply@tsfoodies',
                  recipients=[user_from.email, user_to.email])
  msg.body = "Dears,\n\nKindly be noted that the following transaction was performed on your account:\n\nFrom User : " + user_from.name + "\n\nTo User : " + user_to.name + "\n\nTransaction Amount : " + data[
    'transfer_amount'] + "\n\nPerfomed By : " + current_user.name + "\n\nRegards,\nTE-Foodies"
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

  user_to = User.query.filter_by(name=request.form['to_user'].upper()).first()
  new_transaction = Transaction(to_user=user_to.name,
                                to_user_balance_before=user_to.balance,
                                to_user_balance_after=float(user_to.balance) +
                                float(request.form['transfer_amount']),
                                amount=float(request.form['transfer_amount']),
                                reason=request.form['transfer_reason'],
                                performed_by=current_user.name,
                                date=datetime_string)

  user_to.balance = float(user_to.balance) + float(
    request.form['transfer_amount'])

  if (current_user.email != user_to.email):
    msg = Message("TE-Foodies Transaction",
                  sender='noreply@tsfoodies',
                  recipients=[user_to.email, current_user.email])
  else:
    msg = Message("TE-Foodies Transaction",
                  sender='noreply@tsfoodies',
                  recipients=[user_to.email])

  msg.body = "Dears,\n\nKindly be noted that the following transaction was performed on your account:\n\nTo User : " + user_to.name + "\n\nTransaction Amount : " + data[
    'transfer_amount'] + "\n\nPerfomed By : " + current_user.name + "\n\nTransfer Reason : " + data[
      'transfer_reason'] + "\n\nRegards,\nTE-Foodies"
  mail.send(msg)
  db.session.add(new_transaction)

  db.session.commit()

  return redirect("home")


@app.route("/", methods=['GET', 'POST'])
def login():
  # users_from_db = load_all_users()

  if request.method == "POST":

    user = User.query.filter_by(email=request.form['email'].upper()).first()
    if user:
      if bcrypt.check_password_hash(user.password, request.form['password']):
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

    useremail = User.query.filter_by(
      email=request.form['email'].upper()).first()
    username = User.query.filter_by(name=request.form['name'].upper()).first()
    if not username:
      if not useremail:
        if request.form['password'] == request.form['confirmpassword']:
          hashed_password = bcrypt.generate_password_hash(
            request.form['password'])

          # new_user = User(user_name=request.form['name'],
          #                 user_phone=request.form['phonenumber'],
          #                 user_email=request.form['email'],
          #                 user_password=hashed_password,
          #                 user_balance=0,
          #                 user_admin = False,
          #                 user_active = True )

          user_data = {
            'name': request.form['name'],
            'phone': request.form['phonenumber'],
            'email': request.form['email'],
            'password': hashed_password.decode("utf-8")
          }
          # user_auth = json.dumps(dict(new_user))
          # json_string = new_user.toJSON()
          token = s.dumps(dict(user_data), salt='email-confirm')

          msg = Message("TE-Foodies Mail Verification",
                        sender='noreply@tsfoodies',
                        recipients=[request.form['email']])

          link = url_for('verify_email', token=token, _external=True)
          msg.body = "Dear " + request.form[
            'name'] + ",\n\nKindly click the link below to verify your account.\n\n" + link + "\n\nRegards,\nTE-Foodies"
          mail.send(msg)

          # session['data'] = new_user

          return redirect(url_for('registration_complete'))
          # return redirect(f'/verify_email/{token}')
        else:
          flash("Passwords Don't Match")
      else:
        flash("User Email is already used")
    else:
      flash("User Name is already used")
  return render_template('registration.html')


@app.route("/verify_email/<token>", methods=['GET', 'POST'])
def verify_email(token):
  try:
    token_user = s.loads(token, salt='email-confirm', max_age=3600)

    # print(bytes(token_user['user_password'], 'utf-8'))
    new_user = User(name=token_user['name'],
                    phone=token_user['phone'],
                    email=token_user['email'],
                    password=bytes(token_user['password'], 'utf-8'),
                    balance=0,
                    admin=False,
                    active=True)
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

    user = User.query.filter_by(email=request.form['email'].upper()).first()

    # Check if the email exists in the user database
    if user:

      # Generate a password reset token
      token = s.dumps(request.form['email'], salt='change-password')

      # Send the password reset email with the token
      msg = Message("TE-Foodies Mail Verification",
                    sender='noreply@tsfoodies',
                    recipients=[request.form['email']])

      link = url_for('reset_password', token=token, _external=True)
      msg.body = "Dear " + user.name + ",\n\nKindly click the link below to reset your password.\n\n" + link + "\n\nRegards,\nTE-Foodies"
      mail.send(msg)

    # Always display a success message to prevent email enumeration attacks
    flash("Check Your Email")
    return redirect(url_for('forgot_password'))

  return render_template('forgot_password.html')


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
  try:
    # Verify and load the user from the token
    useremail = s.loads(token, salt='change-password', max_age=3600)

    if request.method == 'POST':
      # Get the new password from the form
      new_password = request.form['new_password']
      confirm_password = request.form['confirm_password']
      if (new_password == confirm_password):
        # Update the user's password
        hashed_password = bcrypt.generate_password_hash(new_password)
        user = User.query.filter_by(email=useremail).first()
        user.password = hashed_password
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
