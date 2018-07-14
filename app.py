import requests
import json
from pprint import pprint
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import time
import sys
import csv
from datetime import datetime
from flask import Flask
from flask_restful import Resource, Api, reqparse
from utils import get_albums_from_db
from flask_cors import CORS, cross_origin
from flask.json import jsonify

app = Flask(__name__)
api = Api(app)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

parser = reqparse.RequestParser()
parser.add_argument('albumsList', action='append')


class SearchAlbum(Resource):
	@cross_origin()
	def get(self, query):
		"""
		GET album
		"""

		resp = get_albums_from_db(query)

		pprint(resp)

		return jsonify(resp[:5])

class RenderPoster(Resource):
	@cross_origin()
	def post(self):
		args = parser.parse_args()
		albums_list = args['albumsList']

		return str(albums_list)



class Index(Resource):
	def get(self):
		return {"ok" : True}

api.add_resource(SearchAlbum, '/search_album/<query>')
api.add_resource(RenderPoster, '/render_poster')
api.add_resource(Index, '/')

if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0', port=5001)