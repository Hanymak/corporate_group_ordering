from flask import Flask, render_template, jsonify, request, redirect, url_for
from database import engine, add_transfered_balance_to_user_db, balance_recharge_to_user_db
from sqlalchemy import text
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt

app = Flask(__name__)
# create the extension
# db = SQLAlchemy()
# configure the SQLite database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'thisisasecretkey'
# initialize the app with the extension
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
  return User.query.get(int(user_id))


class User(db.Model, UserMixin):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(20), nullable=False, unique=True)
  password = db.Column(db.String(80), nullable=False)


class RegisterForm(FlaskForm):
  username = StringField(validators=[InputRequired(),
                                     Length(min=4, max=20)],
                         render_kw={"placeholder": "Username"})

  password = PasswordField(validators=[InputRequired(),
                                       Length(min=8, max=20)],
                           render_kw={"placeholder": "Password"})

  submit = SubmitField('Register')

  def validate_username(self, username):
    existing_user_username = User.query.filter_by(
      username=username.data).first()
    if existing_user_username:
      raise ValidationError(
        'That username already exists. Please choose a different one.')


class LoginForm(FlaskForm):
  username = StringField(validators=[InputRequired(),
                                     Length(min=4, max=20)],
                         render_kw={"placeholder": "Username"})

  password = PasswordField(validators=[InputRequired(),
                                       Length(min=8, max=20)],
                           render_kw={"placeholder": "Password"})

  submit = SubmitField('Login')


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


def load_users_from_db():
  with engine.connect() as conn:
    result = conn.execution_options(stream_results=True).execute(
      text("select * from users"))
    result_all = result.all()
    column_names = result.keys()
    users = []
    for idx, r in enumerate(result_all):
      users.append(dict(zip(column_names, r)))
  return users


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
  users_from_db = load_users_from_db()
  sheet_balance = sum(sub['user_balance'] for sub in users_from_db)
  return render_template('home.html',
                         orders=orders_from_db,
                         sheet_balance=sheet_balance,
                         users=users_from_db)


#this function populates the transaction history
@app.route("/transaction_history")
@login_required
def transaction_history():
  transactions_from_db = load_transactions_from_db()
  transactions_from_db_descending = sorted(
    transactions_from_db,
    key=lambda item: item['transaction_id'],
    reverse=True)
  return render_template('transaction_history.html',
                         transactions=transactions_from_db_descending)


@app.route("/money_transfer", methods=['post'])
@login_required
def transfer_money():
  data = request.form
  add_transfered_balance_to_user_db(data)

  return redirect("home")


@app.route("/balance_recharge", methods=['post'])
@login_required
def balance_recharge():
  data = request.form
  balance_recharge_to_user_db(data)

  return redirect("/home")

  # return render_template('home.html', orders=orders_from_db,
  #                                     sheet_balance=sheet_balance,
  #                                     users=users_from_db)


@app.route("/api/orders")
def list_jobs():
  return jsonify(ORDERS)


@app.route("/", methods=['GET', 'POST'])
def login():
  form = LoginForm()
  if form.validate_on_submit():
    user = User.query.filter_by(username=form.username.data).first()
    if user:
      if bcrypt.check_password_hash(user.password, form.password.data):
        # flash('You have been automatically logged out')
        login_user(user)
        return redirect(url_for('home'))

  return render_template('login.html', form=form)


@app.route("/logout", methods=['GET', 'POST'])
@login_required
def logout():

  logout_user()
  return redirect(url_for('login'))


@app.route("/registration", methods=['GET', 'POST'])
def registration():
  form = RegisterForm()
  if form.validate_on_submit():
    hashed_password = bcrypt.generate_password_hash(form.password.data)
    new_user = User(username=form.username.data, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('login'))
  return render_template('registration.html', form=form)


if __name__ == "__main__":
  app.run(host='0.0.0.0', debug=True)
