from flask import Flask, render_template, request, flash, logging, session, redirect, url_for
from functools import wraps
from flask_mysqldb import MySQL
from passlib.hash import sha256_crypt
from wtforms import Form, TextAreaField, PasswordField, validators, StringField

app = Flask(__name__)

# mysql config
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'krishna1231'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# mysql init
mysql = MySQL(app)

@app.route('/')
def index():
    return render_template('home.html')
    raise NotImplementedError

@app.route("/about")
def about():
    return render_template("about.html")

@app.route('/article/<string:id>')
def article(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM articles WHERE id = %s",(id, ))
    article = cur.fetchone()
    cur.close()
    return render_template("article.html", article = article)
    raise NotImplementedError

class RegisterForm(Form):
    name = StringField('Name', validators=[validators.DataRequired(), validators.Length(min = 3, max = 25)])
    email = StringField('Email', validators=[validators.DataRequired() ,validators.Email(message = 'Invalid Email Format, Enter Again'), validators.Length(min=6, max=50)])
    username = StringField('Username', validators=[validators.DataRequired(), validators.Length(min=4, max=25)])
    password = PasswordField('Password', validators=[validators.DataRequired(), validators.Length(min=8, max=25), validators.EqualTo('confirm', message="Passwords Don't Match") ])
    confirm = PasswordField('Confirm Password')

def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please Login!!','danger')
            return redirect(url_for('login'))
    return wrap

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (name, email, username, password) VALUES (%s, %s, %s, %s)",(name, email, username, password))
        # mysql DB commit
        mysql.connection.commit()
        #close connection
        cur.close()
        flash("Thanks for Registering, You can now log in!",'success')
        return redirect(url_for('index'))
    return render_template('register.html', form = form)

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        input_password = request.form['password']
        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM users WHERE username = %s",[username])
        if result > 0:
            data = cur.fetchone()
            password = data['password']
            if sha256_crypt.verify(input_password, password):
                session['logged_in'] = True
                session['username'] = username
                cur.execute('SELECT name from users where username = %s',(username, ))
                data = cur.fetchone()
                session['name'] = data['name']
                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                app.logger.info("PASSWORDS NOT MATCHED")
                error="Invalid Password"
                return render_template('login.html', error=error)
        else:
            app.logger.info("User not found, register yourself first!!")
            error = "Username doesn't exist"
            return render_template('login.html', error=error)
    return render_template('login.html')

@app.route('/dashboard')
@is_logged_in
def dashboard():
    cur = mysql.connection.cursor()
    result = cur.execute('SELECT * from articles where author=%s',(session['name'], ))
    articles = cur.fetchall()
    cur.close()
    if result > 0:
        return render_template('dashboard.html',articles = articles)
    else:
        msg='No Articles Found'
        return render_template('dashboard.html', msg=msg)

@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash("You are now logged out, Visit Again!!",'success')
    return redirect(url_for('login'))


class ArticleForm(Form):
    title = StringField(
        'Title',
        validators=[
            validators.DataRequired(),
            validators.Length(min=2, max=50)
        ])
    body = TextAreaField(
        'Body',
        validators=[
            validators.DataRequired(),
            validators.Length(min=30)
        ])


@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method =='POST' and form.validate():
        title = form.title.data
        body = form.body.data
        cur = mysql.connection.cursor()
        author = session['name']
        cur.execute("INSERT INTO articles(title, author, body) VALUES (%s, %s, %s)",(title, author, body))
        mysql.connection.commit()
        cur.close()
        flash('Article Successfully Saved!!','success')
        return redirect(url_for('dashboard'))
    return render_template('add_article.html', form=form)

@app.route('/edit_article/<string:id>', methods = ['GET','POST'])
@is_logged_in
def edit_article(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM articles where id =%s",(id,))
    article = cur.fetchone()
    cur.close()
    form = ArticleForm(request.form)
    form.title.data = article['title']
    form.body.data = article['body']
    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']
        cur = mysql.connection.cursor()
        author = session['name']
        cur.execute("UPDATE articles SET title=%s, body=%s where id = %s",(title, body, id))
        mysql.connection.commit()
        cur.close()
        flash('Article Successfully Updated!!','success')
        return redirect(url_for('articles'))
    return render_template('edit_article.html',form = form)

@app.route("/articles")
def articles():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM articles")
    articles = cur.fetchall()
    cur.close()
    if result > 0:
        return render_template("articles.html",articles = articles)
    else:
        msg = 'No Articles found'
        return render_template("home.html", msg=msg)


@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE from articles where id = %s", [id,])
    mysql.connection.commit()
    cur.close()
    flash("Article Successfully Deleted!!", 'success')
    return redirect(url_for('articles'))


if __name__ == '__main__':
    app.secret_key = 'secret123'
    app.run()
