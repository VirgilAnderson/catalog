from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
app = Flask(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, magicCategory, Item

engine = create_engine('sqlite:///magicCatalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine)
session = DBSession()

# Routes
# Show catalog
@app.route('/')
@app.route('/catalog')
def showCatalog():
    return render_template('catalog.html', categories = categories)

# Create a new category
@app.route('/category/new')
def newCategory():
    return render_template('newCategory.html')

# Edit a category
@app.route('/category/category_id/edit')
def editCategory():
    return render_template('editCategory.html', category = category)

# Delete a category
@app.route('/category/category_id/delete')
def deleteCategory():
    return render_template('deleteCategory.html', category = category)

# Show a category
@app.route('/category/category_id')
def showCategory():
    return render_template('category.html', items = items, category = category)

# Create a new item
@app.route('/item/category_id/new')
def newItem():
    return render_template('newItem.html', category = category)

# Edit an item
@app.route('/item/category_id/item_id/edit')
def editItem():
    return render_template('editItem.html', item = item)

# Delete an item
@app.route('/item/category_id/item_id/delete')
def deleteItem():
    return render_template('deleteItem.html', item = item)


# Temporary fake database
#Fake Categories
category = {'name': 'illusions', 'id': '1'}
categories = [{'name': 'illusions', 'id': '1'}, {'name': 'closeup', 'id': '2'}]

#Fake Items
item = {'name': 'ambitious card', 'description': 'card trick', 'price': '$5.00', 'id': '3'}
items = [{'name': 'ambitious card', 'description': 'card trick', 'price': '$5.00', 'id': '3'}, {'name': 'cups and balls', 'description': 'magic trick', 'price': '$15.00', 'id': '4'}]

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)
