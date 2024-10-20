import os
from flask import Flask, flash, render_template, jsonify, request, redirect, url_for, session
# from database import engine, add_transfered_balance_to_user_db, balance_recharge_to_user_db
from sqlalchemy import create_engine, text, distinct, MetaData
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
import threading
import telebot
import sys
import time
from time import sleep
import re
import random
import string

# from flask_caching import Cache

#telegram API
# Define your bot token
# bot = telebot.TeleBot(os.environ['API_KEY'])
import telebot

import logging

app = Flask(__name__)
# app.config['CACHE_TYPE'] = 'simple'
# app.config['CACHE_DEFAULT_TIMEOUT'] = 300

# cache = Cache(app)

# bot.set_webhook(url='https://corporategroupordering-1--hanymak.repl.co/api')

#   print(bot.get_webhook_info())
# with app.app_context():

#   data = {
#     'url':
#     'https://api.render.com/deploy/srv-chanvhvdvk4lphpafoa0?key=kOD17K-MDEs',
#     'has_custom_certificate': False,
#     'pending_update_count': 0,
#     'ip_address': '216.24.57.6',
#     'last_error_date': None,
#     'last_error_message': None,
#     'last_synchronization_error_date': None,
#     'max_connections': 40,
#     'allowed_updates': ['message', 'callback_query']
#   }
#   json_data = json.dumps(data)
#   print(json_data)
# bot.set_webhook(url='https://tefoodies.fun/api')

# BOT_TOKEN = os.environ['API_KEY']
# BOT_INTERVAL = 3
# BOT_TIMEOUT = 30

# bot = None

# def bot_polling():
#   global bot
#   print("Starting bot polling now")
#   while True:
#     try:
#       print("New bot instance started")
#       bot = telebot.TeleBot(BOT_TOKEN)  #Generate new bot instance
#       botactions(
#       )  #If bot is used as a global variable, remove bot as an input param
#       bot.polling(none_stop=True, interval=BOT_INTERVAL, timeout=BOT_TIMEOUT)
#     except Exception as ex:  #Error in polling
#       print("Bot polling failed, restarting in {}sec. Error:\n{}".format(
#         BOT_TIMEOUT, ex))
#       bot.stop_polling()
#       sleep(BOT_TIMEOUT)
#     else:  #Clean exit
#       bot.stop_polling()
#       print("Bot polling loop finished")
#       break  #End loop

# def botactions():
#   #Set all your bot handlers inside this function
#   #If bot is used as a global variable, remove bot as an input param
#   @bot.message_handler(commands=["start"])
#   def command_start(message):
#     bot.reply_to(message, "Hi there!")

# polling_thread = threading.Thread(target=bot_polling)
# polling_thread.daemon = True
# polling_thread.start()
Debug = os.environ['Debug']
if Debug:
  db_connection_string = os.environ['DB_CONNECTION_STRING_TEST_BRANCH']
else:
  db_connection_string = os.environ['DB_CONNECTION_STRING_MAIN_BRANCH']
db_connection_string = os.environ['DB_CONNECTION_STRING_MAIN_BRANCH']
#mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'tsfoodies23@gmail.com'
app.config['MAIL_PASSWORD'] = os.environ['MAIL_APP_PASSWORD']
# os.environ['EMAIL_PASSWORD']
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

# create the extension
# db = SQLAlchemy()
# configure the SQLite database, relative to the app instance folder
# if Debug:
#   # Configuration for the test database
#   app.config['SQLALCHEMY_DATABASE_URI_TEST'] = db_connection_string
#   app.config['TESTING'] = True  # Enable testing mode
#   app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF protection in tests

#   test_db = SQLAlchemy(app,
#                        session_options={'expire_on_commit': False
#                                         })  # Avoid session expiration in tests
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
  active = db.Column(db.Boolean, default=False)
  random_pattern = db.Column(db.String(20), nullable=True, unique=True)
  chat_id = db.Column(db.String(255), nullable=True, unique=True)


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


class Wallet_Transaction(db.Model):
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
  dining_room = db.Column(db.String(20), nullable=True)
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


# bot = telebot.TeleBot(os.environ['API_KEY'], threaded=False)

with app.app_context():

  db.create_all()

# def load_orders_from_db():
#   with engine.connect() as conn:
#     result = conn.execution_options(stream_results=True).execute(
#       text("select * from orders"))
#     result_all = result.all()
#     column_names = result.keys()
#     orders = []
#     for idx, r in enumerate(result_all):
#       orders.append(dict(zip(column_names, r)))


#   return orders
def load_orders_from_db():
  return Orders.query.all()


def load_all_users():
  return User.query.all()


def load_all_active_users():
  return User.query.filter_by(active=True).all()


def load_all_restaurants():
  return Restaurant.query.all()


def load_all_menuitems():
  return MenuItem.query.all()


def load_all_orderitems():
  return OrderItem.query.all()


def load_all_transcations():
  return Transaction.query.all()


def load_all_wallet_transcations():
  return Wallet_Transaction.query.all()


def generate_random_pattern(length):
  characters = string.ascii_letters + string.digits  # Letters (both cases) and numbers
  return ''.join(random.choice(characters) for _ in range(length))


MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 10

# print(generate_random_pattern(5))

