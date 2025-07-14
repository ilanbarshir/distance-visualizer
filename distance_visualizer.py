# Subjective Distance Visualizer
# A tool to explore the differences between perceived and actual geographic distances

import folium
import geopy.distance
from geopy.geocoders import Nominatim
from flask import Flask, render_template, request, jsonify, make_response, session
import numpy as np
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
import requests
from requests.exceptions import Timeout, RequestException
import json
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  
import seaborn as sns
import io
import base64
from datetime import datetime
import pandas as pd

app = Flask(__name__)

quiz_results = []

MAJOR_LANDMARKS = {
    'new york': [
        {'name': 'Statue of Liberty', 'type': 'Monument', 'lat': 40.6892, 'lon': -74.0445, 'description': 'Iconic symbol of freedom and democracy', 'website': 'https://www.nps.gov/stli'},
        {'name': 'Central Park', 'type': 'Park', 'lat': 40.7829, 'lon': -73.9654, 'description': 'Famous urban park in Manhattan', 'website': 'https://www.centralparknyc.org'},
        {'name': 'Empire State Building', 'type': 'Attraction', 'lat': 40.7484, 'lon': -73.9857, 'description': 'Iconic Art Deco skyscraper', 'website': 'https://www.esbnyc.com'},
        {'name': 'Metropolitan Museum of Art', 'type': 'Museum', 'lat': 40.7794, 'lon': -73.9632, 'description': 'World-famous art museum', 'website': 'https://www.metmuseum.org'},
        {'name': 'Times Square', 'type': 'Attraction', 'lat': 40.7580, 'lon': -73.9855, 'description': 'Major commercial intersection and tourist destination', 'website': 'https://www.timessquarenyc.org'},
        {'name': 'Brooklyn Bridge', 'type': 'Bridge', 'lat': 40.7061, 'lon': -73.9969, 'description': 'Historic suspension bridge connecting Manhattan and Brooklyn', 'website': 'https://www.nyc.gov/html/dot/html/infrastructure/brooklyn-bridge.shtml'},
        {'name': 'One World Trade Center', 'type': 'Building', 'lat': 40.7127, 'lon': -74.0134, 'description': 'Tallest building in the Western Hemisphere', 'website': 'https://www.onewtc.com'},
        {'name': 'High Line', 'type': 'Park', 'lat': 40.7480, 'lon': -74.0048, 'description': 'Elevated linear park built on a historic freight rail line', 'website': 'https://www.thehighline.org'},
        {'name': 'American Museum of Natural History', 'type': 'Museum', 'lat': 40.7813, 'lon': -73.9739, 'description': 'World-renowned natural history museum', 'website': 'https://www.amnh.org'},
        {'name': 'Rockefeller Center', 'type': 'Complex', 'lat': 40.7587, 'lon': -73.9787, 'description': 'Famous commercial complex and entertainment venue', 'website': 'https://www.rockefellercenter.com'}
    ],
    'london': [
        {'name': 'Big Ben', 'type': 'Monument', 'lat': 51.5007, 'lon': -0.1246, 'description': 'Famous clock tower at Westminster Palace', 'website': 'https://www.parliament.uk/bigben'},
        {'name': 'British Museum', 'type': 'Museum', 'lat': 51.5194, 'lon': -0.1270, 'description': 'World-famous museum of human history and culture', 'website': 'https://www.britishmuseum.org'},
        {'name': 'Tower of London', 'type': 'Castle', 'lat': 51.5081, 'lon': -0.0759, 'description': 'Historic castle and fortress', 'website': 'https://www.hrp.org.uk/tower-of-london'},
        {'name': 'Buckingham Palace', 'type': 'Palace', 'lat': 51.5014, 'lon': -0.1419, 'description': 'Official residence of the British monarch', 'website': 'https://www.rct.uk/visit/buckingham-palace'},
        {'name': 'Hyde Park', 'type': 'Park', 'lat': 51.5073, 'lon': -0.1657, 'description': 'One of the largest parks in central London', 'website': 'https://www.royalparks.org.uk/parks/hyde-park'},
        {'name': 'London Eye', 'type': 'Attraction', 'lat': 51.5033, 'lon': -0.1195, 'description': 'Giant observation wheel on the South Bank', 'website': 'https://www.londoneye.com'},
        {'name': 'St. Paul\'s Cathedral', 'type': 'Church', 'lat': 51.5139, 'lon': -0.0984, 'description': 'Anglican cathedral and one of London\'s most famous landmarks', 'website': 'https://www.stpauls.co.uk'},
        {'name': 'Tower Bridge', 'type': 'Bridge', 'lat': 51.5055, 'lon': -0.0754, 'description': 'Victorian bridge and exhibition', 'website': 'https://www.towerbridge.org.uk'},
        {'name': 'Natural History Museum', 'type': 'Museum', 'lat': 51.4967, 'lon': -0.1764, 'description': 'World-famous natural history museum', 'website': 'https://www.nhm.ac.uk'},
        {'name': 'Covent Garden', 'type': 'Market', 'lat': 51.5122, 'lon': -0.1217, 'description': 'Famous market and entertainment area', 'website': 'https://www.coventgarden.london'}
    ],
    'paris': [
        {'name': 'Eiffel Tower', 'type': 'Monument', 'lat': 48.8584, 'lon': 2.2945, 'description': 'Iconic iron lattice tower', 'website': 'https://www.toureiffel.paris'},
        {'name': 'Louvre Museum', 'type': 'Museum', 'lat': 48.8606, 'lon': 2.3376, 'description': 'World\'s largest art museum', 'website': 'https://www.louvre.fr'},
        {'name': 'Notre-Dame Cathedral', 'type': 'Church', 'lat': 48.8530, 'lon': 2.3499, 'description': 'Medieval Catholic cathedral', 'website': 'https://www.notredamedeparis.fr'},
        {'name': 'Arc de Triomphe', 'type': 'Monument', 'lat': 48.8738, 'lon': 2.2950, 'description': 'Triumphal arch honoring those who fought for France', 'website': 'https://www.paris-arc-de-triomphe.fr'},
        {'name': 'Champs-Élysées', 'type': 'Avenue', 'lat': 48.8698, 'lon': 2.3079, 'description': 'Famous avenue in Paris', 'website': 'https://www.champselysees-paris.com'},
        {'name': 'Montmartre', 'type': 'District', 'lat': 48.8867, 'lon': 2.3431, 'description': 'Historic district known for its artistic heritage', 'website': 'https://www.montmartre-guide.com'},
        {'name': 'Palace of Versailles', 'type': 'Palace', 'lat': 48.8044, 'lon': 2.1232, 'description': 'Former royal residence and UNESCO World Heritage site', 'website': 'https://en.chateauversailles.fr'},
        {'name': 'Musée d\'Orsay', 'type': 'Museum', 'lat': 48.8600, 'lon': 2.3266, 'description': 'Museum housed in a former railway station', 'website': 'https://www.musee-orsay.fr'},
        {'name': 'Luxembourg Gardens', 'type': 'Park', 'lat': 48.8462, 'lon': 2.3372, 'description': 'Beautiful public park and gardens', 'website': 'https://www.senat.fr/visite/jardin'},
        {'name': 'Centre Pompidou', 'type': 'Museum', 'lat': 48.8607, 'lon': 2.3522, 'description': 'Modern art museum and cultural center', 'website': 'https://www.centrepompidou.fr'}
    ],
    'tokyo': [
        {'name': 'Tokyo Skytree', 'type': 'Tower', 'lat': 35.7100, 'lon': 139.8107, 'description': 'Tallest structure in Japan', 'website': 'https://www.tokyo-skytree.jp'},
        {'name': 'Senso-ji Temple', 'type': 'Temple', 'lat': 35.7147, 'lon': 139.7968, 'description': 'Ancient Buddhist temple', 'website': 'https://www.senso-ji.jp'},
        {'name': 'Tokyo Imperial Palace', 'type': 'Palace', 'lat': 35.6852, 'lon': 139.7528, 'description': 'Primary residence of the Emperor of Japan', 'website': 'https://sankan.kunaicho.go.jp'},
        {'name': 'Meiji Shrine', 'type': 'Shrine', 'lat': 35.6764, 'lon': 139.6993, 'description': 'Shinto shrine dedicated to Emperor Meiji', 'website': 'https://www.meijijingu.or.jp'},
        {'name': 'Ueno Park', 'type': 'Park', 'lat': 35.7142, 'lon': 139.7744, 'description': 'Large public park with museums and zoo', 'website': 'https://www.tokyo-zoo.net'},
        {'name': 'Shibuya Crossing', 'type': 'Attraction', 'lat': 35.6580, 'lon': 139.7016, 'description': 'World\'s busiest pedestrian crossing', 'website': 'https://www.shibuya-scramble-square.com'},
        {'name': 'Tokyo Disneyland', 'type': 'Theme Park', 'lat': 35.6329, 'lon': 139.8804, 'description': 'Popular theme park', 'website': 'https://www.tokyodisneyresort.jp'},
        {'name': 'Tsukiji Outer Market', 'type': 'Market', 'lat': 35.6654, 'lon': 139.7697, 'description': 'Famous fish market and food area', 'website': 'https://www.tsukiji.or.jp'},
        {'name': 'Tokyo National Museum', 'type': 'Museum', 'lat': 35.7187, 'lon': 139.7767, 'description': 'Japan\'s oldest and largest museum', 'website': 'https://www.tnm.jp'},
        {'name': 'Roppongi Hills', 'type': 'Complex', 'lat': 35.6605, 'lon': 139.7292, 'description': 'Modern entertainment and shopping complex', 'website': 'https://www.roppongihills.com'}
    ],
    'rome': [
        {'name': 'Colosseum', 'type': 'Monument', 'lat': 41.8902, 'lon': 12.4922, 'description': 'Ancient Roman amphitheater', 'website': 'https://parcocolosseo.it'},
        {'name': 'Vatican Museums', 'type': 'Museum', 'lat': 41.9022, 'lon': 12.4539, 'description': 'Art museums within Vatican City', 'website': 'https://www.museivaticani.va'},
        {'name': 'Trevi Fountain', 'type': 'Fountain', 'lat': 41.9009, 'lon': 12.4833, 'description': 'Famous Baroque fountain', 'website': 'https://www.trevifountain.net'},
        {'name': 'Pantheon', 'type': 'Temple', 'lat': 41.8986, 'lon': 12.4769, 'description': 'Ancient Roman temple', 'website': 'https://www.pantheonroma.com'},
        {'name': 'Roman Forum', 'type': 'Historic Site', 'lat': 41.8925, 'lon': 12.4853, 'description': 'Ancient Roman plaza', 'website': 'https://parcocolosseo.it/area/foro-romano'},
        {'name': 'St. Peter\'s Basilica', 'type': 'Church', 'lat': 41.9022, 'lon': 12.4539, 'description': 'Renaissance church in Vatican City', 'website': 'https://www.vatican.va'},
        {'name': 'Spanish Steps', 'type': 'Monument', 'lat': 41.9058, 'lon': 12.4823, 'description': 'Famous staircase in Rome', 'website': 'https://www.turismoroma.it'},
        {'name': 'Castel Sant\'Angelo', 'type': 'Castle', 'lat': 41.9031, 'lon': 12.4663, 'description': 'Historic fortress and museum', 'website': 'https://castelsantangelo.beniculturali.it'},
        {'name': 'Piazza Navona', 'type': 'Square', 'lat': 41.8992, 'lon': 12.4731, 'description': 'Famous square with fountains', 'website': 'https://www.turismoroma.it'},
        {'name': 'Borghese Gallery', 'type': 'Museum', 'lat': 41.9142, 'lon': 12.4922, 'description': 'Art gallery in Villa Borghese', 'website': 'https://galleriaborghese.beniculturali.it'}
    ],
    'sydney': [
        {'name': 'Sydney Opera House', 'type': 'Theater', 'lat': -33.8568, 'lon': 151.2153, 'description': 'Iconic performing arts center', 'website': 'https://www.sydneyoperahouse.com'},
        {'name': 'Sydney Harbour Bridge', 'type': 'Bridge', 'lat': -33.8523, 'lon': 151.2108, 'description': 'Steel arch bridge across Sydney Harbour', 'website': 'https://www.bridgeclimb.com'},
        {'name': 'Bondi Beach', 'type': 'Beach', 'lat': -33.8915, 'lon': 151.2767, 'description': 'Famous beach and surf spot', 'website': 'https://www.bondivillage.com'},
        {'name': 'Royal Botanic Garden', 'type': 'Garden', 'lat': -33.8643, 'lon': 151.2165, 'description': 'Botanical garden in central Sydney', 'website': 'https://www.rbgsyd.nsw.gov.au'},
        {'name': 'Darling Harbour', 'type': 'District', 'lat': -33.8697, 'lon': 151.2017, 'description': 'Tourist precinct and entertainment area', 'website': 'https://www.darlingharbour.com'},
        {'name': 'Taronga Zoo', 'type': 'Zoo', 'lat': -33.8433, 'lon': 151.2407, 'description': 'Zoo with harbor views', 'website': 'https://taronga.org.au'},
        {'name': 'The Rocks', 'type': 'District', 'lat': -33.8597, 'lon': 151.2089, 'description': 'Historic area with markets and restaurants', 'website': 'https://www.therocks.com'},
        {'name': 'Art Gallery of NSW', 'type': 'Museum', 'lat': -33.8690, 'lon': 151.2171, 'description': 'Major art museum', 'website': 'https://www.artgallery.nsw.gov.au'},
        {'name': 'Manly Beach', 'type': 'Beach', 'lat': -33.7970, 'lon': 151.2877, 'description': 'Popular beach and surf spot', 'website': 'https://www.manly.nsw.gov.au'},
        {'name': 'Sydney Tower Eye', 'type': 'Tower', 'lat': -33.8704, 'lon': 151.2086, 'description': 'Observation deck and restaurant', 'website': 'https://www.sydneytowereye.com.au'}
    ],
    'berlin': [
        {'name': 'Brandenburg Gate', 'type': 'Monument', 'lat': 52.5163, 'lon': 13.3777, 'description': '18th-century neoclassical monument', 'website': 'https://www.berlin.de'},
        {'name': 'Berlin Wall Memorial', 'type': 'Memorial', 'lat': 52.5350, 'lon': 13.3903, 'description': 'Memorial to the Berlin Wall', 'website': 'https://www.berliner-mauer-gedenkstaette.de'},
        {'name': 'Museum Island', 'type': 'Museum', 'lat': 52.5219, 'lon': 13.4016, 'description': 'Complex of five museums', 'website': 'https://www.museumsinsel-berlin.de'},
        {'name': 'Reichstag Building', 'type': 'Building', 'lat': 52.5186, 'lon': 13.3761, 'description': 'German parliament building', 'website': 'https://www.bundestag.de'},
        {'name': 'Checkpoint Charlie', 'type': 'Historic Site', 'lat': 52.5075, 'lon': 13.3904, 'description': 'Famous border crossing point', 'website': 'https://www.mauermuseum.de'},
        {'name': 'Berlin Cathedral', 'type': 'Church', 'lat': 52.5192, 'lon': 13.4011, 'description': 'Protestant cathedral', 'website': 'https://www.berlinerdom.de'},
        {'name': 'Tiergarten', 'type': 'Park', 'lat': 52.5145, 'lon': 13.3501, 'description': 'Large urban park', 'website': 'https://www.berlin.de'},
        {'name': 'East Side Gallery', 'type': 'Art', 'lat': 52.5054, 'lon': 13.4401, 'description': 'Open-air gallery on Berlin Wall', 'website': 'https://eastsidegallery-berlin.de'},
        {'name': 'Pergamon Museum', 'type': 'Museum', 'lat': 52.5212, 'lon': 13.3966, 'description': 'Museum of ancient artifacts', 'website': 'https://www.smb.museum'},
        {'name': 'Alexanderplatz', 'type': 'Square', 'lat': 52.5219, 'lon': 13.4132, 'description': 'Major public square and transport hub', 'website': 'https://www.berlin.de'}
    ],
    'amsterdam': [
        {'name': 'Anne Frank House', 'type': 'Museum', 'lat': 52.3752, 'lon': 4.8840, 'description': 'Historic house and museum', 'website': 'https://www.annefrank.org'},
        {'name': 'Van Gogh Museum', 'type': 'Museum', 'lat': 52.3584, 'lon': 4.8811, 'description': 'Art museum dedicated to Van Gogh', 'website': 'https://www.vangoghmuseum.nl'},
        {'name': 'Rijksmuseum', 'type': 'Museum', 'lat': 52.3600, 'lon': 4.8852, 'description': 'Dutch national museum', 'website': 'https://www.rijksmuseum.nl'},
        {'name': 'Vondelpark', 'type': 'Park', 'lat': 52.3567, 'lon': 4.8687, 'description': 'Large urban park', 'website': 'https://www.hetvondelpark.net'},
        {'name': 'Jordaan', 'type': 'District', 'lat': 52.3731, 'lon': 4.8797, 'description': 'Historic neighborhood', 'website': 'https://www.amsterdam.info'},
        {'name': 'Dam Square', 'type': 'Square', 'lat': 52.3730, 'lon': 4.8936, 'description': 'Main square of Amsterdam', 'website': 'https://www.iamsterdam.com'},
        {'name': 'Canal Ring', 'type': 'District', 'lat': 52.3676, 'lon': 4.9041, 'description': 'UNESCO World Heritage site', 'website': 'https://www.amsterdam.info'},
        {'name': 'Artis Royal Zoo', 'type': 'Zoo', 'lat': 52.3661, 'lon': 4.9156, 'description': 'Oldest zoo in the Netherlands', 'website': 'https://www.artis.nl'},
        {'name': 'Heineken Experience', 'type': 'Museum', 'lat': 52.3578, 'lon': 4.8917, 'description': 'Interactive brewery tour', 'website': 'https://www.heinekenexperience.com'},
        {'name': 'A\'dam Lookout', 'type': 'Attraction', 'lat': 52.3917, 'lon': 4.9022, 'description': 'Observation deck with swing', 'website': 'https://www.adamlookout.com'}
    ],
    'barcelona': [
        {'name': 'Sagrada Familia', 'type': 'Church', 'lat': 41.4036, 'lon': 2.1744, 'description': 'Unfinished church by Antoni Gaudí', 'website': 'https://sagradafamilia.org'},
        {'name': 'Park Güell', 'type': 'Park', 'lat': 41.4145, 'lon': 2.1527, 'description': 'Gaudí-designed park', 'website': 'https://parkguell.barcelona'},
        {'name': 'La Rambla', 'type': 'Street', 'lat': 41.3802, 'lon': 2.1734, 'description': 'Famous pedestrian street', 'website': 'https://www.barcelona.com'},
        {'name': 'Casa Batlló', 'type': 'Building', 'lat': 41.3917, 'lon': 2.1649, 'description': 'Gaudí-designed building', 'website': 'https://www.casabatllo.es'},
        {'name': 'Gothic Quarter', 'type': 'District', 'lat': 41.3833, 'lon': 2.1767, 'description': 'Historic center of Barcelona', 'website': 'https://www.barcelona.com'},
        {'name': 'Camp Nou', 'type': 'Stadium', 'lat': 41.3809, 'lon': 2.1228, 'description': 'FC Barcelona stadium', 'website': 'https://www.fcbarcelona.com'},
        {'name': 'Montjuïc', 'type': 'Hill', 'lat': 41.3633, 'lon': 2.1647, 'description': 'Hill with parks and museums', 'website': 'https://www.barcelona.com'},
        {'name': 'Barceloneta Beach', 'type': 'Beach', 'lat': 41.3792, 'lon': 2.1894, 'description': 'Popular city beach', 'website': 'https://www.barcelona.com'},
        {'name': 'Picasso Museum', 'type': 'Museum', 'lat': 41.3851, 'lon': 2.1817, 'description': 'Museum dedicated to Picasso', 'website': 'https://www.museupicasso.bcn.cat'},
        {'name': 'Magic Fountain', 'type': 'Fountain', 'lat': 41.3711, 'lon': 2.1514, 'description': 'Colorful fountain show', 'website': 'https://www.barcelona.com'}
    ],
    'dubai': [
        {'name': 'Burj Khalifa', 'type': 'Building', 'lat': 25.1972, 'lon': 55.2744, 'description': 'World\'s tallest building', 'website': 'https://www.burjkhalifa.ae'},
        {'name': 'Dubai Mall', 'type': 'Mall', 'lat': 25.1972, 'lon': 55.2744, 'description': 'World\'s largest shopping mall', 'website': 'https://thedubaimall.com'},
        {'name': 'Palm Jumeirah', 'type': 'Island', 'lat': 25.1124, 'lon': 55.1390, 'description': 'Artificial palm-shaped island', 'website': 'https://www.palmjumeirah.ae'},
        {'name': 'Dubai Marina', 'type': 'District', 'lat': 25.0922, 'lon': 55.1387, 'description': 'Waterfront development', 'website': 'https://www.dubaimarina.ae'},
        {'name': 'Dubai Frame', 'type': 'Monument', 'lat': 25.2331, 'lon': 55.2775, 'description': 'Giant picture frame structure', 'website': 'https://www.dubaiframe.ae'},
        {'name': 'Dubai Miracle Garden', 'type': 'Garden', 'lat': 25.0585, 'lon': 55.2414, 'description': 'World\'s largest flower garden', 'website': 'https://www.dubaimiraclegarden.com'},
        {'name': 'Dubai Museum', 'type': 'Museum', 'lat': 25.2622, 'lon': 55.2972, 'description': 'Museum in Al Fahidi Fort', 'website': 'https://www.dubaiculture.gov.ae'},
        {'name': 'Dubai Opera', 'type': 'Theater', 'lat': 25.1972, 'lon': 55.2744, 'description': 'Performing arts center', 'website': 'https://www.dubaiopera.com'},
        {'name': 'Jumeirah Beach', 'type': 'Beach', 'lat': 25.2285, 'lon': 55.2867, 'description': 'Popular public beach', 'website': 'https://www.visitdubai.com'},
        {'name': 'Dubai Fountain', 'type': 'Fountain', 'lat': 25.1972, 'lon': 55.2744, 'description': 'World\'s largest choreographed fountain', 'website': 'https://www.dubaifountain.com'}
    ]
}

