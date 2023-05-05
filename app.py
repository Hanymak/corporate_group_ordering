from flask import Flask, render_template

app = Flask(__name__)

ORDERS = [{
  'restaurant_logo': 'pic',
  'order_number': '1',
  'restaurant_name': 'Dahan',
  'order_date': '18-10-2022',
  'order_owner': 'Hany',
  'order_status': 'Paid'
}, {
  'restaurant_logo': 'pic2',
  'order_number': '2',
  'restaurant_name': 'Dahan2',
  'order_date': '18-08-2022',
  'order_owner': 'Amr',
  'order_status': 'Paid'
}, {
  'restaurant_logo': 'pic',
  'order_number': '3',
  'restaurant_name': 'Dahan3',
  'order_date': '18-05-2022',
  'order_owner': 'Eslam',
  'order_status': 'Paid'
}]


@app.route("/")
def html_redirect():
  return render_template('home.html', orders=ORDERS)


if __name__ == "__main__":
  app.run(host='0.0.0.0', debug=True)