# def load_transactions_from_db():
#   with engine.connect() as conn:
#     result = conn.execution_options(stream_results=True).execute(
#       text("select * from transactions"))
#     result_all = result.all()
#     column_names = result.keys()
#     transactions = []
#     for idx, r in enumerate(result_all):
#       transactions.append(dict(zip(column_names, r)))
#   return transactions
# def check_for_pattern(message):
#   print("not implemented yet")
#   pattern = r"Hello hany"  # Use the correct regular expression pattern
#   match = re.match(pattern, message.text, re.I)
#   if match:
#     return message.chat.id
#   else:
#     return None
bot = telebot.TeleBot(os.environ['API_KEY'], threaded=False)

with app.app_context():
  bot.remove_webhook()
  #webhook name must have www. in front of it

  bot.set_webhook(url="https://www.tefoodies.com/api",
                  allowed_updates=["message", "callback_query"])


# https://api.render.com/deploy/srv-chanvhvdvk4lphpafoa0?key=kOD17K-MDEs
@app.route("/api", methods=['POST'])
def webhook():
  try:
    print("hi")
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '', 200
  except json.JSONDecodeError as e:
    print(f"JSON decoding error: {e}")
    return 'Bad Request - Invalid JSON', 400


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):

  bot.send_message(message.chat.id,
                   "Welcome to tefoodies bot!\nPlease enter the token")


def send_telegram_bot_message(chat_id, message):
  try:
    with app.app_context():
      bot.send_message(chat_id, message)
    return True
  except Exception as e:
    print(f"An exception occurred: {e}")
    return None


def check_for_pattern(message):
  # print("hello Hany___________")
  print(message.chat.id)
  try:
    with app.app_context():
      user_match_random_pattern = User.query.filter_by(
        random_pattern=message.text).first()
    print(f"users: {user_match_random_pattern}")

  except Exception as e:
    print(f"An exception occurred: {e}")

  if user_match_random_pattern:
    # Your code block
    return user_match_random_pattern
  else:
    # Handle the case when users is None
    return None


def send_notification(user, msg):
  for _ in range(MAX_RETRIES):
    try:
      if user.chat_id is None:
        mail.send(msg)
      else:
        bot.send_message(user.chat_id, msg.body)
      break  # If successful, exit the loop
    except Exception as e:
      logging.warning(f"Notification sending failed: {e}")
      time.sleep(RETRY_DELAY_SECONDS)


@bot.message_handler(
  func=lambda message: check_for_pattern(message) is not None)
def handle_specific_text(message):
  user = check_for_pattern(message)

  if user:

    with app.app_context():
      try:
        curr_user = User.query.filter_by(id=user.id).first()
        curr_user.chat_id = message.chat.id

      except Exception as e:
        print(f"An exception occurred: {e}")
      else:
        db.session.commit()
        bot.send_message(message.chat.id,
                         "Hello " + user.name + ", Welcome to tefoodies bot")


@app.route("/order_history", methods=['GET', 'POST'])
@login_required
def orders_history():
  order_restaurant_name = []
  orders_from_db = load_orders_from_db()
  restaurant_from_db = load_all_restaurants()
  users_from_db = load_all_users()
  sheet_balance = sum(sub.balance for sub in users_from_db)
  orders_restaurant_id = [order.restaurant_id for order in orders_from_db]
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
# @cache.cached(timeout=600)  # Cache for 10 minutes
def home():
  order_restaurant_name = []
  orders_from_db = load_orders_from_db()
  open_orders = [order for order in orders_from_db if order.status == "Open"]
  # open_orders = Orders.query.filter_by(status="Open")
  restaurant_from_db = load_all_restaurants()
  users_from_db = load_all_users()
  active_users = load_all_active_users()
  admin_users = [user for user in active_users if user.admin]
  sheet_balance = sum(sub.balance for sub in users_from_db)
  admin_wallet_balance = current_user.volt_balance
  wallet_balance = sum(sub.volt_balance for sub in users_from_db)
  orders_restaurant_id = [order.restaurant_id for order in open_orders]
  for order_restaurant_id in orders_restaurant_id:
    order_restaurant_name.append(
      Restaurant.query.filter_by(id=order_restaurant_id).first())
  zipped_data = zip(open_orders, order_restaurant_name)
  # zipped_list = list(zipped_data)
  # length_zipped_data = len(zipped_list)
  return render_template('home.html',
                         orders=open_orders,
                         sheet_balance=sheet_balance,
                         users=users_from_db,
                         active_users=active_users,
                         currentUser=current_user,
                         restaurants=restaurant_from_db,
                         zipped_data=zipped_data,
                         admin_wallet_balance=admin_wallet_balance,
                         wallet_balance=wallet_balance,
                         admin_users=admin_users)


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


@app.route("/wallet_transaction_history")
@login_required
def wallet_transaction_history():
  wallet_transactions_from_db = load_all_wallet_transcations()
  # transactions_from_db_descending = sorted(
  #   transactions_from_db,
  #   key=lambda item: item['transaction_id'],
  #   reverse=True)
  return render_template('wallet_transaction_history.html',
                         wallet_transactions=wallet_transactions_from_db,
                         currentUser=current_user)