class SubjectiveDistanceVisualizer:
    def __init__(self):
        self.map = folium.Map(location=[0, 0], zoom_start=2, tiles="OpenStreetMap")
        self.perceived_distances = {}
        self.actual_distances = {}
    
    def add_location_pair(self, loc1, loc2, perceived_dist):
        c1 = (loc1['lat'], loc1['lng'])
        c2 = (loc2['lat'], loc2['lng'])
        
        actual_distance = geopy.distance.distance(c1, c2).kilometers
        
        id_for_pairing = f"{loc1['name']}-{loc2['name']}"
        self.perceived_distances[id_for_pairing] = perceived_dist
        self.actual_distances[id_for_pairing] = actual_distance
        
        # Add markers for locations
        folium.Marker(
            c1,
            popup=loc1['name']
        ).add_to(self.map)
        
        folium.Marker(
            c2,
            popup=loc2['name']
        ).add_to(self.map)
        
        self._draw_connection(c1, c2, perceived_dist, actual_distance)
        
    def _draw_connection(self, c1, c2, perceived_dist, actual_distance):
        ratio = perceived_dist / actual_distance
        
        if ratio > 1.2:
            color = 'red'
        elif ratio < 0.8:
            color = 'blue'
        else:
            color = 'green'
            
        folium.PolyLine(
            locations=[c1, c2],
            weight=2,
            color=color,
            popup=f'Perceived: {perceived_dist:.1f}km\nActual: {actual_distance:.1f}km'
        ).add_to(self.map)

