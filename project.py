# !/usr/bin/env python3

# Magic Catalog Project
# By Virgil Anderson
# December 13, 2018

from flask import (Flask,
                   render_template,
                   request,
                   redirect,
                   url_for,
                   flash,
                   jsonify)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, magicCategory, Item, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

engine = create_engine('sqlite:///magicCatalogUsers.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


# Routes
# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


# Google Login
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('User already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data.get('name', '')
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(login_session["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 150px; height: 150px;'
    output += 'border-radius: 150px; -webkit-border-radius: 150px;'
    output += '-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


# User Helper Functions
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one_or_none()
    return user if user else None


def getUserID(email):
        user = session.query(User).filter_by(email=email).one_or_none()
        return user.id if user else None


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('User not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s' % access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token='
    url += '%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['user_id']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# Show Catalog
@app.route('/')
@app.route('/catalog')
def showCatalog():
    # Show all the categories in the catelog
    c = session.query(magicCategory).all()
    # Set page title
    t = 'Magic Catalog'
    # If there are no categories, display a message
    m = ''
    if not c:
        m = "There are no magic categories..."

    # Check to see if user logged in
    if 'username' not in login_session:
        return render_template('publicCatalog.html', c=c, message=m, t=t)
    else:
        # add user picture
        p = login_session['picture']
        return render_template('catalog.html', c=c, message=m, t=t, p=p)


# Create a new category
@app.route('/category/new', methods=['GET', 'POST'])
def newCategory():
    # Check to see if user is logged if user is logged in
    if 'username' not in login_session:
        return redirect('/login')

    # Set page title
    t = 'New Magic Category'

    # add user picture
    p = login_session['picture']

    id = login_session['user_id']
    if request.method == 'POST':
        nCat = magicCategory(name=request.form['name'], user_id=id)
        session.add(nCat)
        flash('New Category %s Successfully Created' % nCat.name)
        session.commit()
        return redirect(url_for('showCategory', cat_id=nCat.id))
    else:
        return render_template('newCategory.html', t=t, p=p)


# Edit a category
@app.route('/category/<int:cat_id>/edit', methods=['GET', 'POST'])
def editCategory(cat_id):
    editCat = session.query(magicCategory).filter_by(id=cat_id).one()

    # Set page title
    t = ('Edit %s' % editCat.name)

    # Check to see if user is logged if user is logged in
    if 'username' not in login_session:
        return redirect('/login')

    # Ensure only creator can edit category
    if editCat.user_id != login_session['user_id']:
        error = "<script>function myFunction() "
        error += "{alert('You are not authorized to edit this"
        error += " category. Please create your own category "
        error += "in order to edit.');"
        error += "window.location.href = '/';}</script><body "
        error += "onload='myFunction()'>"
        return error

    if request.method == 'POST':
        if request.form['name']:
            editCat.name = request.form['name']
        session.add(editCat)
        flash('%s Successfully Edited' % editCat.name)
        session.commit()
        return redirect(url_for('showCatalog'))
    else:
        # add user picture
        p = login_session['picture']
        return render_template('eCat.html', category=editCat, t=t, p=p)


# Delete a category
@app.route('/category/<int:cat_id>/delete', methods=['GET', 'POST'])
def deleteCategory(cat_id):
    dCat = session.query(magicCategory).filter_by(id=cat_id).one()

    # Set page title
    t = ('Delete %s' % dCat.name)

    # add user picture
    p = login_session['picture']

    # Check to see if user is logged if user is logged in
    if 'username' not in login_session:
        return redirect('/login')

    # Ensure only creator can delete category
    if dCat.user_id != login_session['user_id']:
        error = "<script>function myFunction() "
        error += "{alert('You are not authorized to "
        error += "delete this category. Please create "
        error += "your own category in order to delete."
        error += "'); window.location.href = '/';"
        error += "}</script><body onload='myFunction()'>"
        return error

    if request.method == 'POST':
        session.delete(dCat)
        flash('%s Successfully Deleted' % dCat.name)
        session.commit()
        return redirect(url_for('showCatalog'))
    else:
        return render_template('dCat.html', category=dCat, t=t, p=p)


# Show a category
@app.route('/category/<int:cat_id>')
def showCategory(cat_id):
    c = session.query(magicCategory).filter_by(id=cat_id).one()
    o = getUserInfo(c.user_id)
    i = session.query(Item).filter_by(category_id=cat_id).all()

    # Set page title
    t = ('%s' % c.name)

    # If there are no items in the category, display a message
    m = ''
    if not i:
        m = "Your category doesn't have any items yet"

    # add picture if available
    if 'picture' in login_session:
        p = login_session['picture']
    else:
        p = ''

    # Check to see if user is logged if user is logged in
    if 'username' not in login_session or o.id != login_session['user_id']:
        return render_template('pCat.html', i=i, c=c, m=m, o=o, t=t, p=p)
    else:
        return render_template('cat.html', i=i, c=c, m=m, o=o, t=t, p=p)


# Create a new item
@app.route('/item/<int:cat_id>/new', methods=['GET', 'POST'])
def newItem(cat_id):
    category = session.query(magicCategory).filter_by(id=cat_id).one()

    # Set page title
    t = ('New Magic Item')

    # add user picture
    p = login_session['picture']

    # Check to see if user is logged if user is logged in
    if 'username' not in login_session:
        return redirect('/login')

    # Ensure only category creator can add items
    if login_session['user_id'] != category.user_id:
        error = "<script>function myFunction() "
        error += "{alert('You are not authorized to add "
        error += "items to this category. Please create your "
        error += "own category in order to add items.');"
        error += "window.location.href = '/';}"
        error += "</script><body onload='myFunction()'>"
        return error

    if request.method == 'POST':
        n = request.form['name']
        p = request.form['price']
        d = request.form['description']
        c = cat_id
        u = category.user_id
        nItem = Item(name=n, price=p, description=d, category_id=c, user_id=u)
        session.add(nItem)
        flash('%s Successfully Created' % nItem.name)
        session.commit()
        return redirect(url_for('showCategory', cat_id=cat_id))
    else:
        return render_template('newItem.html', category=category, t=t, p=p)


# Edit an item
@app.route('/item/<int:cat_id>/<int:item_id>/edit', methods=['GET', 'POST'])
def editItem(cat_id, item_id):
    category = session.query(magicCategory).filter_by(id=cat_id).one()
    e = session.query(Item).filter_by(id=item_id).one()

    # Set page title
    t = ('Edit %s' % e.name)

    # add user picture
    p = login_session['picture']

    # Check to see if user is logged if user is logged in
    if 'username' not in login_session:
        return redirect('/login')

    # Ensure only category creator can edit items
    if login_session['user_id'] != category.user_id:
        error = "<script>function myFunction() "
        error += "{alert('You are not authorized to edit "
        error += "items this category. Please create your own "
        error += "category in order to edit items.');}"
        error += "</script><body onload='myFunction()'>"
        return error

    if request.method == 'POST':
        if request.form['name']:
            e.name = request.form['name']
        if request.form['description']:
            e.description = request.form['description']
        if request.form['price']:
            e.price = request.form['price']
        session.add(e)
        flash('%s Successfully Edited' % e.name)
        session.commit()
        return redirect(url_for('showCategory', cat_id=cat_id))
    else:
        return render_template('eItem.html', item=e, cat_id=cat_id, t=t, p=p)


# Delete an item
@app.route('/item/<int:cat_id>/<int:item_id>/delete', methods=['GET', 'POST'])
def deleteItem(cat_id, item_id):
    category = session.query(magicCategory).filter_by(id=cat_id).one()
    d = session.query(Item).filter_by(id=item_id).one()

    # Set page title
    t = ('Delete %s' % d.name)

    # add user picture
    p = login_session['picture']

    # Check to see if user is logged if user is logged in
    if 'username' not in login_session:
        return redirect('/login')

    # Ensure only category creator can delete items
    if login_session['user_id'] != category.user_id:
        error = "<script>function myFunction() "
        error += "{alert('You are not authorized to "
        error += "delete items in this category. Please"
        error += " create your own category in order to "
        error += "delete items.');}</script><body "
        error += "onload='myFunction()'>"
        return error

    if request.method == 'POST':
        session.delete(d)
        flash('%s Successfully Deleted' % d.name)
        session.commit()
        return redirect(url_for('showCategory', cat_id=category.id))
    else:
        return render_template('dI.html', item=d, cat_id=category.id, t=t, p=p)


# Catalog API Endpoint
@app.route('/catalog/JSON')
def catalogJSON():
    categories = session.query(magicCategory).all()
    return jsonify(magicCategory=[i.serialize for i in categories])


# Category API Endpoint
@app.route('/category/<int:cat_id>/JSON')
def categoryJSON(cat_id):
    category = session.query(magicCategory).filter_by(id=cat_id).one()
    items = session.query(Item).filter_by(category_id=cat_id).all()
    return jsonify(Item=[i.serialize for i in items])


# User API Endpoint
@app.route('/user/JSON')
def userJSON():
    user = session.query(User).all()
    return jsonify(User=[i.serialize for i in user])


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
