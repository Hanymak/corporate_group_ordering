from flask import Flask, render_template, jsonify
from database import engine
from sqlalchemy import text

app = Flask(__name__)



def load_orders_from_db():
  with engine.connect() as conn:
    result = conn.execution_options(stream_results=True).execute(text("select * from orders"))
    result_all = result.all()
    column_names = result.keys() 
    orders = []
    for idx, r in enumerate(result_all):
      orders.append(dict(zip(column_names, r)))
  

  return orders

def load_users_from_db():
  with engine.connect() as conn:
    result = conn.execution_options(stream_results=True).execute(text("select * from users"))
    result_all = result.all()
    column_names = result.keys() 
    users = []
    for idx, r in enumerate(result_all):
      users.append(dict(zip(column_names, r)))
  return users

@app.route("/")
def html_redirect():
  orders_from_db=load_orders_from_db()
  users_from_db=load_users_from_db()
  sheet_balance=sum(sub['user_balance'] for sub in users_from_db)
  return render_template('home.html', orders=orders_from_db,
                                      sheet_balance=sheet_balance,
                                      users=users_from_db)


@app.route("/api/orders")
def list_jobs():
  return jsonify(ORDERS)


if __name__ == "__main__":
  app.run(host='0.0.0.0', debug=True)
