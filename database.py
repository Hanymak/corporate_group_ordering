import os
from sqlalchemy import create_engine,text

db_connection_string = os.environ['DB_CONNECTION_STRING']

engine = create_engine(
  db_connection_string,
  connect_args={
      "ssl": {
          "ssl_ca": "/etc/ssl/cert.pem"
      }
  }
  
)

# def Convert(lst):
#     print("order_len",len(lst))
#     res_dct = {lst[i]: lst[i + 1] for i in range(0, len(lst), 2)}
#     return res_dct
# with engine.connect() as conn:
#   result = conn.execution_options(stream_results=True).execute(text("select * from orders"))
#   result_all = result.all()
#   column_names = result.keys() 
#   orders = []
#   for idx, r in enumerate(result_all):
#     orders.append(dict(zip(column_names, r)))
  
# print(orders)


