#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from config import SQLALCHEMY_DATABASE_URI
import json
import dateutil.parser
import babel
from datetime import datetime, timezone
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)


#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#


class Show(db.Model):
    __tablename__ = 'Show'

    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey(
        'Artist.id'), nullable=False)
    start_time = db.Column(db.DateTime())

    def __repr__(self):
        return '<Show {self.id} {self.name}>'


class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(200))
    seeking_talent = db.Column(db.Boolean, default=True)
    seeking_description = db.Column(db.String(250))
    shows = db.relationship('Show', backref='venue', lazy=True)

    def __repr__(self):
        return f'<Venue {self.id} {self.name}>'


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(200))
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(250))
    shows = db.relationship('Show', backref='artist', lazy=True)

    def __repr__(self):
        return f'<Artist {self.id} {self.name}>'


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(value, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    areas = db.session.query(Venue.city, Venue.state).distinct()
    data = []
    for area in areas:
        venues = Venue.query.filter_by(
            state=area.state).filter_by(city=area.city).all()
        venue_data = []
        for venue in venues:
            venue_data.append({
                'id': venue.id,
                'name': venue.name,
                'num_upcoming_shows': len(list(filter(lambda x: x.start_time > datetime.utcnow(), venue.shows)))
            })
        data.append({
            'city': area.city,
            'state': area.state,
            'venues': venue_data
        })
    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_str = request.form.get('search_term')
    venue_search = Venue.query.filter(
        Venue.name.ilike('%{}%'.format(search_str)))
    venue_list = list(venue_search)
    response = {
        "count": len(venue_list),
        "data": venue_list
    }
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''), venue_query=Venue.query.filter(
        Venue.name.ilike('%{}%'.format('search_term'))))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    form = VenueForm(request.form)
    genres = form.genres.data
    now = datetime.utcnow()
    venue = Venue.query.get(venue_id)
    venue.upcoming_shows_count = db.session.query(Show).join(Artist, Show.artist_id == Artist.id).join(Venue, Show.venue_id == Venue.id).filter(
        Show.venue_id == venue_id, Show.start_time >= now).count()
    venue.upcoming_shows = db.session.query(Show).join(Artist, Show.artist_id == Artist.id).join(Venue, Show.venue_id == Venue.id).add_columns(
        Artist.name.label("artist_name"), Show.start_time, Show.artist_id).filter(Show.venue_id == venue_id, Show.start_time >= now).all()
    venue.past_shows_count = db.session.query(Show).join(Artist, Show.artist_id == Artist.id).filter(
        Show.venue_id == venue_id,  Show.start_time < now).count()
    venue.past_shows = db.session.query(Show).join(Artist, Show.artist_id == Artist.id).add_columns(
        Artist.name.label("artist_name"), Show.start_time, Show.artist_id).filter(Show.venue_id == venue_id,  Show.start_time < now).all()
    return render_template('pages/show_venue.html', form=form, venue=venue)


#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    genres = form.genres.data
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    try:
        new_venue = Venue(
            name=request.form.get('name'),
            city=request.form.get('city'),
            state=request.form.get('state'),
            genres=request.form.getlist('genres'),
            image_link=request.form.get('image_link'),
            facebook_link=request.form.get('facebook_link'),
            address=request.form.get('address'),
            phone=request.form.get('phone'),
            website=request.form.get('website'),
            seeking_talent=(request.form.get('seeking_talent') == 'y'),
            seeking_description=request.form.get('seeking_description')
        )
        db.session.add(new_venue)
        db.session.commit()
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except:
        error = True
        flash('An error occurred. Venue ' +
              request.form['name'] + ' could not be listed.')
        db.session.rollback()
    finally:
        db.session.close
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    try:
        Venue.query.filter_by(id=venue_id).delete()
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    return jsonify({'success': True})
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    return render_template('pages/artists.html', artists=Artist.query.all())


