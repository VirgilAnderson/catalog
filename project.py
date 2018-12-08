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
    # Show all the categories in the catelog
    categories = session.query(magicCategory).all()

    # If there are no categories, display a message
    message = ''
    if not categories:
        message = "You don't have any magic categories..."
    return render_template('catalog.html', categories = categories, message = message)

# Create a new category
@app.route('/category/new', methods=['GET', 'POST'])
def newCategory():
    if request.method == 'POST':
        newCategory = magicCategory(name = request.form['name'])
        session.add(newCategory)
        flash('New Category %s Successfully Created' % newCategory.name)
        session.commit()
        return redirect(url_for('showCategory', category_id = newCategory.id))
    else:
        return render_template('newCategory.html')

# Edit a category
@app.route('/category/<int:category_id>/edit', methods=['GET', 'POST'])
def editCategory(category_id):
    editedCategory = session.query(magicCategory).filter_by(id = category_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedCategory.name = request.form['name']
        session.add(editedCategory)
        flash('%s Successfully Edited' % editedCategory.name)
        session.commit()
        return redirect(url_for('showCatalog'))
    else:
        return render_template('editCategory.html', category = editedCategory)

# Delete a category
@app.route('/category/<int:category_id>/delete', methods=['GET', 'POST'])
def deleteCategory(category_id):
    deletionCategory = session.query(magicCategory).filter_by(id = category_id).one()
    if request.method == 'POST':
        session.delete(deletionCategory)
        flash('%s Successfully Deleted' % deletionCategory.name)
        session.commit()
        return redirect(url_for('showCatalog'))
    else:
        return render_template('deleteCategory.html', category = deletionCategory)

# Show a category
@app.route('/category/<int:category_id>')
def showCategory(category_id):
    category = session.query(magicCategory).filter_by(id = category_id).one()
    items = session.query(Item).filter_by(category_id = category_id).all()

    # If there are no items in the category, display a message
    message = ''
    if not items:
        message = "Your category doesn't have any items yet"
    return render_template('category.html', items = items, category = category, message = message)

# Create a new item
@app.route('/item/<int:category_id>/new', methods=['GET', 'POST'])
def newItem(category_id):
    category = session.query(magicCategory).filter_by(id = category_id).one()
    if request.method == 'POST':
        newItem = Item(name = request.form['name'], price = request.form['price'], description = request.form['description'], category_id = category_id)
        session.add(newItem)
        flash('%s Successfully Created' % newItem.name)
        session.commit()
        return redirect(url_for('showCategory', category_id = category_id))
    else:
        return render_template('newItem.html', category = category)

# Edit an item
@app.route('/item/<int:category_id>/<int:item_id>/edit', methods=['GET', 'POST'])
def editItem(category_id, item_id):
    category = session.query(magicCategory).filter_by(id = category_id).one()
    editedItem = session.query(Item).filter_by(id = item_id).one()
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
        return render_template('editItem.html', item = editedItem, category_id = category_id)

# Delete an item
@app.route('/item/<int:category_id>/<int:item_id>/delete', methods=['GET', 'POST'])
def deleteItem(category_id, item_id):
    category = session.query(magicCategory).filter_by(id = category_id).one()
    deletionItem = session.query(Item).filter_by(id = item_id).one()
    if request.method == 'POST':
        session.delete(deletionItem)
        flash('%s Successfully Deleted' % deletionItem.name)
        session.commit()
        return redirect(url_for('showCategory', category_id = category.id))
    else:
        return render_template('deleteItem.html', item = deletionItem, category_id = category.id)

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
