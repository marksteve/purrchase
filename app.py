import os
import time

import const
import requests
from flask import (abort, Flask, json, jsonify, redirect, render_template,
                   request, url_for)
from redis import StrictRedis
from simpleflake import simpleflake

app = Flask(__name__)
app.config.from_pyfile('config.py')
db = StrictRedis(host=os.environ.get('REDIS_PORT_6379_TCP_ADDR'))

@app.route('/')
def index():
  return render_template('index.html')

@app.route('/demos/<demo>')
def demos(demo):
  return render_template('demos/{}.html'.format(demo))

# ==== /oauth ==== #
@app.route('/oauth')
def oauth():
  code = request.args['code']
  # Hackathon "merchant" sample details
  data = {
    'app_id': app.config['GLOBE_APP_ID'],
    'app_secret': app.config['GLOBE_APP_SECRET'],
    'code': code,
  }
  res = requests.post(const.G_AUTH_ENDPOINT, data=data)
  if res.ok:
    payload = res.json()
    db.hmset(payload['subscriber_number'], payload)
    return render_template('oauth.html', **payload)
  else:
    abort(500)
# ==== END /oauth ==== #

# ==== /charge ==== #
@app.route('/charge', methods=['POST'])
def charge():
  """
  Charge URI is the endpoint for charging and sending of sms
  This endpoint expects the ff params:
  - subscriber_number
  - amount
  """

  subscriber_number = request.json['subscriber_number']
  amount = request.json['amount']

  #: get the access token from DB
  access_token = db.hget(subscriber_number, 'access_token')
  if not access_token:
    return jsonify(
      needs_authorization=True,
      dialog_url=const.G_DIALOG.format(app.config['GLOBE_APP_ID']),
    )

  sender = app.config['GLOBE_SHORTCODE'][-4:] # this is weird!
  # Generate a random code for this user session
  confirm_code = str(simpleflake())[-6:]

  params = {'access_token': access_token}
  req = {
    'outboundSMSMessageRequest': {
      'clientCorrelator': str(simpleflake()),
      'senderAddress': 'tel:{}'.format(sender),
      'outboundSMSTextMessage': {
        'message': 'PHonePay\n\nYou will be charged PHP {}. This is your code to proceed: {}'.format(
          amount,
          confirm_code,
        ),
      },
      'address': ['tel:+63{}'.format(subscriber_number)],
    }
  }

  res = requests.post(
    const.G_SMS_ENDPOINT.format(sender),
    headers={
      'Content-Type': 'application/json',
    },
    params=params,
    data=json.dumps(req)
  )

  if not res.ok:
    abort(500)

  payload = res.json()
  payload.update(confirm_code_sent=True)

  # Save confirm code assoc
  db.setex(
    '{}:confirm:{}'.format(subscriber_number, confirm_code),
    15 * 60,  # 15 minutes
    amount,
  )

  return jsonify(**payload)
# ==== END /charge ==== #


# ==== /confirm ==== #
@app.route('/confirm', methods=['POST'])
def confirm():
  subscriber_number = request.json['subscriber_number']
  confirm_code = request.json['confirm_code']

  # Get confirm code assoc
  confirm_key = '{}:confirm:{}'.format(subscriber_number, confirm_code)
  amount = db.get(confirm_key)
  if not amount:
    abort(400)
  db.delete(confirm_key)

  # Get access token
  access_token = db.hget(subscriber_number, 'access_token')
  if not access_token:
    abort(403)

  suffix = app.config['GLOBE_SHORTCODE'][-4:] # this is weird!
  reference_code = '{0}1{1:06d}'.format(suffix, db.scard('charges') + 1)

  params = {'access_token': access_token}
  req = {
    'amount': '0.00',
    'description': amount,
    'endUserId': subscriber_number,
    'referenceCode': reference_code,
    'transactionOperationStatus': 'charged',
  }

  # Charge baby charge
  res = requests.post(
    const.G_CHARGING_ENDPOINT,
    headers={
      'Content-Type': 'application/json',
    },
    params=params,
    data=json.dumps(req)
  )

  # Log charges
  db.sadd('charges', reference_code)
  db.hmset(
    'charges:{}'.format(reference_code),
    {
      'subscriber_number': subscriber_number,
      'amount': amount,
    },
  )

  if not res.ok:
    abort(500)

  # TODO:
  # Retrieve download url

  return jsonify(
    download_url="https://docs.google.com/uc?id=0BwrPbVd2f3w8TmlRblNoX2RJV3c&export=download",
  )
# ==== END /confirm ==== #

@app.route('/download/<item_id>')
def download(item_id):
  # TODO: Retrieve file
  pass

@app.route('/login', methods=['GET', 'POST'])
def login():
  if request.method == 'POST':
    session['subscriber_number'] = request.values['subscriber_number']
    return redirect(url_for('dashboard'))

  return render_template('login.html')

@app.route('/logout')
def logout():
  session.clear()
  return redirect(url_for('index'))

def logged_in():
  subscriber_number = session.get('subscriber_number')
  if not subscriber_number:
    abort(401)
  return subscriber_number

@app.route('/dashboard')
def dashboard():
  subscriber_number = logged_in()
  # TODO: Get items
  # Example:
  items = [
    {
      'item_id': 89241749781247821,
      'filename': 'filename.pdf',
    },
    {
      'item_id': 193792813712,
      'filename': 'filename.pdf',
    },
    {
      'item_id': 290183921,
      'filename': 'filename.pdf',
    },
  ]
  return render_template(
    'dashboard.html',
    subscriber_number=subscriber_number,
    items=items,
  )

@app.route('/upload', methods=['POST'])
def upload():
  subscriber_number = logged_in()

  # TODO
  # upload file to filesystem: /var/uploads
  # filename = ?
  # filepath = ?

  item_id = simpleflake()

  # Save as upload of user
  db.sadd(
    '{}:items'.format(subscriber_number),
    item_id,
  )

  # Save upload details
  db.hmset(
    '{}:items:{}'.format(
      subscriber_number,
      item_id,
    ),
    {
      'filename': filename,
      'filepath': filepath,
    },
  )

  return redirect(url_for('dashboard'))

@app.route('/delete/<item_id>')
def delete(item_id):
  subscriber_number = logged_in()

  # Remove from user uploads
  db.srem(
    '{}:items'.format(subscriber_number),
    item_id,
  )

  # Remove upload details
  db.delete('{}:items:{}'.format(
    subscriber_number,
    item_id,
  ))

  # TODO: Not urgent
  # Delete uploads

  return redirect(url_for('dashboard'))


if __name__ == '__main__':
  app.run(host="0.0.0.0", debug=True)
