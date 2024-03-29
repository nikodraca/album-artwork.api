import json
from pprint import pprint
from colorthief import ColorThief
from urllib.request import urlopen
import requests
import sys
import io
import base64
from PIL import Image, ImageFont, ImageDraw
from pymongo import MongoClient
import creds
from fake_useragent import UserAgent
import numpy
from time import gmtime, strftime

# init mongo connection
client = MongoClient('mongodb://{}:{}@ds131551.mlab.com:31551/album-artwork'.format(creds.MONGO_USERNAME, creds.MONGO_PASSWORD))
db = client['album-artwork']


def search_for_album(album_name):
	ua = UserAgent()

	# get spotify token
	SPOTIFY_REFRESH_TOKEN = creds.spotify_refresh_token

	token_payload = { "grant_type" : "refresh_token", "refresh_token" : creds.spotify_refresh_token }
	token_clients = base64.b64encode(bytes('{}:{}'.format(creds.spotify_client_id, creds.spotify_client_secret), 'utf-8'))
	token_headers = {"Authorization" : "Basic {}".format(token_clients.decode("utf-8"))}
	access_token_request = requests.post("https://accounts.spotify.com/api/token", data=token_payload, headers=token_headers)

	SPOTIFY_ACCESS_TOKEN = access_token_request.json()['access_token']

	# attach payload
	payload = {
	   "access_token": SPOTIFY_ACCESS_TOKEN,
	   "token_type": "Bearer",
	   "refresh_token": SPOTIFY_REFRESH_TOKEN,
		"q" : album_name,
		"type" : 'album'
	}

	# make api call
	header = {'User-Agent':str(ua.random)}
	r = requests.get('https://api.spotify.com/v1/search', params=payload, headers=header)


	spotify_album_json = r.json()

	return spotify_album_json


def album_to_db(album_resp):
	albums_list = []
	albums_collection = db['albums']

	for album in album_resp:

		if album['album_type'] == 'album' and not (albums_collection.find_one({"album_id" : album['id']})):
			album_dict = {
				"album_id" : album['id'],
				"name" : album['name'],
				"artist" : {
					"id" : album['artists'][0]['id'],
					"name" : album['artists'][0]['name'],
				},
				"href" : album['href'],
				"images" : album['images'],
				"color_palette" : color_palette_from_url(album['images'][0]['url']),
			}

			albums_list.append(album_dict)
			pprint(album_dict)

	if len(albums_list) > 0:
		post_ids = albums_collection.insert_many(albums_list).inserted_ids

		for a in albums_list:
			a['_id'] = str(a['_id'])

	return albums_list


def color_palette_from_url(url):
	r = requests.get(url)
	f = io.BytesIO(r.content)

	color_thief = ColorThief(f)

	color_palette = color_thief.get_palette(quality=9)

	res = [list(x) for x in color_palette]

	return res


def find_coeffs(pb, pa):
    matrix = []
    for p1, p2 in zip(pa, pb):
        matrix.append([p1[0], p1[1], 1, 0, 0, 0, -p2[0]*p1[0], -p2[0]*p1[1]])
        matrix.append([0, 0, 0, p1[0], p1[1], 1, -p2[1]*p1[0], -p2[1]*p1[1]])

    A = numpy.matrix(matrix, dtype=numpy.float)
    B = numpy.array(pb).reshape(8)

    res = numpy.dot(numpy.linalg.inv(A.T * A) * A.T, B)
    return numpy.array(res).reshape(8)


def render_poster_mockups(img, img_path, pb, paste_pos):
	img_width, img_height = img.size

	poster = Image.open("static/img/{}".format(img_path))
	poster = poster.convert("RGBA")

	coeffs = find_coeffs([(0, 0), (img_width, 0), (img_width, img_height), (0, img_height)], pb)

	poster_img = img.transform(img.size, Image.PERSPECTIVE, coeffs ,Image.BILINEAR, fillcolor="red")
	poster.paste(poster_img, paste_pos, mask=poster_img)

	buffered = io.BytesIO()
	poster.save(buffered, format="PNG")
	image_base_64_string = base64.b64encode(buffered.getvalue())

	return image_base_64_string.decode("utf-8")


def render_image(json_data):
	img = Image.open("static/img/blank_light.png")
	img = img.convert("RGBA")

	draw = ImageDraw.Draw(img)
	font = ImageFont.truetype("Helvetica", 12)

	poster_title_text = json_data['album_title']
	poster_title_font = ImageFont.truetype("Helvetica", 40)

	#### Create poster

	img_width, img_height = img.size

	# this is fucking weird lol
	# I just wanted something that is proportional
	album_len_spacing = len(json_data['album_list']) + 2
	v_gap_spacing = img_height/album_len_spacing - (img_height/album_len_spacing/album_len_spacing)
	h_gap_spacing = (img_width/13)

	v_gap = v_gap_spacing * 2

	for album in json_data['album_list']:
		h_gap = h_gap_spacing * 2

		for color in album['color_palette']:
			draw.line((h_gap, v_gap, h_gap+h_gap_spacing, v_gap), fill=tuple(color), width=40)
			h_gap += h_gap_spacing

		draw.text((h_gap_spacing * 2, v_gap+30),"{} - {}".format(album['artist']['name'], album['name']),(0,0,0),font=font)

		v_gap += v_gap_spacing


	draw.text((h_gap_spacing * 2, v_gap), poster_title_text, (0,0,0),font=poster_title_font)

	poster_1 = render_poster_mockups(img, "poster_1_sm.png", [(22, 22), (528, 17), (543, 749), (29, 754)], (409, 72))
	poster_2 = render_poster_mockups(img, "poster_2_sm.png", [(28, 20), (262, 21), (260, 362), (22, 361)], (563, 274))

	return [poster_1, poster_2]


def get_albums_from_db(query):

	res = []

	albums_collection = db['albums']

	for album in albums_collection.find({'name': {'$regex': query, '$options': 'i'}}):
		album['_id'] = str(album['_id'])
		res.append(album)

	return res

def email_to_db(email):
	email_collection = db['emails']
	email_obj = {"email" : email}

	email_id = email_collection.insert_one(email_obj).inserted_id

	return {"email" : email}


search_results = search_for_album("Childish Gambino")
albums_list = album_to_db(search_results['albums']['items'])
# albums_list = get_albums_from_db("kanye")

# render_image(albums_list)

