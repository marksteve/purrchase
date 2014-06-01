import os

from flask import Flask, request, jsonify
from redis import StrictRedis
import requests

app = Flask(__name__)
r = StrictRedis(host=os.environ.get('REDIS_PORT_6379_TCP_ADDR'))

@app.route('/', methods=['GET', 'POST'])
def index():
    res = requests.get('https://google.com')
    return res.content

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
