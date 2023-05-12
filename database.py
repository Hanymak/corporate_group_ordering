import os
from sqlalchemy import create_engine, text, update, bindparam
from datetime import datetime, timezone
from pytz import timezone

db_connection_string = os.environ['DB_CONNECTION_STRING']

engine = create_engine(db_connection_string,
                       connect_args={"ssl": {
                         "ssl_ca": "/etc/ssl/cert.pem"
                       }})


def add_transfered_balance_to_user_db(transaction):
  # getting the current time in UTC timezone
  now_utc = datetime.now(timezone('UTC'))

  # Converting to Asia/Kolkata time zone
  now_cairo = now_utc.astimezone(timezone('Africa/Cairo'))
  datetime_string = now_cairo.strftime("%d/%m/%Y %I:%M:%S")
  #insert into DB for transactions table
  with engine.connect() as conn:

    query = text(
      "INSERT INTO transactions (transaction_from_user,transaction_to_user,transaction_amount,transaction_reason,transaction_date) VALUES (:transaction_from_user,:transaction_to_user,:transaction_amount,:transaction_reason,:transaction_date)"
    )

    conn.execute(
      query,
      dict(transaction_from_user=transaction['from_user'],
           transaction_to_user=transaction['to_user'],
           transaction_amount=transaction['transfer_amount'],
           transaction_reason=transaction['transfer_reason'],
           transaction_date=datetime_string))
    quer_user_dediction = text(
      "UPDATE users SET user_balance=user_balance-:transaction_amount WHERE user_name = :transaction_from_user"
    )
    conn.execute(
      quer_user_dediction,
      dict(transaction_amount=transaction['transfer_amount'],
           transaction_from_user=transaction['from_user']))
    quer_user_addition = text(
      "UPDATE users SET user_balance=user_balance+:transaction_amount WHERE user_name = :transaction_to_user"
    )
    conn.execute(
      quer_user_addition,
      dict(transaction_amount=transaction['transfer_amount'],
           transaction_to_user=transaction['to_user']))


def balance_recharge_to_user_db(transaction):
  # getting the current time in UTC timezone
  now_utc = datetime.now(timezone('UTC'))

  # Converting to Asia/Kolkata time zone
  now_cairo = now_utc.astimezone(timezone('Africa/Cairo'))
  datetime_string = now_cairo.strftime("%d/%m/%Y %I:%M:%S")
  #insert into DB for transactions table
  with engine.connect() as conn:
    query = text(
      "INSERT INTO transactions (transaction_from_user,transaction_to_user,transaction_amount,transaction_reason,transaction_date) VALUES (:transaction_from_user,:transaction_to_user,:transaction_amount,:transaction_reason,:transaction_date)"
    )

    conn.execute(
      query,
      dict(transaction_from_user="-",
           transaction_to_user=transaction['to_user'],
           transaction_amount=transaction['transfer_amount'],
           transaction_reason="Balance Recharge",
           transaction_date=datetime_string))
    quer_user_addition = text(
      "UPDATE users SET user_balance=user_balance+:transaction_amount WHERE user_name = :transaction_to_user"
    )
    conn.execute(
      quer_user_addition,
      dict(transaction_amount=transaction['transfer_amount'],
           transaction_to_user=transaction['to_user']))
