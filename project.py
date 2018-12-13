from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
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
DBSession = sessionmaker(bind = engine)
session = DBSession()

# Routes
# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

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
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
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

    login_session['username'] = data['name']
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
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
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
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

# DISCONNECT - Revoke a current user's token and reset their login_session

@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s' % access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# Show catalog
@app.route('/')
@app.route('/catalog')
def showCatalog():
    # Show all the categories in the catelog
    categories = session.query(magicCategory).all()
    # Set page title
    title = 'Magic Catalog'
    # If there are no categories, display a message
    message = ''
    if not categories:
        message = "There are no magic categories..."



    # Check to see if user logged in
    if 'username' not in login_session:
        return render_template('publicCatalog.html', categories = categories, message = message, title = title)
    else:
        # add user picture
        picture = login_session['picture']
        return render_template('catalog.html', categories = categories, message = message, title = title, picture = picture)

# Create a new category
@app.route('/category/new', methods=['GET', 'POST'])
def newCategory():
    #Check to see if user is logged if user is logged in
    if 'username' not in login_session:
        return redirect('/login')

    # Set page title
    title = 'New Magic Category'

    # add user picture
    picture = login_session['picture']

    if request.method == 'POST':
        newCategory = magicCategory(name = request.form['name'], user_id=login_session['user_id'])
        session.add(newCategory)
        flash('New Category %s Successfully Created' % newCategory.name)
        session.commit()
        return redirect(url_for('showCategory', category_id = newCategory.id))
    else:
        return render_template('newCategory.html', title = title, picture = picture)

# Edit a category
@app.route('/category/<int:category_id>/edit', methods=['GET', 'POST'])
def editCategory(category_id):
    editedCategory = session.query(magicCategory).filter_by(id = category_id).one()

    # Set page title
    title = ('Edit %s' % editedCategory.name)

    # add user picture
    picture = login_session['picture']

    #Check to see if user is logged if user is logged in
    if 'username' not in login_session:
        return redirect('/login')

    # Ensure only creator can edit category
    if editedCategory.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to edit this category. Please create your own category in order to edit.');}</script><body onload='myFunction()'>"

    if request.method == 'POST':
        if request.form['name']:
            editedCategory.name = request.form['name']
        session.add(editedCategory)
        flash('%s Successfully Edited' % editedCategory.name)
        session.commit()
        return redirect(url_for('showCatalog'))
    else:
        return render_template('editCategory.html', category = editedCategory, title = title, picture = picture)

# Delete a category
@app.route('/category/<int:category_id>/delete', methods=['GET', 'POST'])
def deleteCategory(category_id):
    deletionCategory = session.query(magicCategory).filter_by(id = category_id).one()

    # Set page title
    title = ('Delete %s' % deletionCategory.name)

    # add user picture
    picture = login_session['picture']

    #Check to see if user is logged if user is logged in
    if 'username' not in login_session:
        return redirect('/login')

    # Ensure only creator can delete category
    if deletionCategory.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to delete this category. Please create your own category in order to delete.');}</script><body onload='myFunction()'>"

    if request.method == 'POST':
        session.delete(deletionCategory)
        flash('%s Successfully Deleted' % deletionCategory.name)
        session.commit()
        return redirect(url_for('showCatalog'))
    else:
        return render_template('deleteCategory.html', category = deletionCategory, title = title, picture = picture)

# Show a category
@app.route('/category/<int:category_id>')
def showCategory(category_id):
    category = session.query(magicCategory).filter_by(id = category_id).one()
    creator = getUserInfo(magicCategory.user_id)
    items = session.query(Item).filter_by(category_id = category_id).all()

    # Set page title
    title = ('%s' % category.name)



    # If there are no items in the category, display a message
    message = ''
    if not items:
        message = "Your category doesn't have any items yet"

    #Check to see if user is logged if user is logged in
    if 'username' not in login_session or creator.id != login_session['user_id']:
        return render_template('publicCategory.html', items = items, category = category, message = message, creator=creator, title = title)
    else:
        # add user picture
        picture = login_session['picture']
        return render_template('category.html', items = items, category = category, message = message, creator=creator, title = title, picture = picture)

