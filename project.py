from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
app = Flask(__name__)

# Routes
# Show catalog
@app.route('/')
@app.route('/catalog')
def showCatalog():
    return render_template('catalog.html')

# Create a new category
@app.route('/category/new')
def newCategory():
    return render_template('newCategory.html')

# Edit a category
@app.route('/category/category_id/edit')
def editCategory():
    return render_template('editCategory.html')

# Delete a category
@app.route('/category/category_id/delete')
def deleteCategory():
    return render_template('deleteCategory.html')

# Show a category
@app.route('/category/category_id')
def showCategory():
    return render_template('category.html')

# Create a new item
@app.route('/item/category_id/new')
def newItem():
    return render_template('newItem.html')

# Edit an item
@app.route('/item/category_id/item_id/edit')
def editItem():
    return render_template('editItem.html')

# Delete an item
@app.route('/item/category_id/item_id/delete')
def deleteItem():
    return render_template('deleteItem.html')

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)
