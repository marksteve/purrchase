import os
import constants

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
  test = get_access_token()
  return test

def get_access_token():
  return "ACCESS_TOKEN"

# ==== /sms ==== #
@app.route('/sms', methods=['POST'])
def sms_uri():
  return "SMS"

# ==== /charge ==== #
@app.route('/charge', methods=['POST'])
def charge_uri():
  return "CHARGE"

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)

#test katpadillaaa@gmail as author
