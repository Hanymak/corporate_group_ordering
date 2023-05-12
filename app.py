from flask import Flask, render_template, jsonify, request, redirect
from database import engine, add_transfered_balance_to_user_db, balance_recharge_to_user_db
from sqlalchemy import text

app = Flask(__name__)


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


@app.route("/")
def html_redirect():
  orders_from_db = load_orders_from_db()
  users_from_db = load_users_from_db()
  sheet_balance = sum(sub['user_balance'] for sub in users_from_db)
  return render_template('home.html',
                         orders=orders_from_db,
                         sheet_balance=sheet_balance,
                         users=users_from_db)


#this function populates the transaction history
@app.route("/transaction_history")
def transaction_history():
  transactions_from_db = load_transactions_from_db()
  transactions_from_db_descending = sorted(
    transactions_from_db,
    key=lambda item: item['transaction_id'],
    reverse=True)
  return render_template('transaction_history.html',
                         transactions=transactions_from_db_descending)


@app.route("/money_transfer", methods=['post'])
def transfer_money():
  data = request.form
  add_transfered_balance_to_user_db(data)

  return redirect("/")


@app.route("/balance_recharge", methods=['post'])
def balance_recharge():
  data = request.form
  balance_recharge_to_user_db(data)

  return redirect("/")

  # return render_template('home.html', orders=orders_from_db,
  #                                     sheet_balance=sheet_balance,
  #                                     users=users_from_db)


@app.route("/api/orders")
def list_jobs():
  return jsonify(ORDERS)


if __name__ == "__main__":
  app.run(host='0.0.0.0', debug=True)
