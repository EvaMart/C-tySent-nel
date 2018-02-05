from flask import Flask, render_template, redirect, url_for, request, session, logging, flash, send_file
from flask_pymongo import PyMongo
import bcrypt
from bson.json_util import dumps
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
import flask
import os
from folium import plugins
import folium

app = Flask(__name__)


#Configure MongoDB database login
#app.config['MONGO_DBNAME'] = 'CitySen'
#app.config['MONGO_URI']= 'mongodb://localhost/CitySen'
app.config['MONGO_DBNAME'] = 
app.config['MONGO_URI']= 
app.config['DEBUG'] = True

mongo = PyMongo(app)

#-------- this is needed so the browser does not cached the map ------------------------------------#
# from https://ana-balica.github.io/2014/02/01/autoversioning-static-assets-in-flask/
@app.template_filter('autoversion')
def autoversion_filter(filename):
  # determining fullpath might be project specific
  fullpath = os.path.join('/home/selen/Desktop/flaskapp/updated_Eva_4feb', filename[1:])
  try:
      timestamp = str(os.path.getmtime(fullpath))
  except OSError:
      return filename
  newfilename = "{0}?v={1}".format(filename, timestamp)
  return newfilename
#------------------------------------------------------------------------------------------------#

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/login')
def login():
    if 'username' in session:
        return render_template('back_to_index.html')
    return render_template('login.html')


@app.route('/loggedin',methods=['POST'])
def loggedin():
    users = mongo.db.users
    login_user = users.find_one({'name':request.form['username']})
    if login_user:
        if bcrypt.hashpw(request.form['pass'].encode('utf-8'),login_user['password'].encode('utf-8')) == login_user['password'].encode('utf-8'):
            session['username'] = request.form['username']
            return redirect(url_for('index'))
    return render_template('login.html', error = error)




@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        users = mongo.db.users
        existing_user = users.find_one({'name':request.form['username']})
        if existing_user is None:
            hashpass = bcrypt.hashpw(request.form['pass'].encode('utf-8'), bcrypt.gensalt())
            users.insert({'name':request.form['username'],
                          'password':hashpass,
                          'email' : request.form['mail'],
                          'age':request.form['age'],
                          'status':request.form['status']})
            session['username'] = request.form['username']
            flash('You are now registered and can log in', 'success')
            return redirect(url_for('index'))
        return render_template('sorry_exists.html')
    return render_template('register.html')


@app.route('/discussion')
def discussion():
    if 'username' in session:
        return render_template('discussion.html')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    return render_template('index.html')


@app.route('/event', methods=['GET', 'POST'])
def event():
    if 'username' in session:
        if request.method == 'POST':
            events = mongo.db.events
            events.insert({'user':session['username'],
                           'location':request.form['location'],
                           'crime':request.form['crime'],
                           'layer':request.form['layer'],
                           'date':request.form['date'],
                           'description':request.form['description']})
            flash('Event registered successfully', 'success')
            return redirect(url_for('index'))
        return render_template('event.html')
    return render_template('login.html')

#### ------ Maps generation and routing -----------------------------------------------------##

@app.route('/maps/map.html')

def show_map():
    return flask.send_file('maps/map.html')

def show_map_event():
    return flask.send_file('maps/maps_event.html')

def get_color(crime_type):
    if crime_type == 'sexual':
        return 'red'
    elif crime_type == 'robbery':
        return 'blue'
    else:
        return 'green'

def get_time_span(label):
    diction = {'all_day':[0,24], 'p1':[0,6], 'p2':[6,12], 'p3':[12,18], 'p4':[18,24]}
    return diction[label]

@app.route('/map', methods=['GET', 'POST'])
def map():
    events=mongo.db.events
    coordinates = [41.390205, 2.154007]
    layer = 'street'
    time_span = [0,24]
    map_tile = 'Stamen Toner'
    if request.method == 'POST':
        layer = flask.request.form['layer']
        time_span = get_time_span(flask.request.form['time_span'])
        print time_span
        map_tile = flask.request.form['map_tile']
    #else:
    #   layer = 'street'
    #    time_span = [0,24]
    #    map_tile = 'openstreetmap'
    folium_map = folium.Map(location=coordinates, zoom_start=12, tiles = map_tile)
    fg_sexual= folium.FeatureGroup(name='Sexual')
    folium_map.add_child(fg_sexual)
    fg_robbery= folium.FeatureGroup(name='Robbery')
    folium_map.add_child(fg_robbery)
    fg_assault= folium.FeatureGroup(name='Assault')
    folium_map.add_child(fg_assault)
    print(layer)

    for event in events.find({'layer' : layer}):
       if int(event['date']['hour']) <  time_span[1] and int(event['date']['hour']) >= time_span[0]:
            crime_type=event['crime_type']
            e_coordinates = [event['location']['coordinates'][0], event['location']['coordinates'][1]]
            popup = 'Description: <br\><br\>' + str(event['description']) + '<br\><br\> <a href="http://www.wikipedia.org" target="_parent">details</a>'
            if event['crime_type']=='sexual':
                fg_sexual.add_child(folium.Marker(location=e_coordinates, popup = popup, icon=folium.Icon(color='green')))
            elif event['crime_type'] == 'robbery':
                fg_robbery.add_child(folium.Marker(location=e_coordinates, popup = popup, icon=folium.Icon(color=get_color(crime_type))))
            else:
                fg_assault.add_child(folium.Marker(location=e_coordinates, popup = popup, icon=folium.Icon(color=get_color(crime_type))))
            #marker = folium.CircleMarker(location= [c1, c2], clustered_marker = True, popup=, fill=True)
            #marker.add_to(folium_map)
            #,popup='crime type: '+ crime_type + ' <br\><br\>' + str(event['date']) + '<br\><br\> <a href="http://www.wikipedia.org" target="_parent">wiki!</a>'
    folium.GeoJson(data = open("static/metro.json").read(),
               name='metro', style_function=lambda feature: {
        'color' : '#0a9b00',
        'weight' : 3,
        'fillOpacity' : 0.7,
        }
              ).add_to(folium_map)
    folium.LayerControl().add_to(folium_map)
    folium_map.add_child(folium.LatLngPopup())
    folium_map.save('maps/map.html')
    return render_template("maps.html", coords=coordinates)



if __name__=="__main__":
    app.secret_key = 'secret123'
    app.run(debug=True)
