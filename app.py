import os
import time

import const
import requests
from flask import abort, Flask, json, jsonify, render_template, request
from redis import StrictRedis
from simpleflake import simpleflake

app = Flask(__name__)
app.config.from_pyfile('config.py')
db = StrictRedis(host=os.environ.get('REDIS_PORT_6379_TCP_ADDR'))

@app.route('/')
def index():
  return render_template('index.html')

@app.route('/opm')
def opm():
  return render_template('opm.html')

# ==== /oauth ==== #
@app.route('/oauth')
def oauth():
  return render_template('oauth.html')
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
    db.hset(
      payload['subscriber_number'],
      'access_token',
      payload['access_token'],
    )
    return render_template('oauth.html')
  else:
    abort(500)
# ==== END /oauth ==== #

# ==== /sms ==== #
@app.route('/sms', methods=['POST', 'GET'])
def sms():
  return "boo!"
# ==== END /sms ==== #

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

  # check access token
  if not access_token:
    return jsonify(
      needs_authorization=True,
      dialog_url=const.G_DIALOG.format(app.config['GLOBE_APP_ID']),
    )

  sender = app.config['GLOBE_SHORTCODE'][-4:] # this is weird!
  # Generate a random code for this user session
  security_code = str(simpleflake())[-6:]

  params = {'access_token': access_token}
  req = {
    'outboundSMSMessageRequest': {
      'clientCorrelator': str(simpleflake()),
      'senderAddress': 'tel:{}'.format(sender),
      'outboundSMSTextMessage': {
        'message': 'PHonePay\n\nYou will be charged PHP {}. This is your code to proceed: {}'.format(
          amount,
          security_code,
        ),
      },
      'address': ['tel:+63{}'.format(subscriber_number)],
    }
  }

  res = requests.post(
    const.G_SMS_ENDPOINT.format(sender),
    headers = {
      'Content-Type': 'application/json',
    },
    params = params,
    data = json.dumps(req)
  )

  if res.ok:
    #: Maybe log a little?
    # r.zadd(msisdn, time.localtime(), amount)
    payload = res.json()
    payload.update(confirm_code_sent=True)
    return jsonify(**payload)
  else:
    abort(500)

# ==== END /charge ==== #


if __name__ == '__main__':
  app.run(host="0.0.0.0", debug=True)

