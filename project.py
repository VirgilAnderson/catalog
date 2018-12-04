from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
app = Flask(__name__)

# Routes
# Show catalog
@app.route('/')
@app.route('/catalog')
def showCatalog():
    return "This page will show all my categories"

# Create a new category
@app.route('/category/new')
def newCategory():
    return "This page will enable you to add a new item to the category"

# Edit a category
@app.route('/category/category_id/edit')
def editCategory():
    return "This page will allow me to edit a category"

# Delete a category
@app.route('/category/category_id/delete')
def deleteCategory():
    return "This page will enable category deletion"

# Show a category
@app.route('/category/category_id')
def showCategory():
    return "This page will show all the items in a particular category"

# Create a new item
@app.route('/item/category_id/new')
def newItem():
    return "This page will enable new item creation"

# Edit an item
@app.route('/item/category_id/item_id/edit')
def editItem():
    return "This page will enable item edits"

# Delete an item
@app.route('/item/category_id/item_id/delete')
def deleteItem():
    return "This page will enable item deletion"

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)
