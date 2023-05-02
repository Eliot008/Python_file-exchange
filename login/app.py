# Store this code in 'app.py' file

from ssl import SSLSession
from flask import Flask, render_template, request, redirect, url_for, session, send_file
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename
from datetime import datetime
import MySQLdb.cursors
import re
import os
import subprocess
 
app = Flask(__name__)
 
 
app.secret_key = 'your secret key'
 
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'test2'
 
mysql = MySQL(app)
 
@app.route('/')
@app.route('/login', methods =['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = % s AND password = % s', (username, password, ))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            #app.jinja_env.globals.update(session['username'])
            msg = 'Logged in successfully !'
            return redirect(url_for("uploadfile"))
        else:
            msg = 'Incorrect username / password !'
    return render_template('login.html', msg = msg)
 
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))
 
@app.route('/register', methods =['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form :
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = % s', (username, ))
        account = cursor.fetchone()
        if account:
            msg = 'Account already exists !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address !'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers !'
        elif not username or not password or not email:
            msg = 'Please fill out the form !'
        else:
            cursor.execute('INSERT INTO accounts VALUES (NULL, % s, % s, % s)', (username, password, email, ))
            mysql.connection.commit()
            msg = 'You have successfully registered !'
    elif request.method == 'POST':
        msg = 'Please fill out the form !'
    return render_template('register.html', msg = msg)
  


upload_folder = "uploads/"
if not os.path.exists(upload_folder):
   os.mkdir(upload_folder)

app.config['UPLOAD_FOLDER'] = upload_folder

@app.route('/upload', methods = ['GET', 'POST'])
def uploadfile():
    if session['loggedin'] == True:
        file_successfully = ''
        if request.method == 'POST': # check if the method is post
            f = request.files['file'] # get the file from the files object
            # Saving the file in the required destination
            f.save(os.path.join(app.config['UPLOAD_FOLDER'] ,secure_filename(f.filename))) # this will secure the file
            file_name = f.filename
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('INSERT INTO filedownload VALUES (NULL, % s)', (file_name, ))
            mysql.connection.commit()
            file_successfully = 'file uploaded successfully' # Display this message after uploading
        else:
            file_successfully = 'file uploaded error or the file is not selected'
        
        cursor2 = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor2.execute('''SELECT id_file, filename FROM filedownload''')
        fileNameID = cursor2.fetchall()
        
        return render_template('upload.html', file_successfully=file_successfully, fileNameID = fileNameID)

 
@app.route('/download/<upload_id>')
def download(upload_id):
    if session['loggedin'] == True:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT filename FROM filedownload WHERE id_file = % s', (upload_id, ))
        file_table = cursor.fetchone()
        download_name=file_table['filename']
        all_path_download_file = os.path.join(app.config['UPLOAD_FOLDER'], download_name)
        mysql.connection.commit()
        return send_file(all_path_download_file, as_attachment=True )

@app.route('/comment/<post_id>')
def comment_postid(post_id):
    if session['loggedin'] == True:
        fid=post_id
        return render_template('comment.html', fid=fid)

@app.route('/comment', methods =['GET', 'POST'])
def comment():
    if session['loggedin'] == True:
        message = request.form['message']
        uid = request.form['uid']
        fid = request.form['fid']
        date = datetime.now()
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('INSERT INTO comment VALUES (NULL, % s, % s, % s, % s)', (uid, fid, message, date))
        mysql.connection.commit()
        return render_template('comment.html')

@app.route('/show_comment/<post_id>')
def show_commentid(post_id):
    if session['loggedin'] == True:
        fid = post_id
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('''SELECT uid, date, message FROM comment WHERE fid = %s''', (fid, ))
        data = cursor.fetchall()
        return render_template('showcomment.html', data=data)

@app.route('/shell', methods =['GET', 'POST'])
def shell():
    if session['loggedin'] == True and session['username'] == 'Admin':
        return render_template('shell.html')

@app.route('/shellrun', methods =['GET', 'POST'])
def shellrun():
    if session['username'] == 'Admin':
        command = request.form['command']
        command_output = subprocess.check_output(command, shell=True)
        return render_template('shell.html', command_output=command_output)