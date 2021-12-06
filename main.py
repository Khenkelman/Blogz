from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
from hashutils import make_pw_hash, check_pw_hash

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:letsmingle@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'dfh7q9DK1*d6'

class Blog(db.Model):
    
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(100))
    body = db.Column(db.String(5000))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, body, owner):
        self.title = title
        self.body = body
        self.owner = owner

class User(db.Model):
    
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(100), unique = True)
    pw_hash = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref = 'owner')

    def __init__(self, username, password):
        self.username = username
        self.pw_hash = make_pw_hash(password)


@app.before_request
def require_login():
    allowed_routes = ['login', 'list_blogs', 'index', 'signup', 'static', 'logout']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')

@app.route('/signup', methods=["POST", "GET"])
def signup():
    if request.method == "GET":
        return render_template('signup.html', page_title="signup")

    username = request.form["username"]
    password = request.form["password"]
    verify = request.form["verify"]
    user = User.query.filter_by(username=username).first()

    if username == "":
        username_error = "Name field cannot be blank"
    elif len(username) < 3:
        username_error = "Name must be at least three characters long"
    elif user: 
        username_error = "That username already exists.  Enter a different username."
    else:
        username_error = ""

    if password == "" and not user: 
        password_error = "Password field cannot be blank"
    elif len(password) < 3 and not user: 
        password_error = "Password must be at least three characters long"
    else:
        password_error = ""

    if verify == "" and not user: 
        verify_error = "Verify Password field cannot be blank"
    elif verify != password and not user: 
        verify_error = "Passwords do not match"
    else:
        verify_error = ""

    if not username_error and not password_error and not verify_error:
        if request.method == "POST":
            new_user = User(username, password)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = username
            return redirect('/newpost')
    else:
        return render_template('signup.html', page_title = "signup", username = username, username_error = username_error, 
            password_error = password_error, verify_error = verify_error)
    

@app.route('/login', methods=["POST", "GET"])
def login(): 
    if request.method == "GET":
        return render_template('login.html', page_title="login")

    username = request.form["username"]
    password = request.form["password"]
    user = User.query.filter_by(username=username).first()

    if username == "":
        username_error = "name field cannot be blank"
    elif not user: 
        username_error = "user name not registered"
    else:        
        username_error = ""

    if password == "" and user: 
        password_error = "password cannot be blank" 
    elif user: 
        if not check_pw_hash(password, user.pw_hash):
            password_error = "incorrect password"
        else:
            password_error = ""
    elif not user: 
        password_error = ""
    
    if username_error == "" and  password_error == "":
        if request.method == 'POST':
            if user and check_pw_hash(password, user.pw_hash):
                session['username'] = username
                flash("logged in")
                return redirect('/newpost') 

    else:
        return render_template('login.html', page_title = "login", username = username, 
            username_error = username_error, password_error = password_error)



@app.route('/', methods=["POST", "GET"])
def index():
    users = User.query.all()
    return render_template('index.html', page_title = "bloggers", users = users)
    
@app.route('/logout')
def logout():
    if session:
        del session['username']
        flash("logged out")
    return redirect('/blog')

@app.route('/blog', methods=["POST", "GET"])
def list_blogs():
    entries = Blog.query.all()
    
    if "id" in request.args:
        id = request.args.get('id')
        entry = Blog.query.get(id)
        
        return render_template('entries.html', page_title="blog-post", title = entry.title, body = entry.body, owner = entry.owner)

    if "user" in request.args:
        owner_id = request.args.get('user')
        userEntries = Blog.query.filter_by(owner_id=owner_id)
        username = User.query.get(owner_id)

        return render_template('singleUser.html', page_title = "user contributions", userEntries = userEntries, user = username)

    return render_template('posts.html', page_title="blog", entries = entries)


@app.route('/newpost', methods=["POST", "GET"])
def add_entry():
    
    if request.method == "GET":
        return render_template('newpost.html', page_title="blog")

    title = request.form["title"]
    body = request.form["body"]

    if title == "":
        title_error = "Blog entry must have a title."
    else:
        title_error = "" 

    if body == "":
        body_error = "Blog entry must have content."
    elif len(body) > 5000:
        body_error = "Blog entry cannot be more than 5000 characters long."
    else:
        body_error = ""
    
    if not title_error and not body_error:
        if request.method == "POST":
            owner = User.query.filter_by(username =session['username']).first()
            new_entry = Blog(title, body, owner) 
            db.session.add(new_entry)
            db.session.commit()
        
        return render_template('entries.html', page_title = "confirmation", title = title, body = body, owner = owner)
    else:
        return render_template('newpost.html', page_title = "blog", title = title, 
            title_error = title_error, body = body, body_error = body_error)

if __name__ == '__main__':
    app.run()