def get_city_coordinates(city_name):
    try:
        geolocator = Nominatim(user_agent="city_map_viewer")
        location = geolocator.geocode(city_name)
        if location:
            return location.latitude, location.longitude, location.address
        return None, None, None
    except (GeocoderTimedOut, GeocoderUnavailable) as e:
        print(f"Geocoding error: {e}")
        return None, None, None

def get_nearby_landmarks(lat, lng, city_name):
    try:
        city_key = city_name.lower()
        
        if city_key in MAJOR_LANDMARKS:
            landmarks = MAJOR_LANDMARKS[city_key]

            for landmark in landmarks:
                if landmark['type'] in ['Monument', 'Museum']:
                    landmark['popularity_score'] = 4
                elif landmark['type'] in ['Castle', 'Palace', 'Temple']:
                    landmark['popularity_score'] = 3
                else:
                    landmark['popularity_score'] = 2
            return landmarks
        
    
        return []
        
    except Exception as e:
        print(f"Error getting landmarks: {e}")
        return []

@app.route('/')
def index():
    return render_template('distance_visualizer.html')

@app.route('/search_city', methods=['POST'])
def search_city():
    try:
        city_name = request.form.get('city_name')
        if not city_name:
            return jsonify({'error': 'Please enter a city name'}), 400

        lat, lng, address = get_city_coordinates(city_name)
        if not lat or not lng:
            return jsonify({'error': f'Could not find coordinates for {city_name}'}), 404

        # Get nearby landmarks
        landmarks = get_nearby_landmarks(lat, lng, city_name)
        
        if not landmarks:
            return jsonify({
                'map_html': '',
                'coordinates': {'lat': lat, 'lng': lng},
                'landmarks': [],
                'error': 'No landmarks found for this city. Try New York, London, Paris, Tokyo, or Rome.'
            })
        
        # Calculate the center point of all landmarks
        lats = [landmark['lat'] for landmark in landmarks]
        lons = [landmark['lon'] for landmark in landmarks]
        center_lat = sum(lats) / len(lats)
        center_lon = sum(lons) / len(lons)
        
        # Create a map centered on the landmarks
        m = folium.Map(location=[center_lat, center_lon], zoom_start=9)
        
        # Add markers for landmarks
        for landmark in landmarks:
            popup_content = f"""
            <b>{landmark['name']}</b><br>
            Type: {landmark['type']}<br>
            {landmark['description']}<br>
            <a href="{landmark['website']}" target="_blank">Visit Website</a>
            """
            
            marker = folium.Marker(
                [landmark['lat'], landmark['lon']],
                popup=folium.Popup(popup_content, max_width=300),
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(m)
        
        return jsonify({
            'map_html': m._repr_html_(),
            'coordinates': {'lat': lat, 'lng': lng},
            'landmarks': landmarks
        })
    except Exception as e:
        print(f"Error processing request: {e}")
        return jsonify({'error': 'An error occurred while processing your request. Please try again.'}), 500

@app.route('/test_map')
def test_map():
    m = folium.Map(location=[0, 0], zoom_start=2, tiles="OpenStreetMap")
    folium.Marker([0, 0], popup="Test Marker").add_to(m)
    return render_template('map.html', map_html=m._repr_html_())

@app.route('/visualize', methods=['POST'])
def visualize():
    try:
        visualizer = SubjectiveDistanceVisualizer()
        
        loc1 = {
            'name': request.form['loc1_name'],
            'lat': float(request.form['loc1_lat']),
            'lng': float(request.form['loc1_lng'])
        }
        
        loc2 = {
            'name': request.form['loc2_name'],
            'lat': float(request.form['loc2_lat']),
            'lng': float(request.form['loc2_lng'])
        }
        
        perceived_dist = float(request.form['perceived_dist'])
        
        visualizer.add_location_pair(loc1, loc2, perceived_dist)
        
        return render_template('map.html', map_html=visualizer.map._repr_html_())
    except Exception as e:
        return str(e), 400

@app.route('/get_landmarks/<city_name>')
def get_landmarks(city_name):
    try:
        landmarks = get_nearby_landmarks(0, 0, city_name)  
        
        if not landmarks:
            return jsonify({
                'error': f'No landmarks found for {city_name}. Try New York, London, Paris, Tokyo, Rome, Sydney, Berlin, Amsterdam, Barcelona, or Dubai.'
            }), 404
        
        return jsonify({
            'landmarks': landmarks
        })
    except Exception as e:
        print(f"Error getting landmarks: {e}")
        return jsonify({'error': 'An error occurred while fetching landmarks'}), 500

@app.route('/store_quiz_result', methods=['POST'])
def store_quiz_result():
    """Store quiz results for analysis."""
    try:
        data = request.get_json()
        result = {
            'city': data.get('city'),
            'landmark1': data.get('landmark1'),
            'landmark2': data.get('landmark2'),
            'perceived_distance': float(data.get('perceived_distance')),
            'actual_distance': float(data.get('actual_distance')),
            'unit': data.get('unit'),
            'timestamp': datetime.now().isoformat()
        }
        
        # Convert to km if needed
        if result['unit'] == 'mi':
            result['perceived_distance'] *= 1.60934
            result['actual_distance'] *= 1.60934
        
        quiz_results.append(result)
        
        # Keep only last 100 results to prevent memory issues
        if len(quiz_results) > 100:
            quiz_results.pop(0)
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error storing quiz result: {e}")
        return jsonify({'error': 'Failed to store result'}), 500

@app.route('/get_distortion_analysis')
def get_distortion_analysis():
    """Generate distortion analysis visualizations."""
    try:
        if not quiz_results:
            return jsonify({
                'error': 'No quiz results available. Please complete some distance quizzes first.'
            }), 404
        
        # Create DataFrame for analysis
        df = pd.DataFrame(quiz_results)
        
        # Calculate distortion metrics
        df['distortion_ratio'] = df['perceived_distance'] / df['actual_distance']
        df['distortion_percentage'] = ((df['perceived_distance'] - df['actual_distance']) / df['actual_distance']) * 100
        df['absolute_error'] = abs(df['perceived_distance'] - df['actual_distance'])
        
        # Generate visualizations
        graphs = {}
        
        # Perceived vs Actual Distance Scatter Plot
        plt.figure(figsize=(10, 8))
        plt.scatter(df['actual_distance'], df['perceived_distance'], alpha=0.6, s=50)
        
        # Add perfect prediction line
        max_dist = max(df['actual_distance'].max(), df['perceived_distance'].max())
        plt.plot([0, max_dist], [0, max_dist], 'r--', alpha=0.7, label='Perfect Prediction')
        
        plt.xlabel('Actual Distance (km)')
        plt.ylabel('Perceived Distance (km)')
        plt.title('Perceived vs Actual Distances')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Save to base64
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        graphs['scatter_plot'] = base64.b64encode(img_buffer.getvalue()).decode()
        plt.close()
        
        # Distortion Ratio Distribution
        plt.figure(figsize=(10, 6))
        plt.hist(df['distortion_ratio'], bins=20, alpha=0.7, edgecolor='black')
        plt.axvline(x=1, color='red', linestyle='--', label='Perfect Prediction (Ratio = 1)')
        plt.xlabel('Distortion Ratio (Perceived/Actual)')
        plt.ylabel('Frequency')
        plt.title('Distribution of Distance Distortion Ratios')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        graphs['distortion_histogram'] = base64.b64encode(img_buffer.getvalue()).decode()
        plt.close()
        
        # Distortion Heatmap by City
        if len(df['city'].unique()) > 1:
            plt.figure(figsize=(12, 8))
            city_distortion = df.groupby('city')['distortion_ratio'].mean().sort_values()
            
            # Create heatmap data
            heatmap_data = df.pivot_table(
                values='distortion_ratio', 
                index='city', 
                columns=None, 
                aggfunc='mean'
            ).fillna(0)
            
            sns.heatmap(heatmap_data, annot=True, cmap='RdYlBu_r', center=1, 
                       cbar_kws={'label': 'Average Distortion Ratio'})
            plt.title('Distance Distortion Heatmap by City')
            plt.ylabel('City')
            
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            graphs['city_heatmap'] = base64.b64encode(img_buffer.getvalue()).decode()
            plt.close()
        
        # Error Analysis
        plt.figure(figsize=(12, 8))
        
        # Subplot 1: Absolute Error vs Actual Distance
        plt.subplot(2, 2, 1)
        plt.scatter(df['actual_distance'], df['absolute_error'], alpha=0.6)
        plt.xlabel('Actual Distance (km)')
        plt.ylabel('Absolute Error (km)')
        plt.title('Absolute Error vs Actual Distance')
        plt.grid(True, alpha=0.3)
        
        # Subplot 2: Percentage Error vs Actual Distance
        plt.subplot(2, 2, 2)
        plt.scatter(df['actual_distance'], df['distortion_percentage'], alpha=0.6)
        plt.xlabel('Actual Distance (km)')
        plt.ylabel('Percentage Error (%)')
        plt.title('Percentage Error vs Actual Distance')
        plt.grid(True, alpha=0.3)
        
        # Subplot 3: Box plot of distortion ratios by city
        plt.subplot(2, 2, 3)
        df.boxplot(column='distortion_ratio', by='city', ax=plt.gca())
        plt.title('Distortion Ratio Distribution by City')
        plt.suptitle('')  # Remove default title
        plt.grid(True, alpha=0.3)
        
        # Subplot 4: Time series of accuracy improvement
        plt.subplot(2, 2, 4)
        df_sorted = df.sort_values('timestamp')
        plt.plot(range(len(df_sorted)), df_sorted['distortion_ratio'], marker='o', alpha=0.7)
        plt.axhline(y=1, color='red', linestyle='--', alpha=0.7)
        plt.xlabel('Quiz Attempt')
        plt.ylabel('Distortion Ratio')
        plt.title('Learning Progress Over Time')
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        graphs['error_analysis'] = base64.b64encode(img_buffer.getvalue()).decode()
        plt.close()
        
        # Calculate statistics
        stats = {
            'total_quizzes': len(df),
            'average_distortion_ratio': df['distortion_ratio'].mean(),
            'median_distortion_ratio': df['distortion_ratio'].median(),
            'std_distortion_ratio': df['distortion_ratio'].std(),
            'average_absolute_error': df['absolute_error'].mean(),
            'average_percentage_error': df['distortion_percentage'].mean(),
            'overestimation_rate': (df['distortion_ratio'] > 1).mean() * 100,
            'underestimation_rate': (df['distortion_ratio'] < 1).mean() * 100,
            'accurate_rate': ((df['distortion_ratio'] >= 0.9) & (df['distortion_ratio'] <= 1.1)).mean() * 100,
            'cities_tested': df['city'].nunique(),
            'landmark_pairs_tested': len(df[['landmark1', 'landmark2']].drop_duplicates())
        }
        
        return jsonify({
            'graphs': graphs,
            'stats': stats,
            'recent_results': df.tail(10).to_dict('records')
        })
        
    except Exception as e:
        print(f"Error generating distortion analysis: {e}")
        return jsonify({'error': 'Failed to generate analysis'}), 500

@app.route('/clear_quiz_results', methods=['POST'])
def clear_quiz_results():
    """Clear all stored quiz results."""
    global quiz_results
    quiz_results.clear()
    return jsonify({'success': True})

@app.route('/generate_mock_data', methods=['POST'])
def generate_mock_data():
    """Generate mock quiz data for testing the distortion analysis."""
    global quiz_results
    
    # Clear existing data
    quiz_results.clear()
    
    # Mock cities and landmarks
    mock_cities = ['New York', 'London', 'Paris', 'Tokyo', 'Rome']
    mock_landmarks = {
        'New York': ['Statue of Liberty', 'Central Park', 'Empire State Building', 'Times Square', 'Brooklyn Bridge'],
        'London': ['Big Ben', 'British Museum', 'Tower of London', 'Buckingham Palace', 'London Eye'],
        'Paris': ['Eiffel Tower', 'Louvre Museum', 'Notre-Dame Cathedral', 'Arc de Triomphe', 'Champs-Élysées'],
        'Tokyo': ['Tokyo Skytree', 'Senso-ji Temple', 'Tokyo Imperial Palace', 'Meiji Shrine', 'Shibuya Crossing'],
        'Rome': ['Colosseum', 'Vatican Museums', 'Trevi Fountain', 'Pantheon', 'Roman Forum']
    }
    
    # Generate realistic mock data with systematic biases
    import random
    from datetime import datetime, timedelta
    
    # Set seed for reproducible results
    random.seed(2024)
    
    # Generate 50 mock quiz results
    for i in range(50):
        city = random.choice(mock_cities)
        landmarks = mock_landmarks[city]
        
        # Randomly select two different landmarks
        landmark1, landmark2 = random.sample(landmarks, 2)
        
        # Generate realistic actual distances (0.5 to 15 km)
        actual_distance = random.uniform(0.5, 15.0)
        
        # Generate perceived distance with systematic biases
        # People tend to overestimate short distances and underestimate long distances
        if actual_distance < 2:
            # Overestimate short distances by 20-50%
            bias_factor = random.uniform(1.2, 1.5)
        elif actual_distance > 10:
            # Underestimate long distances by 10-30%
            bias_factor = random.uniform(0.7, 0.9)
        else:
            # Mixed bias for medium distances
            bias_factor = random.uniform(0.8, 1.3)
        
        # Add some random noise
        noise = random.uniform(0.9, 1.1)
        perceived_distance = actual_distance * bias_factor * noise
        
        # Generate timestamp (spread over the last 7 days)
        days_ago = random.uniform(0, 7)
        timestamp = datetime.now() - timedelta(days=days_ago)
        
        result = {
            'city': city,
            'landmark1': landmark1,
            'landmark2': landmark2,
            'perceived_distance': round(perceived_distance, 1),
            'actual_distance': round(actual_distance, 1),
            'unit': 'km',
            'timestamp': timestamp.isoformat()
        }
        
        quiz_results.append(result)
    
    return jsonify({
        'success': True,
        'message': f'Generated {len(quiz_results)} mock quiz results',
        'cities': list(set([r['city'] for r in quiz_results])),
        'total_landmarks': len(set([r['landmark1'] for r in quiz_results] + [r['landmark2'] for r in quiz_results]))
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