# Create a new item
@app.route('/item/<int:category_id>/new', methods=['GET', 'POST'])
def newItem(category_id):
    category = session.query(magicCategory).filter_by(id = category_id).one()

    # Set page title
    title = ('New Magic Item')

    # add user picture
    picture = login_session['picture']

    #Check to see if user is logged if user is logged in
    if 'username' not in login_session:
        return redirect('/login')

    # Ensure only category creator can add items
    if login_session['user_id'] != category.user_id:
        return "<script>function myFunction() {alert('You are not authorized to add items to this category. Please create your own category in order to add items.');}</script><body onload='myFunction()'>"

    if request.method == 'POST':
        newItem = Item(name = request.form['name'], price = request.form['price'], description = request.form['description'], category_id = category_id, user_id=category.user_id)
        session.add(newItem)
        flash('%s Successfully Created' % newItem.name)
        session.commit()
        return redirect(url_for('showCategory', category_id = category_id))
    else:
        return render_template('newItem.html', category = category, title = title, picture = picture)

# Edit an item
@app.route('/item/<int:category_id>/<int:item_id>/edit', methods=['GET', 'POST'])
def editItem(category_id, item_id):
    category = session.query(magicCategory).filter_by(id = category_id).one()
    editedItem = session.query(Item).filter_by(id = item_id).one()

    # Set page title
    title = ('Edit %s' % editedItem.name)

    # add user picture
    picture = login_session['picture']

    #Check to see if user is logged if user is logged in
    if 'username' not in login_session:
        return redirect('/login')

    # Ensure only category creator can edit items
    if login_session['user_id'] != category.user_id:
        return "<script>function myFunction() {alert('You are not authorized to edit items this category. Please create your own category in order to edit items.');}</script><body onload='myFunction()'>"

    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['price']:
            editedItem.price = request.form['price']
        session.add(editedItem)
        flash('%s Successfully Edited' % editedItem.name)
        session.commit()
        return redirect(url_for('showCategory', category_id = category_id))
    else:
        return render_template('editItem.html', item = editedItem, category_id = category_id, title = title, picture = picture)

# Delete an item
@app.route('/item/<int:category_id>/<int:item_id>/delete', methods=['GET', 'POST'])
def deleteItem(category_id, item_id):
    category = session.query(magicCategory).filter_by(id = category_id).one()
    deletionItem = session.query(Item).filter_by(id = item_id).one()

    # Set page title
    title = ('Delete %s' % deletionItem.name)

    # add user picture
    picture = login_session['picture']

    #Check to see if user is logged if user is logged in
    if 'username' not in login_session:
        return redirect('/login')

    # Ensure only category creator can delete items
    if login_session['user_id'] != category.user_id:
        return "<script>function myFunction() {alert('You are not authorized to delete items in this category. Please create your own category in order to delete items.');}</script><body onload='myFunction()'>"

    if request.method == 'POST':
        session.delete(deletionItem)
        flash('%s Successfully Deleted' % deletionItem.name)
        session.commit()
        return redirect(url_for('showCategory', category_id = category.id))
    else:
        return render_template('deleteItem.html', item = deletionItem, category_id = category.id, title = title, picture = picture)

# Catalog API Endpoint
@app.route('/catalog/JSON')
def catalogJSON():
    categories = session.query(magicCategory).all()
    return jsonify(magicCategory=[i.serialize for i in categories])

# Category API Endpoint
@app.route('/category/<int:category_id>/JSON')
def categoryJSON(category_id):
    category = session.query(magicCategory).filter_by(id = category_id).one()
    items = session.query(Item).filter_by(category_id = category_id).all()
    return jsonify(Item=[i.serialize for i in items])


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)