#this function notifies users through telegram notifications only
@app.route("/telegram_notifications")
@login_required
def telegram_notifications():
  users = load_all_users()
  # transactions_from_db_descending = sorted(
  #   transactions_from_db,
  #   key=lambda item: item['transaction_id'],
  #   reverse=True)
  return render_template('telegram_notifications.html',
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


@app.route("/admins_details")
@login_required
def admins_details():
  users = load_all_users()
  admins = [admin for admin in users if admin.admin == 1]
  # print(admins)
  # transactions_from_db_descending = sorted(
  #   transactions_from_db,
  #   key=lambda item: item['transaction_id'],
  #   reverse=True)
  return render_template('admins_details.html', users=admins)


@app.route("/create_order", methods=['GET', 'POST'])
@login_required
def create_order():
  order_restaurant_name = []
  orders_from_db = load_orders_from_db()
  active_users = load_all_active_users()
  open_orders = [order for order in orders_from_db if order.status == "Open"]
  # open_orders = Orders.query.filter_by(status="Open")
  restaurant_from_db = load_all_restaurants()
  users_from_db = load_all_users()
  admin_users = [user for user in active_users if user.admin]
  sheet_balance = sum(sub.balance for sub in users_from_db)
  admin_wallet_balance = current_user.volt_balance
  wallet_balance = sum(sub.volt_balance for sub in users_from_db)
  orders_restaurant_id = [order.restaurant_id for order in open_orders]
  for order_restaurant_id in orders_restaurant_id:
    order_restaurant_name.append(
      Restaurant.query.filter_by(id=order_restaurant_id).first())
  zipped_data = zip(open_orders, order_restaurant_name)
  data = request.form
  print(data)
  # Converting to Egypt time zone
  now_utc = datetime.now(timezone('UTC'))
  now_cairo = now_utc.astimezone(timezone('Africa/Cairo'))
  datetime_string = now_cairo.strftime("%d/%m/%Y %I:%M:%S")
  restaurant = Restaurant.query.filter_by(name=data['restaurant_name']).first()

  users = load_all_users()

  try:
    new_order = Orders(restaurant_id=restaurant.id,
                       order_within_time=data['time_to_order'],
                       status='Open',
                       charge=0,
                       taxes=1,
                       service=1,
                       delivery=0,
                       total_charge=0,
                       owner=current_user.name,
                       dining_room=data['dining_room'],
                       date=datetime_string)
    db.session.add(new_order)
    # db.session.commit()

  except Exception as e:
    # Handle any exceptions that might occur during database interaction
    print(f"An error occurred: {e}")
    db.session.rollback()  # Rollback the transaction in case of an error
    flash("An error occurred while creating the order")

    return render_template(
      'home.html',
      orders=open_orders,
      sheet_balance=sheet_balance,
      users=users_from_db,
      active_users=active_users,
      currentUser=current_user,
      restaurants=restaurant_from_db,
      zipped_data=zipped_data,
      admin_wallet_balance=admin_wallet_balance,
      wallet_balance=wallet_balance,
      admin_users=admin_users)  # Redirect to an error page or another route

  else:
    db.session.commit()
    for user in active_users:
      if user.id != current_user.id:
        msg = Message("TE-Foodies Orders",
                      sender='noreply@tsfoodies',
                      recipients=[user.email])

        msg.body = "Dears,\n\nKindly be noted that " + current_user.name + " Started a new order from " + restaurant.name + " and will order within " + data[
          'time_to_order'] + " mints" + "\n\n Place your order from: https://www.tefoodies.com/order_sheet/" + str(
            new_order.id) + "\n\nRegards,\nTE-Foodies"
        send_notification(user, msg)
    return redirect("/order_sheet/{}".format(new_order.id))


@app.route("/create_restaurant", methods=['GET', 'POST'])
@login_required
def create_restaurant():
  data = request.form
  restaurant_name = Restaurant.query.filter_by(
    name=data['restaurant_name'].upper()).first()
  if not restaurant_name:
    new_restaurant = Restaurant(name=data['restaurant_name'],
                                address=data['restaurant_address'],
                                contact_info=data['restaurant_phone'])
    db.session.add(new_restaurant)
    db.session.commit()
  else:
    flash("Restaurant exists")
  return redirect("home")


@app.route("/order_sheet/<id>", methods=['GET', 'POST'])
@login_required
def order_sheet(id):
  # orderitems = load_all_orderitems()
  cid = id
  users = load_all_users()
  active_users = load_all_active_users()
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

  if (order_status == 'Paid'):
    order_cost = sum(users_items_cost) + float(order.delivery)
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
  total_num_of_items = sum(menu_items_quantity)
  # print(menu_items_quantity)

  menuitems_uniqueorders = menuitems_inorder
  orderitems_uniqueusers = users_inorder
  # for users in orderitems_uniqueusers:
  #   user = User.query.filter_by(id=orderitems_uniqueorders[0]).all()
  #   print(user)
  # exists = db.session.query(User.id).filter_by(name='davidism').first() is not None

  if request.method == "POST":

    action = request.form.get("action")
    print(request.form)
    if action == "addOrder":
      # if (current_user.active == 1):
      if float(current_user.balance) > float(-50.0):
        try:
          data = request.form
          for key, value in data.items():
            # print(key, value)
            if key.startswith('menuitem_'):
              menuitem_index = key.replace('menuitem_', '')
              quantity_from_user = "{:.2f}".format(
                float(data.get(f'quantity_{menuitem_index}')))
              if value:
                menuitem = MenuItem.query.filter_by(
                  description=value, restaurant_id=restaurant_id).first()

                orderitems = OrderItem.query.filter_by(order_id=id)
                user_exists_inorder = orderitems.filter_by(
                  user_id=current_user.id)
                if (user_exists_inorder):
                  order_already_exists_inorder = orderitems.filter_by(
                    user_id=current_user.id, menuitem_id=menuitem.id).first()
                  if (order_already_exists_inorder):
                    if float(quantity_from_user) == 0:
                      # print('hello word not delete')
                      db.session.delete(order_already_exists_inorder)
                    else:
                      order_already_exists_inorder.quantity = float(
                        quantity_from_user)
                    # db.session.commit()

                  else:
                    if (float(quantity_from_user) == 0):
                      flash("Item does not already exist")
                    else:
                      new_orderitem = OrderItem(order_id=id,
                                                menuitem_id=menuitem.id,
                                                user_id=current_user.id,
                                                quantity=quantity_from_user)
                      # print(new_orderitem)
                      db.session.add(new_orderitem)
                      # db.session.commit()
        except Exception as e:
          # Handle any exceptions that might occur during database interaction
          print(f"An error occurred: {e}")
          db.session.rollback()  # Rollback the transaction in case of an error
          flash("An error occurred while adding the order item.")
        else:
          db.session.commit()
        # if (data['menuitem'] == orderitems[])
      else:
        flash("Your balance is insufficient to place your order")
      return redirect(url_for('order_sheet', id=id))
      # else:
      # flash("You are an inactive user")
      # return redirect(url_for('order_sheet', id=id))
    elif action == "updateItemPrice":
      try:
        data = request.form
        order = Orders.query.filter_by(id=id).first()
        menuitem = MenuItem.query.filter_by(
          description=data['menuitem'],
          restaurant_id=order.restaurant_id).first()
        menuitem.price = float(data['item_new_price'])
        # db.session.commit()
      except Exception as e:
        # Handle any exceptions that might occur during database interaction
        print(f"An error occurred: {e}")
        db.session.rollback()  # Rollback the transaction in case of an error
        flash("An error occurred while updating the menu item price.")
      else:
        db.session.commit()
      return redirect(url_for('order_sheet', id=id))
    elif action == "addMenuItem":
      try:
        data = request.form
        order = Orders.query.filter_by(id=id).first()
        restaurant = Restaurant.query.filter_by(id=order.restaurant_id).first()
        new_menuitem = MenuItem(restaurant_id=order.restaurant_id,
                                name=restaurant.name,
                                description=data['itemName'],
                                price=data['itemPrice'])
        db.session.add(new_menuitem)
        # db.session.commit()
      except Exception as e:
        # Handle any exceptions that might occur during database interaction
        print(f"An error occurred: {e}")
        db.session.rollback()  # Rollback the transaction in case of an error
        flash("An error occurred while adding a new menu item.")
      else:
        db.session.commit()
      return redirect(url_for('order_sheet', id=id))
    elif action == "payOrder":
      try:
        data = request.form
        order = Orders.query.filter_by(id=id).first()
        order.status = "Paid"
        order.delivery = float(data['delivery_fees'])
        order.total_charge = order_cost + float(data['delivery_fees'])

        delivery_per_user = "{:.2f}".format(
          float(data['delivery_fees']) / len(users_inorder))

        transactions = []
        for user, cost in zip(users_inorder, users_items_cost):
          user_balance_before = float(user.balance)
          user.balance = float(
            user.balance) - float(cost) - float(delivery_per_user)

          # Create Transaction object
          new_transaction = Transaction(
            from_user=user.name,
            from_user_balance_before=user_balance_before,
            from_user_balance_after=float(user.balance),
            amount=float(cost) + float(delivery_per_user),
            reason="Order from " + order_restaurant.name,
            performed_by=current_user.name,
            date=datetime.now(
              timezone('Africa/Cairo')).strftime("%d/%m/%Y %I:%M:%S"))
          transactions.append(new_transaction)

          # Notify users
          msg = Message("TE-Foodies Order Payment Transaction",
                        sender='noreply@tsfoodies',
                        recipients=[user.email])
          amount = -float(cost) - float(delivery_per_user)
          user_balance_before_2f = "{:.2f}".format(float(user_balance_before))
          user_balance_after_2f = "{:.2f}".format(float(user.balance))
          amount_2f = "{:.2f}".format(float(amount))
          msg.body = f"Dears,\n\nKindly be noted that the following transaction was performed on your account:\n\nFrom User : {user.name}\n\nTransaction Amount : {amount_2f}\n\nBalance Before/After : {user_balance_before_2f} / {user_balance_after_2f}\n\nPerfomed By : {current_user.name}\n\nTransfer Reason : Order from {order_restaurant.name}\n\nRegards,\nTE-Foodies"

          send_notification(user, msg)
        user_vault_paid = User.query.filter_by(name=data['user_name']).first()

        new_wallet_transaction = Wallet_Transaction(
          from_user=data['user_name'],
          from_user_balance_before=user_vault_paid.volt_balance,
          from_user_balance_after=float(user_vault_paid.volt_balance) -
          float(order_cost) - (float(delivery_per_user) * len(users_inorder)),
          amount=float(order_cost) +
          (float(delivery_per_user) * len(users_inorder)),
          reason="Order from " + order_restaurant.name,
          performed_by=current_user.name,
          date=datetime.now(
            timezone('Africa/Cairo')).strftime("%d/%m/%Y %I:%M:%S"))
        transactions.append(new_wallet_transaction)
        # Add all transactions to the session and commit
        db.session.add_all(transactions)

        # Update user vault balance
        user_vault_paid.volt_balance = float(
          user_vault_paid.volt_balance) - float(order_cost) - (
            float(delivery_per_user) * len(users_inorder))

      except Exception as e:
        print(f"An error occurred: {e}")
        db.session.rollback()
        flash("An error occurred while paying the order.")
      else:
        db.session.commit()

      return redirect(url_for('order_sheet', id=id))
    elif action == "closeOrder":
      try:
        if len(users_inorder) != 0:
          order = Orders.query.filter_by(id=id).first()
          order.status = "Closed"
          # db.session.commit()
        else:
          flash("You have not ordered anything yet.")
      except Exception as e:
        # Handle any exceptions that might occur during database interaction
        print(f"An error occurred: {e}")
        db.session.rollback()  # Rollback the transaction in case of an error
        flash("An error occurred while closing the order.")
      else:
        db.session.commit()
      return redirect(url_for('order_sheet', id=id))
    elif action == "orderArrived":
      try:
        order = Orders.query.filter_by(id=id).first()
        order.status = "Arrived"
        # x = 10 / 0 for testing except block
        for user in users_inorder:
          if user.id != current_user.id:
            msg = Message("TE-Foodies Order Arrived",
                          sender='noreply@tsfoodies',
                          recipients=[user.email])

            msg.body = "Dears,\n\nKindly be noted that your order from " + order_restaurant.name + " has arrived at " + order.dining_room + "\n\nRegards,\nTE-Foodies"
            send_notification(user, msg)
      except Exception as e:
        # Handle any exceptions that might occur during database interaction
        print(f"An error occurred: {e}")
        db.session.rollback()  # Rollback the transaction in case of an error
        flash("An error occurred while changing order status to Arrived.")
      else:
        db.session.commit()
      return redirect(url_for('order_sheet', id=id))
    elif action == "cancelOrder":
      try:
        order = Orders.query.filter_by(id=id).first()
        order.status = "Canceled"
        # db.session.commit()

        for user in users_inorder:
          if user.id != current_user.id:
            msg = Message("TE-Foodies Order Cancelled",
                          sender='noreply@tsfoodies',
                          recipients=[user.email])

            msg.body = "Dears,\n\nKindly be noted that your order from " + order_restaurant.name + " has been CANCELLED" "\n\nRegards,\nTE-Foodies"
            send_notification(user, msg)
      except Exception as e:
        # Handle any exceptions that might occur during database interaction
        print(f"An error occurred: {e}")
        db.session.rollback()  # Rollback the transaction in case of an error
        flash("An error occurred while changing order status to Canceled.")
      else:
        db.session.commit()

      return redirect(url_for('order_sheet', id=id))
    elif action == "addCollegeOrder":
      data = request.form
      print(data)
      if 'user' in data:
        college = User.query.filter_by(name=data['user']).first()
        if float(college.balance) > float(-50.0):
          try:
            for key, value in data.items():
              # print(key, value)
              if key.startswith('menuitem_'):
                menuitem_index = key.replace('menuitem_', '')
                quantity_from_user = "{:.2f}".format(
                  float(data.get(f'quantity_{menuitem_index}')))
                if value:
                  menuitem = MenuItem.query.filter_by(
                    description=value, restaurant_id=restaurant_id).first()

                  orderitems = OrderItem.query.filter_by(order_id=id)
                  user_exists_inorder = orderitems.filter_by(
                    user_id=college.id)
                  if (user_exists_inorder):
                    order_already_exists_inorder = orderitems.filter_by(
                      user_id=college.id, menuitem_id=menuitem.id).first()
                    if (order_already_exists_inorder):
                      if float(quantity_from_user) == 0:
                        # print('hello word not delete')
                        db.session.delete(order_already_exists_inorder)
                      else:
                        order_already_exists_inorder.quantity = float(
                          quantity_from_user)
                      # db.session.commit()

                    else:
                      if (float(quantity_from_user) == 0):
                        flash("Item does not already exist")
                      else:
                        new_orderitem = OrderItem(order_id=id,
                                                  menuitem_id=menuitem.id,
                                                  user_id=college.id,
                                                  quantity=quantity_from_user)
                        # print(new_orderitem)
                        db.session.add(new_orderitem)
                        # db.session.commit()

          except Exception as e:
            # Handle any exceptions that might occur during database interaction
            print(f"An error occurred: {e}")
            db.session.rollback(
            )  # Rollback the transaction in case of an error
            flash("An error occurred while adding your college order.")
          else:
            db.session.commit()
        else:
          flash("Your college's balance is insufficient to place his order")

      else:
        flash("This user does not exist in the database.")
      return redirect(url_for('order_sheet', id=id))

  zipped_data = zip(orderitems_uniqueusers, users_items_cost)
  zipped_data1 = zip(menuitems_uniqueorders, menu_items_quantity)

  users = load_all_users()
  active_users = load_all_active_users()
  return render_template('order_sheet.html',
                         menuitems_uniqueorders=menuitems_uniqueorders,
                         orderitems_uniqueusers=orderitems_uniqueusers,
                         orderitems=orderitems,
                         menuitems=menuitems_restaurant,
                         menu_items_quantity=menu_items_quantity,
                         users_items_cost=users_items_cost,
                         zipped_data=zipped_data,
                         zipped_data1=zipped_data1,
                         total_num_of_items=total_num_of_items,
                         order_cost=order_cost,
                         users=users,
                         active_users=active_users,
                         order_status=order_status,
                         order_owner=order_owner,
                         order_restaurant=order_restaurant,
                         delivery_cost=delivery_cost,
                         id=id)


@app.route("/transfer_wallet", methods=['get', 'post'])
@login_required
def transfer_wallet():

  now_utc = datetime.now(timezone('UTC'))

  # Converting to Egypt time zone
  now_cairo = now_utc.astimezone(timezone('Africa/Cairo'))
  datetime_string = now_cairo.strftime("%d/%m/%Y %I:%M:%S")
  try:
    data = request.form
    # add_transfered_balance_to_user_db(data)
    # print(data)
    user_from = User.query.filter_by(name=data['from_user']).first()

    user_to = User.query.filter_by(name=data['to_user']).first()

    new_transaction = Wallet_Transaction(
      from_user=user_from.name,
      from_user_balance_before=user_from.volt_balance,
      from_user_balance_after=float(user_from.volt_balance) -
      float(data['transfer_amount']),
      to_user=user_to.name,
      to_user_balance_before=user_to.volt_balance,
      to_user_balance_after=float(user_to.volt_balance) +
      float(data['transfer_amount']),
      amount=float(data['transfer_amount']),
      reason=data['transfer_reason'],
      performed_by=current_user.name,
      date=datetime_string)

    user_from.volt_balance = float(user_from.volt_balance) - float(
      data['transfer_amount'])

    user_to.volt_balance = float(user_to.volt_balance) + float(
      data['transfer_amount'])
    # user_list = [user_from, user_to]

    db.session.add(new_transaction)

    # db.session.commit()
    msg = Message("TE-Foodies Wallet Transaction",
                  sender='noreply@tsfoodies',
                  recipients=[user_from.email])
    msg.body = "Dears,\n\nKindly be noted that the following transaction was performed on your account:\n\nFrom User : " + user_from.name + "\n\nTo User : " + user_to.name + "\n\nTransaction Amount : " + data[
      'transfer_amount'] + "\n\nWallet Balance Before/After : " + "{:.2f}".format(
        float(float(user_from.volt_balance) + float(data['transfer_amount']))
      ) + " / " + "{:.2f}".format(
        float(user_from.volt_balance)
      ) + "\n\nPerfomed By : " + current_user.name + "\n\nRegards,\nTE-Foodies"
    if (user_from.chat_id == None):
      mail.send(msg)
    else:
      bot.send_message(user_from.chat_id, msg.body)

    msg = Message("TE-Foodies Wallet Transaction",
                  sender='noreply@tsfoodies',
                  recipients=[user_to.email])
    msg.body = "Dears,\n\nKindly be noted that the following transaction was performed on your account:\n\nFrom User : " + user_from.name + "\n\nTo User : " + user_to.name + "\n\nTransaction Amount : " + data[
      'transfer_amount'] + "\n\nWallet Balance Before/After : " + "{:.2f}".format(
        float(float(user_to.volt_balance) - float(data['transfer_amount']))
      ) + " / " + "{:.2f}".format(
        float(user_to.volt_balance)
      ) + "\n\nPerfomed By : " + current_user.name + "\n\nRegards,\nTE-Foodies"
    if (user_to.chat_id == None):
      mail.send(msg)
    else:
      bot.send_message(user_to.chat_id, msg.body)

  except Exception as e:
    # Handle any exceptions that might occur during database interaction
    print(f"An error occurred: {e}")
    db.session.rollback()  # Rollback the transaction in case of an error
    flash("An error occurred while transfering to others wallet.")
  else:
    db.session.commit()
    # flash("Transaction Successful!")
  return redirect("home")


@app.route("/money_transfer_from_all_users", methods=['get', 'post'])
@login_required
def money_transfer_from_all_users():
  now_utc = datetime.now(timezone('UTC'))

  # Converting to Egypt time zone
  now_cairo = now_utc.astimezone(timezone('Africa/Cairo'))
  datetime_string = now_cairo.strftime("%d/%m/%Y %I:%M:%S")
  transactions = []
  try:
    data = request.form
    user_to = User.query.filter_by(name=data['to_user']).first()
    site_fees = "{:.2f}".format(float(data['site_fees']))
    # Process the form data when from_user is not null
    #Get all users

    active_users = load_all_active_users()
    #count number of users
    number_of_active_users = len(active_users)
    #divide by the number of users
    transfer_amount = "{:.2f}".format(
      float(data['site_fees']) / number_of_active_users)
    #remove the user paid from the list
    users_from = [user for user in active_users if user.name != user_to.name]
    print(users_from)
    for user_from in users_from:
      new_transaction = Transaction(
        from_user=user_from.name,
        from_user_balance_before=user_from.balance,
        from_user_balance_after=float(user_from.balance) -
        float(transfer_amount),
        to_user=user_to.name,
        to_user_balance_before=user_to.balance,
        to_user_balance_after=float(user_to.balance) + float(transfer_amount),
        amount=float(transfer_amount),
        reason=data['transfer_reason'],
        performed_by=current_user.name,
        date=datetime_string)
      user_from.balance = float(user_from.balance) - float(transfer_amount)

      user_to.balance = float(user_to.balance) + float(transfer_amount)
      # user_list = [user_from, user_to]
      print(new_transaction)
      print(user_from.balance)
      print(user_to.balance)
      transactions.append(new_transaction)
      msg = Message("TE-Foodies Transaction",
                    sender='noreply@tsfoodies',
                    recipients=[user_from.email])
      msg.body = "Dears,\n\nKindly be noted that the following transaction was performed on your account:\n\nFrom User : " + user_from.name + "\n\nTo User : " + user_to.name + "\n\nTransaction Amount : " + transfer_amount + "\n\nBalance Before/After : " + "{:.2f}".format(
        float(float(user_from.balance) + float(transfer_amount))
      ) + " / " + "{:.2f}".format(
        float(user_from.balance)
      ) + "\n\nPerfomed By : " + current_user.name + "\n\nRegards,\nTE-Foodies"
      if (user_from.chat_id == None):
        mail.send(msg)
      else:
        bot.send_message(user_from.chat_id, msg.body)

      # else:
      #   # Handle the case when from_user is null or empty
      #   flash('Error: "from_user" cannot be null or empty', 'error')
      #   # Optionally, you can redirect the user to an error page or render the form again.
      # return redirect(url_for('your_form_route'))
      # print("HI")
    msg = Message("TE-Foodies Transaction",
                  sender='noreply@tsfoodies',
                  recipients=[user_to.email])
    msg.body = "Dears,\n\nKindly be noted that the following transaction was performed on your account From All Users \n\nTo User : " + user_to.name + "\n\nTransaction Amount : " + "{:.2f}".format(
      float(site_fees) - float(transfer_amount)
    ) + "\n\nBalance Before/After : " + "{:.2f}".format(
      float(
        float(user_to.balance) - float(site_fees) + float(transfer_amount))
    ) + " / " + "{:.2f}".format(
      float(user_to.balance)
    ) + "\n\nPerfomed By : " + current_user.name + "\n\nRegards,\nTE-Foodies"
    if (user_to.chat_id == None):
      mail.send(msg)
    else:
      bot.send_message(user_to.chat_id, msg.body)
    # db.session.commit()
    db.session.add_all(transactions)

  except Exception as e:
    # Handle any exceptions that might occur during database interaction
    print(f"An error occurred: {e}")
    db.session.rollback()  # Rollback the transaction in case of an error
    flash("An error occurred while transfering the money.")
  else:
    db.session.commit()

  return redirect("home")


@app.route("/money_transfer", methods=['get', 'post'])
@login_required
def transfer_money():

  now_utc = datetime.now(timezone('UTC'))

  # Converting to Egypt time zone
  now_cairo = now_utc.astimezone(timezone('Africa/Cairo'))
  datetime_string = now_cairo.strftime("%d/%m/%Y %I:%M:%S")
  transactions = []
  try:
    data = request.form
    user_to = User.query.filter_by(name=data['to_user']).first()
    for key, value in data.items():
      print(key, value)
      if key.startswith('from_user_'):
        from_user_count = key.replace('from_user_', '')
        transfer_amount = "{:.2f}".format(
          float(data.get(f'transfer_amount_{from_user_count}')))
        # print(from_user_count, transfer_amount)
        # Check if the value is not null or empty
        if value:
          # Process the form data when from_user is not null
          user_from = User.query.filter_by(name=value).first()
          new_transaction = Transaction(
            from_user=user_from.name,
            from_user_balance_before=user_from.balance,
            from_user_balance_after=float(user_from.balance) -
            float(transfer_amount),
            to_user=user_to.name,
            to_user_balance_before=user_to.balance,
            to_user_balance_after=float(user_to.balance) +
            float(transfer_amount),
            amount=float(transfer_amount),
            reason=data['transfer_reason'],
            performed_by=current_user.name,
            date=datetime_string)
          user_from.balance = "{:.2f}".format(
            float(user_from.balance) - float(transfer_amount))

          user_to.balance = "{:.2f}".format(
            float(user_to.balance) + float(transfer_amount))
          # user_list = [user_from, user_to]
          print(new_transaction)
          print(user_from.balance)
          print(user_to.balance)
          transactions.append(new_transaction)
          msg = Message("TE-Foodies Transaction",
                        sender='noreply@tsfoodies',
                        recipients=[user_from.email])
          msg.body = "Dears,\n\nKindly be noted that the following transaction was performed on your account:\n\nFrom User : " + user_from.name + "\n\nTo User : " + user_to.name + "\n\nTransaction Amount : " + transfer_amount + "\n\nBalance Before/After : " + "{:.2f}".format(
            float(float(user_from.balance) + float(transfer_amount))
          ) + " / " + "{:.2f}".format(
            float(user_from.balance)
          ) + "\n\nPerfomed By : " + current_user.name + "\n\nRegards,\nTE-Foodies"
          if (user_from.chat_id == None):
            mail.send(msg)
          else:
            bot.send_message(user_from.chat_id, msg.body)

          msg = Message("TE-Foodies Transaction",
                        sender='noreply@tsfoodies',
                        recipients=[user_to.email])
          msg.body = "Dears,\n\nKindly be noted that the following transaction was performed on your account:\n\nFrom User : " + user_from.name + "\n\nTo User : " + user_to.name + "\n\nTransaction Amount : " + transfer_amount + "\n\nBalance Before/After : " + "{:.2f}".format(
            float(float(user_to.balance) - float(transfer_amount))
          ) + " / " + "{:.2f}".format(
            float(user_to.balance)
          ) + "\n\nPerfomed By : " + current_user.name + "\n\nRegards,\nTE-Foodies"
          if (user_to.chat_id == None):
            mail.send(msg)
          else:
            bot.send_message(user_to.chat_id, msg.body)

        else:
          # Handle the case when from_user is null or empty
          flash('Error: "from_user" cannot be null or empty', 'error')
          # Optionally, you can redirect the user to an error page or render the form again.
          # return redirect(url_for('your_form_route'))
    # print("HI")
    db.session.add_all(transactions)

    # db.session.commit()

  except Exception as e:
    # Handle any exceptions that might occur during database interaction
    print(f"An error occurred: {e}")
    db.session.rollback()  # Rollback the transaction in case of an error
    flash("An error occurred while transfering the money.")
  else:
    db.session.commit()

  return redirect("home")


@app.route("/balance_recharge", methods=['post'])
@login_required
def balance_recharge():
  now_utc = datetime.now(timezone('UTC'))

  # Converting to Asia/Kolkata time zone
  now_cairo = now_utc.astimezone(timezone('Africa/Cairo'))
  datetime_string = now_cairo.strftime("%d/%m/%Y %I:%M:%S")
  try:
    data = request.form

    user_to = User.query.filter_by(
      name=request.form['to_user'].upper()).first()
    new_transaction = Wallet_Transaction(
      to_user=user_to.name,
      to_user_balance_before=user_to.balance,
      to_user_balance_after=float(user_to.balance) +
      float(request.form['transfer_amount']),
      amount=float(request.form['transfer_amount']),
      reason=request.form['transfer_reason'],
      performed_by=current_user.name,
      date=datetime_string)

    user_to.balance = float(user_to.balance) + float(
      request.form['transfer_amount'])
    current_user.volt_balance = float(current_user.volt_balance) + float(
      request.form['transfer_amount'])
    db.session.add(new_transaction)

    if (current_user.email != user_to.email):
      msg = Message("TE-Foodies Balance Transaction",
                    sender='noreply@tsfoodies',
                    recipients=[user_to.email, current_user.email])
    else:
      msg = Message("TE-Foodies Balance Recharge",
                    sender='noreply@tsfoodies',
                    recipients=[user_to.email])

    msg.body = "Dears,\n\nKindly be noted that the following transaction was performed on your account:\n\nTo User : " + user_to.name + "\n\nTransaction Amount : " + data[
      'transfer_amount'] + "\n\nBalance Before/After : " + "{:.2f}".format(
        float(float(user_to.balance) - float(data['transfer_amount']))
      ) + " / " + "{:.2f}".format(
        user_to.balance
      ) + "\n\nPerfomed By : " + current_user.name + "\n\nTransfer Reason : " + data[
        'transfer_reason'] + "\n\nRegards,\nTE-Foodies"
    # if any user does not have chat id send a mail and send telegram notification
    if (user_to.chat_id == None or current_user.chat_id == None):
      mail.send(msg)
    if (current_user.email != user_to.email):
      if (user_to.chat_id != None):
        bot.send_message(user_to.chat_id, msg.body)
      if (current_user.chat_id != None):
        bot.send_message(current_user.chat_id, msg.body)

    else:
      if (user_to.chat_id != None):
        bot.send_message(user_to.chat_id, msg.body)

  except Exception as e:
    # Handle any exceptions that might occur during database interaction
    print(f"An error occurred: {e}")
    db.session.rollback()  # Rollback the transaction in case of an error
    flash("An error occurred while recharging user the balance.")
  else:
    db.session.commit()
  return redirect("home")


@app.route("/", methods=['GET', 'POST'])
def login():
  # users_from_db = load_all_users()

  if request.method == "POST":

    user = User.query.filter_by(email=request.form['email'].upper()).first()
    if user:
      if bcrypt.check_password_hash(user.password, request.form['password']):
        if (user.active == 1):
          login_user(user)
          return redirect(url_for('home'))
        else:
          flash("Your account is not active. Please contact the admin.",
                'error')
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

    random_pattern = generate_random_pattern(5)
    random_pattern_exists = User.query.filter_by(
      random_pattern=random_pattern).first()

    while random_pattern_exists is not None:
      # If the random pattern already exists, generate a new one
      random_pattern = generate_random_pattern(5)
      random_pattern_exists = User.query.filter_by(
        random_pattern=random_pattern).first()
    # print(bytes(token_user['user_password'], 'utf-8'))
    new_user = User(name=token_user['name'],
                    phone=token_user['phone'],
                    email=token_user['email'],
                    password=bytes(token_user['password'], 'utf-8'),
                    balance=0,
                    admin=False,
                    active=True,
                    random_pattern=random_pattern)
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
  # telegram_main()

  app.run(host='0.0.0.0', debug=True)

  # while True:
  #   try:
  #     sleep(120)
  #   except KeyboardInterrupt:
  #     bot.stop_polling()
  #     print("Exiting...")
  #     sys.exit(0)
