import os
import const

from flask import Flask, request, jsonify, render_template
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

def get_code():
  # nu to?
  return true

def get_access_token():
  app_id = 'oyap4tKpyBqf4RcLkgiyzefLnae6tMj7'
  app_secret ='256e555ba0d3d76c933bc56fae30c2192e2880557625ab8fe947429e7383a3e5'
  code = get_code()

  params = {'app_id': app_id, 'app_secret': app_secret, 'code': code}
  r = requests.post(const.G_AUTH_ENDPOINT, data=params)
  return "ACCESS_TOKEN"
# ==== END /oauth ==== #

# ==== /sms ==== #
@app.route('/sms', methods=['POST'])
def sms_uri():
  return "SMS"
# ==== END /sms ==== #

# ==== /charge ==== #
@app.route('/charge', methods=['POST'])
def charge_uri():
  return "CHARGE"
# ==== END /charge ==== #

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)

#test katpadillaaa@gmail as author
