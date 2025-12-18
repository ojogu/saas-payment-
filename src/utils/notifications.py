import os
from twilio.rest import Client
from flask import current_app


# Find your Account SID and Auth Token at twilio.com/console
# and set the environment variables. See http://twil.io/secure
account_sid = current_app.config['Twilio_key']
auth_token = current_app.config['Twilio_token']
client = Client(account_sid, auth_token)

message = client.messages.create(
  from_='+14849464235',
  body='How are you doing today',
  to='+2348104647669'
)
print(message.sid)