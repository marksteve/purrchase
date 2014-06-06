import os
import time

import const
import requests
from flask import (abort, Flask, json, jsonify, redirect, render_template,
                   request, session, url_for)
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

@app.route('/info/<shortcode>')
def info(shortcode):
  merchant = db.hgetall(shortcode)
  return jsonify(
    store_name=merchant['store_name'],
  )

# ==== /oauth ==== #
@app.route('/oauth/<shortcode>')
def oauth(shortcode):
  merchant = db.hgetall(shortcode)
  if not merchant:
    abort(404)
  code = request.args['code']
  data = {
    'app_id': merchant['globe_app_id'],
    'app_secret': merchant['globe_app_secret'],
    'code': code,
  }
  res = requests.post(const.G_AUTH_ENDPOINT, data=data)
  if res.ok:
    payload = res.json()
    db.hmset(
      '{}:{}'.format(shortcode, payload['subscriber_number']),
      payload,
    )
    return render_template(
      'oauth.html',
      subscriber_number=payload['subscriber_number'],
      store_name=merchant['store_name'],
    )
  else:
    abort(500)
# ==== END /oauth ==== #

# ==== /charge ==== #
@app.route('/charge', methods=['POST'])
def charge():
  """
  Charge URI is the endpoint for charging and sending of sms
  This endpoint expects the ff params:
  - shortcode
  - subscriber_number
  - amount
  """

  shortcode = request.json['shortcode']
  merchant = db.hgetall(shortcode)
  if not merchant:
    abort(404)

  subscriber_number = request.json['subscriber_number']
  amount = request.json['amount']

  # Get the access token from DB
  access_token = db.hget(
    '{}:{}'.format(shortcode, subscriber_number),
    'access_token',
  )
  if not access_token:
    return jsonify(
      needs_authorization=True,
      dialog_url=const.G_DIALOG.format(merchant['globe_app_id']),
    )

  sender = shortcode[-4:] # this is weird!
  confirm_code = str(simpleflake())[-6:] # Generate a random code for this user session

  params = {'access_token': access_token}
  req = {
    'outboundSMSMessageRequest': {
      'clientCorrelator': str(simpleflake()),
      'senderAddress': 'tel:{}'.format(sender),
      'outboundSMSTextMessage': {
        'message': '{}\n\nYou will be charged PHP {}. This is your code to proceed: {}'.format(
          merchant['store_name'],
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
  # Expires after 15 minutes
  db.setex(
    '{}:{}:confirm:{}'.format(
      shortcode,
      subscriber_number,
      confirm_code,
    ),
    15 * 60,  # 15 minutes
    amount,
  )

  return jsonify(**payload)
# ==== END /charge ==== #

# ==== /confirm ==== #
@app.route('/confirm', methods=['POST'])
def confirm():
  shortcode = request.json['shortcode']
  merchant = db.hgetall(shortcode)
  if not merchant:
    abort(404)

  subscriber_number = request.json['subscriber_number']
  confirm_code = request.json['confirm_code']

  # Get confirm code assoc
  confirm_key = '{}:{}:confirm:{}'.format(
    shortcode,
    subscriber_number,
    confirm_code,
  )
  amount = db.get(confirm_key)
  if not amount:
    abort(400)
  db.delete(confirm_key)

  # Get access token
  access_token = db.hget(
    '{}:{}'.format(shortcode, subscriber_number),
    'access_token',
  )
  if not access_token:
    abort(403)

  suffix = shortcode[-4:] # this is weird!
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

  if not res.ok:
    abort(500)

  # Log charges
  db.sadd('charges', reference_code)
  db.hmset(
    'charges:{}'.format(reference_code),
    {
      'subscriber_number': subscriber_number,
      'amount': amount,
    },
  )

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

@app.route('/signup', methods=['GET', 'POST'])
def signup():
  shortcode = request.form['globe_shortcode']
  db.hmset(shortcode, {
    'store_name': request.form['store_name'],
    'globe_app_id': request.form['globe_app_id'],
    'globe_app_secret': request.form['globe_app_secret'],
  })
  session['shortcode'] = shortcode
  return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
  if request.method == 'POST':
    shortcode = request.values['shortcode']
    if db.exists(shortcode):
      session['shortcode'] = shortcode
      return redirect(url_for('dashboard'))

  return render_template('login.html')

@app.route('/logout')
def logout():
  session.clear()
  return redirect(url_for('index'))

def logged_in():
  shortcode = session.get('shortcode')
  if not shortcode:
    abort(401)
  return shortcode

@app.route('/dashboard')
def dashboard():
  shortcode = logged_in()
  # TODO: Get items
  # Example:
  items = [
    {
      'item_id': 89241749781247821,
      'filename': 'filename.pdf',
    },
    {
      'item_id': 193792813712,
      'filename': 'filename.mp3',
    },
    {
      'item_id': 290183921,
      'filename': 'filename.jpg',
    },
  ]
  return render_template(
    'dashboard.html',
    shortcode=shortcode,
    items=items,
  )

@app.route('/upload', methods=['POST'])
def upload():
  shortcode = logged_in()

  # TODO
  # upload file to filesystem: /var/uploads
  # filename = ?
  # filepath = ?

  item_id = simpleflake()

  # Save as upload of user
  db.sadd(
    '{}:items'.format(shortcode),
    item_id,
  )

  # Save upload details
  db.hmset(
    '{}:items:{}'.format(
      shortcode,
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
  shortcode = logged_in()

  # Remove from user uploads
  db.srem(
    '{}:items'.format(shortcode),
    item_id,
  )

  # Remove upload details
  db.delete('{}:items:{}'.format(
    shortcode,
    item_id,
  ))

  # TODO: Not urgent
  # Delete uploads

  return redirect(url_for('dashboard'))


if __name__ == '__main__':
  app.run(host="0.0.0.0", debug=True)
