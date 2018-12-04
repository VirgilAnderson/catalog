from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
app = Flask(__name__)

# Routes
# Show catalog
@app.route('/')
def showCatalog():
    return "This page will show all my categories"

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)
