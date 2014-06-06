import os
import time
from random import randint

import const
import requests
from flask import (abort, Flask, json, jsonify, redirect, render_template,
                   request, session, url_for, flash, get_flashed_messages, send_file)
from werkzeug.utils import secure_filename
from redis import StrictRedis
from simpleflake import simpleflake

# For upload stuff
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
app.config.from_pyfile('config.py')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
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

def gen_reference_code(suffix):
  return '{0}1{1:06d}'.format(suffix, randint(0, 999999))

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

  # Get access token
  access_token = db.hget(
    '{}:{}'.format(shortcode, subscriber_number),
    'access_token',
  )
  if not access_token:
    abort(403)

  suffix = shortcode[-4:] # this is weird!
  reference_code = gen_reference_code(suffix)

  params = {'access_token': access_token}

  # Charge baby charge
  for _ in range(3):
    req = {
      'amount': '0.00',
      'description': amount,
      'endUserId': subscriber_number,
      'referenceCode': reference_code,
      'transactionOperationStatus': 'charged',
    }
    res = requests.post(
      const.G_CHARGING_ENDPOINT,
      headers={
        'Content-Type': 'application/json',
      },
      params=params,
      data=json.dumps(req)
    )
    if not res.ok:
      error = res.json().get('error')
      if error == 'Invalid referenceCode':
        reference_code = gen_reference_code(suffix)
        continue
      abort(500)
    break

  # Log charges
  db.sadd('charges', reference_code)
  db.hmset(
    'charges:{}'.format(reference_code),
    {
      'subscriber_number': subscriber_number,
      'amount': amount,
    },
  )

  # Delete confirm key
  db.delete(confirm_key)

  # TODO:
  # Retrieve download url

  return jsonify(
    download_url="https://docs.google.com/uc?id=0BwrPbVd2f3w8TmlRblNoX2RJV3c&export=download",
  )
# ==== END /confirm ==== #

@app.route('/download/<shortcode>/<item_id>')
def download(shortcode, item_id):
  # TODO: Retrieve file
  item=db.hgetall('{}:items:{}'.format(
    shortcode,
    item_id,
  ))
  return send_file(item['filepath'], as_attachment=True)

@app.route('/instabuy/<shortcode>/<item_id>')
def instabuy(shortcode, item_id):
  item=db.hgetall('{}:items:{}'.format(
    shortcode,
    item_id,
  ))
  return render_template('instabuy.html',shortcode=shortcode,item_id=item_id,**item)


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
  merchant = db.hgetall(shortcode)
  if not merchant:
    abort(401)
  merchant.update(globe_shortcode=shortcode)
  return merchant

@app.route('/dashboard')
def dashboard():
  merchant = logged_in()
  shortcode = merchant['globe_shortcode']
  item_ids=db.smembers('{}:items'.format(shortcode))
  items=[]
  for item_id in item_ids:
    item=db.hgetall('{}:items:{}'.format(
      shortcode,
      item_id,
    ))
    item.update(item_id=item_id)
    items.append(item)
  return render_template(
    'dashboard.html',
    integration="""<script src="http://phonepay.marksteve.com/static/js/phonepay.js"></script>
<script>pp({{shortcode: {}}});</script>""",
    item_code="""<div
  class="payload"
  data-id="{}"
  data-desc="{}"
  data-amount="{}"
></div>""",
    merchant=merchant,
    items=items,
    messages=get_flashed_messages()
  )

def allowed_file(filename):
  return '.' in filename and \
  filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload():
  merchant = logged_in()

  file = request.files['file']
  #empty?
  if not file:
    flash('Empty!')
    return redirect(url_for('dashboard'))
  if file and allowed_file(file.filename):
    filename = secure_filename(file.filename)
    filepath=os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

  item_id = simpleflake()
  shortcode = merchant['globe_shortcode']
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
      'desc'    : request.form['description'],
      'price'   : request.form['price']
    },
  )
  flash('Uploaded!')
  return redirect(url_for('dashboard'))

@app.route('/delete/<item_id>')
def delete(item_id):
  merchant = logged_in()

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