@app.route('/artists/search', methods=['POST'])
def search_artists():
    search_str = request.form.get('search_term')
    artist_search = Artist.query.filter(
        Artist.name.ilike('%{}%'.format(search_str)))
    artist_list = list(artist_search)
    response = {
        "count": len(artist_list),
        "data": artist_list
    }
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''), artist_query=Artist.query.filter(
        Artist.name.ilike('%{}%'.format('search_term'))))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    now = datetime.utcnow()
    artist = Artist.query.get(artist_id)
    artist.upcoming_shows_count = db.session.query(Show).join(
        Venue, Show.venue_id == Venue.id).filter(
        Show.artist_id == artist_id, Show.start_time >= now).count()
    artist.upcoming_shows = db.session.query(Show).join(
        Venue, Show.venue_id == Venue.id).add_columns(Venue.name.label("venue_name"), Show.start_time, Show.venue_id).filter(
        Show.artist_id == artist_id, Show.start_time >= now).all()
    artist.past_shows_count = db.session.query(Show).join(
        Venue, Show.venue_id == Venue.id).filter(
        Show.artist_id == artist_id, Show.start_time < now).count()
    artist.past_shows = db.session.query(Show).join(
        Venue, Show.venue_id == Venue.id).add_columns(
        Venue.name.label("venue_name"), Show.start_time, Show.venue_id).filter(Show.artist_id == artist_id, Show.start_time < now).all()
    return render_template('pages/show_artist.html', artist=artist)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = {
        "id": 4,
        "name": "Guns N Petals",
        "genres": ["Rock n Roll"],
        "city": "San Francisco",
        "state": "CA",
        "phone": "326-123-5000",
        "website": "https://www.gunsnpetalsband.com",
        "facebook_link": "https://www.facebook.com/GunsNPetals",
        "seeking_venue": True,
        "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
        "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80"
    }
    # TODO: populate form with fields from artist with ID <artist_id>
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm(obj=venue)
    venue = Venue.query.get(venue_id)
    # TODO: populate form with values from venue with ID <venue_id>
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    try:
        new_artist = Artist(
            name=request.form.get('name'),
            city=request.form.get('city'),
            state=request.form.get('state'),
            phone=request.form.get('phone'),
            genres=request.form.getlist('genres'),
            image_link=request.form.get('image_link'),
            facebook_link=request.form.get('facebook_link'),
            website=request.form.get('website'),
            seeking_venue=(request.form.get('seeking_venue') == "y"),
            seeking_description=request.form.get('seeking_description')
        )
        db.session.add(new_artist)
        db.session.commit()
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except:
        error = True
        flash('An error occurred. Artist ' +
              request.form['name'] + ' could not be listed.')
        db.session.rollback()
    finally:
        db.session.close
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # TODO: num_shows should be aggregated based on number of upcoming shows per venue.
    result = []
    shows = Show.query.join(Venue, Show.venue_id == Venue.id).join(
        Artist, Artist.id == Show.artist_id).all()
    for show in shows:
        print(show.artist.name)
        showObj = {"venue_id": show.venue_id,
                   "venue_name": show.venue.name,
                   "artist_id": show.artist_id,
                   "artist_name": show.artist.name,
                   "artist_image_link": show.artist.image_link,
                   "start_time": show.start_time
                   }
        result.append(showObj)
    form = ShowForm()
    return render_template('pages/shows.html', shows=result, form=form)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    date_time_obj = datetime.strptime(
        request.form.get('start_time'), '%Y-%m-%d %H:%M:%S')
    try:
        new_show = Show(
            venue_id=request.form.get('venue_id'),
            artist_id=request.form.get('artist_id'),
            start_time=date_time_obj,
        )
        db.session.add(new_show)
        db.session.commit()
        flash('Show was successfully listed!')
    except:
        error = True
        flash('An error occurred. Show could not be listed.')
        db.session.rollback()
    finally:
        db.session.close
    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
