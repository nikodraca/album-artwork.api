import requests
import json
from pprint import pprint
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import time
import sys
import csv
from datetime import datetime
from flask import Flask, request
from flask_restful import Resource, Api, reqparse
from utils import get_albums_from_db, render_image, email_to_db, album_to_db, search_for_album
from flask_cors import CORS, cross_origin
from flask.json import jsonify

app = Flask(__name__)
api = Api(app)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

class SearchAlbum(Resource):
	@cross_origin()
	def get(self, query):
		resp = get_albums_from_db(query)

		return jsonify(resp[:5])

class SearchAlbumFromSpotify(Resource):
	@cross_origin()
	def get(self, query):
		resp = search_for_album(query)
		albums_list = album_to_db(resp['albums']['items'])

		return jsonify(albums_list[:5])


class RenderPoster(Resource):
	@cross_origin()
	def post(self):
		json_data = request.get_json(force=True)

		return jsonify(render_image(json_data))

class EmailList(Resource):
	@cross_origin()
	def post(self):
		json_data = request.get_json(force=True)

		return jsonify(email_to_db(json_data['email']))


class Index(Resource):
	def get(self):
		return {"ok" : True}

api.add_resource(SearchAlbum, '/search_album/<query>')
api.add_resource(SearchAlbumFromSpotify, '/search_album_from_spotify/<query>')
api.add_resource(RenderPoster, '/render_poster')
api.add_resource(EmailList, '/email_list')
api.add_resource(Index, '/')

if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0', port=5001)