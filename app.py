import os
import const
import uuid

from flask import Flask, request, json, jsonify, render_template
#from redis import StrictRedis
import requests

app = Flask(__name__)
#r = StrictRedis(host=os.environ.get('REDIS_PORT_6379_TCP_ADDR'))

@app.route('/', methods=['GET', 'POST'])
def index():
  return render_template('index.html')

# ==== /oauth ==== #
@app.route('/oauth', methods=['GET'])
def oauth_uri():
  access_token = get_access_token()
  return access_token

# this doesn't really get JUST the access token
# returns json data of subscriber_number & access_token
def get_access_token():
  # Hackathon "merchant" sample details
  app_id     = 'oyap4tKpyBqf4RcLkgiyzefLnae6tMj7'
  app_secret = '256e555ba0d3d76c933bc56fae30c2192e2880557625ab8fe947429e7383a3e5'

  code       = request.args['code']

  params = {'app_id': app_id, 'app_secret': app_secret, 'code': code}
  res    = requests.post(const.G_AUTH_ENDPOINT, data=params)

  return  jsonify(**res.json())
# ==== END /oauth ==== #

# ==== /sms ==== #
@app.route('/sms', methods=['POST','GET'])
def sms_uri():
  # HARDCODED STUFF huhu :((
  msisdn = '9175246984'
  sender = '0680' # this is weird! 21580680
  access_token = 'tTDETIWF7yJtfdT_HlhMD53Ixqq26rSCHmdpJTO4TPY'
  # Generate a random code for this user session
  security_code = str(uuid.uuid4())[:6]

  params   = { 'access_token': access_token }
  req_body = {
    'outboundSMSMessageRequest': {
      #'clientCorrelator': security_code, #dyan muna yan
      'senderAddress': 'tel:%s' % sender,
      'outboundSMSTextMessage': { 'message':'Swaggy test! This is your code: ' + security_code },
      'address': 'tel:+63%s' % msisdn
    }
  }

  res = requests.post(
    const.G_SMS_ENDPOINT % sender,
    headers = {
      'Content-Type': 'application/x-www-form-urlencoded',
      'Accept': 'application/json'
    },
    params = params,
    data = json.dumps(req_body)
  )

  if res.ok:
    return "alright!"

  return "boo!"
# ==== END /sms ==== #

# ==== /charge ==== #
@app.route('/charge', methods=['POST'])
def charge_uri():
  return "CHARGE"
# ==== END /charge ==== #

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)

#test katpadillaaa@gmail as author
