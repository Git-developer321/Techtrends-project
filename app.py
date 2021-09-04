import sqlite3
import logging
import sys
import os

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash, g
from werkzeug.exceptions import abort

db_connect_count = 0
title = None

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    global db_connect_count
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    db_connect_count += 1
    return connection

# Function to check whether app could connect to db
def connection_exists(connection):
     try:
        connection.cursor()
        return True
     except Exception as ex:
        return False

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post

# Function to get a title using its ID
def get_title(post_id):
    connection = get_db_connection()
    title = connection.execute('SELECT title FROM posts WHERE id = ?',
                        (post_id,)).fetchone()[0]
    connection.close()
    return title

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)

    if post is None:
      app.logger.info("404 - The requested article is not available!")
      return render_template('404.html'), 404
    else:
      title= get_title(post_id)
      app.logger.info("Article \"%s\" retrieved!", title)
      return render_template('post.html', post=post)
 

# Define the About Us page
@app.route('/about')
def about():
    app.logger.info("Accessed \"About us\" page")
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()
            
            app.logger.info("New article \"%s\" created", title)
            return redirect(url_for('index'))

    return render_template('create.html')

# Show the health of the application
@app.route('/healthz')
def healthcheck():
  connection = get_db_connection()  

  if connection_exists(connection) :
    response = app.response_class(
            response=json.dumps({"result":"OK - healthy"}),
            status=200,
            mimetype='application/json'
    )

  else :
    response = app.response_class(
            response=json.dumps({"result":"ERROR - unhealthy"}),
            status=500,
            mimetype='application/json'
    )
   
  connection.close()

  return response

# Show the metrics of the application
@app.route('/metrics')
def metrics():
    connection = get_db_connection()
    post_count = len(connection.execute('SELECT * FROM posts').fetchall())
    connection.close()
    response = app.response_class(
            response=json.dumps({"status": "success", "code": 0, "data": {"db_connection_count": db_connect_count, "post_count": post_count}}),
            status=200,
            mimetype='application/json'
    )
   
    return response

# start the application on port 3111
if __name__ == "__main__":
   
   stdout = logging.StreamHandler(sys.stdout)
   stderr = logging.StreamHandler(sys.stderr) 
   handle = [stderr, stdout]

   FORMAT = '%(asctime)s, %(message)s'
   logging.basicConfig(format=FORMAT,level=logging.DEBUG,handlers=handle)


   app.run(host='0.0.0.0', port='3111')
