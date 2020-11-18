from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
import json, os
from flask_mail import Mail
from werkzeug.utils import secure_filename
import math

with open('config.json', 'r') as c:
    params = json.load(c)["params"]

app = Flask(__name__)
app.secret_key = 'super-key'
app.config['upload_file'] = params['upload_location']
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = "465",
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['user'],
    MAIL_PASSWORD = params['pwd']
)
mail = Mail(app)

if params['local_server'] == "True":
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
db = SQLAlchemy(app)


class Contact(db.Model):
    """     id, name, phone_num, msg, email, date      """

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone_num = db.Column(db.String(10), nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(20), unique=True, nullable=False)
    date = db.Column(db.String(10))

class Post(db.Model):
    """     id, name, phone_num, msg, email, date      """

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(10), nullable=False)
    img_file = db.Column(db.String(25), nullable=False)
    timestamp = db.Column(db.String(20))


@app.route('/')
def home():
    posts = Post.query.filter_by().all()
    
    # [0:params['no_of_posts']]
    last = math.floor( len(posts)/ int(params['no_of_posts']) )
    
    page = request.args.get('page')
    if( not str(page).isnumeric()):
        page = 1

    page = int(page)
    posts = posts[ (page-1) * int(params['no_of_posts']): (page-1) *int(params['no_of_posts']) + int(params['no_of_posts'])]

    if (page==1):
        prev = "#"
        nex = "/?page="+str(page+1)
    
    elif(page==last):
            prev = "/?page="+str(page-1)
            nex = "#"

    else:
        prev = "/?page="+str(page-1)
        nex  = "/?page="+str(page+1)

    
    return render_template('index.html', params=params, posts=posts, prev=prev, nex = nex)

@app.route('/about')
def about():
    return render_template('about.html', params=params)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if(request.method == 'POST'):
        """ADD ENTRY LINE TO DATABASE"""

        """     id, name, phone_num, msg, email, date      """
        
        name = request.form.get('name')
        email = request.form.get('email')
        phoneNum = request.form.get('phoneNum')
        msg = request.form.get('msg')
        # submit = request.form.get('submit')

        entry = Contact(name = name, phone_num = phoneNum, msg = msg, email= email)
        db.session.add(entry)
        db.session.commit()
        mail.send_message("Testing "+name, sender=params['user'], recipients = [email], body=msg+"\n"+str(phoneNum))
    
    return render_template('contact.html', params=params)

@app.route('/post/<string:post_slug>', methods=['GET'])
def post_route(post_slug):
    posts = Post.query.filter_by(slug=post_slug).first()
    return render_template('post.html', params=params, post=posts)

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():

    if 'user' in session and session['user'] == params['admin_user']:
        posts = Post.query.all()
        return render_template('dashboard.html', params=params, posts=posts)
        
    elif request.method == 'POST':
        uname = request.form.get('uname')
        pwd = request.form.get('pwd')
        if uname == params['admin_user']:
            if pwd == params['admin_pwd']:
                session['user'] = uname

                posts = Post.query.all()

                return render_template('dashboard.html', params=params, posts=posts)
            else:
                return render_template('login.html', params=params)
        else:
            return render_template('login.html', params=params)
    else:
        return render_template('login.html', params=params)

@app.route('/edit/<string:id>', methods=['GET', 'POST'])
def edit(id):
    if 'user' in session and session['user'] == params['admin_user']:
        if request.method == 'POST':
            req_title = request.form.get('title')
            req_content = request.form.get('content')
            req_slug = request.form.get('slug')
            req_img = request.form.get('img')

            if id == '0':
                post = Post(title=req_title, content=req_content, slug=req_slug, img_file=req_img)
                db.session.add(post)
                db.session.commit()

                redirect('/dashboard')
            else:
                post = Post.query.filter_by(id=id).first()
                post.title = req_title
                post.content = req_content
                post.slug = req_slug
                post.img_file = req_img

                db.session.commit()
                return redirect('/dashboard')


        post = Post.query.filter_by(id=id).first()
        return render_template('edit.html', params=params, post = post)
    else:
        return render_template('login.html', params=params)


@app.route('/uploader', methods=['GET', 'POST'])
def uploader():
    if 'user' in session and session['user'] == params['admin_user']:
        if request.method == 'POST':
            file = request.files['img']
            file.save(os.path.join(app.config['upload_file'], secure_filename(file.filename)))
            return "Uploaded successfully"

@app.route('/logout')
def logout():
    session.pop('user')
    return redirect('/dashboard')

@app.route('/delete/<string:id>', methods=['GET', 'POST'])
def delete(id):
    if 'user' in session and session['user'] == params['admin_user']:
        post = Post.query.filter_by(id=id).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')

if __name__ == "__main__":
    app.run(debug=True)