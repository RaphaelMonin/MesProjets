from flask import Flask, flash, redirect, render_template, request, session, abort, url_for, send_from_directory
from flask_mail import Mail, Message
from flask_socketio import SocketIO
from werkzeug.utils import secure_filename
import os
import re
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from random import choice
from string import ascii_lowercase
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
from tabledef import Utilisateur, Annee, RaphMail, Matiere, hasher, Tchat, Fichier, Like, Dislike, QuestionArchive, Commentaire, ChatPrive
engine = create_engine('sqlite:///base.db', echo=True)

ALLOWED_EXTENSIONS = set(['pdf'])

app = Flask(__name__)
socketio = SocketIO(app)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///base.db'

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

##Admin
class MyModel(ModelView):
    column_display_pk = True
    form_columns = ('username', 'password', 'email')

class MyAdminIndexView(AdminIndexView):
    def is_accessible(selfself):
        Session = sessionmaker(bind=engine)
        s = Session()
        statut = s.query(Utilisateur.status).filter(Utilisateur.username == session['username']).first()[0]
        return session.get('logged_in') and statut == 'administrateur'

db = SQLAlchemy(app)
admin = Admin(app, index_view=MyAdminIndexView())

admin.add_view(MyModel(Utilisateur, db.session))
admin.add_view(ModelView(RaphMail, db.session))
admin.add_view(ModelView(Matiere, db.session))
admin.add_view(ModelView(Tchat, db.session))
admin.add_view(ModelView(Fichier, db.session))
admin.add_view(ModelView(Like, db.session))
admin.add_view(ModelView(Dislike, db.session))

##Upload de fichiers
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

##Main
@app.route('/')
@app.route('/<string:anneeChoisi>/<string:matiereChoisi>/<string:sujetChoisi>')
def home(anneeChoisi="3TC", matiereChoisi="TSA", sujetChoisi="DS2016_s.pdf"):
    if not session.get('logged_in'):
        return redirect(url_for('do_admin_login'))
    else:
        lien = "/static/asset/" + anneeChoisi + "/" + matiereChoisi + "/" + sujetChoisi
        lien2 = "/static/asset/" + anneeChoisi + "/" + matiereChoisi + "/" + sujetChoisi[:-5] + "c.pdf"
        Session = sessionmaker(bind=engine)
        s = Session()
        annees = s.query(Annee.annee)
        id =  s.query(Fichier.id).filter(Fichier.nomMat == matiereChoisi, Fichier.nomFichier == sujetChoisi).first()[0]
        return render_template('ressources.html', myUsername=session['username'], annees=annees, lien=lien, lien2=lien2, anneeCh=anneeChoisi, matiereCh= matiereChoisi, sujetCh=sujetChoisi[:-6], idSujetCh=id)

@app.route('/login', methods=['GET','POST'])
def do_admin_login():
    if request.method == 'POST':
        POST_USERNAME = str(request.form['username'])
        POST_PASSWORD = str(request.form['password'])
        password_hash=hasher(POST_PASSWORD)

        Session = sessionmaker(bind=engine)
        s = Session()
        query = s.query(Utilisateur).filter(Utilisateur.username.in_([POST_USERNAME]), Utilisateur.password.in_([password_hash]))
        result = query.first()
        if result:
            session['logged_in'] = True
            session['username'] = POST_USERNAME
        else:
            flash('Nom d\'utilisateur ou mot de passe incorrect !')
        return redirect(url_for('home'))
    return render_template('login.html')

@app.route("/logout")
def logout():
    session['logged_in'] = False
    session.pop('username', None)
    return redirect(url_for('home'))

def messageReceived(methods=['GET', 'POST']):
    print('message was received!!!')

## Question

@socketio.on('propositionQuestion')
def handle_event(msg, methods=['GET', 'POST']):
    Session = sessionmaker(bind=engine)
    s = Session()
    id = s.query(Fichier.id).filter(Fichier.nomMat == msg['matiere'], Fichier.nomFichier == msg['sujet']+"_s.pdf").first()[0]
    new_question = QuestionArchive(username=msg['username'], question=msg["question"], annee=msg['annee'], nomMat=msg['matiere'], idFichier=id, score = 0)
    s.add(new_question)
    s.commit()

## Forum

@socketio.on('initChoixForum')
def handle_event(msg, methods=['GET', 'POST']):
    Session = sessionmaker(bind=engine)
    s = Session()
    query = s.query(QuestionArchive.question, QuestionArchive.id).filter(QuestionArchive.nomMat == msg['matiere'], QuestionArchive.idFichier == msg['sujet'])
    questions = []
    for q in query:
        questions.append([q[0], q[1]])
    socketio.emit('initChoixForumBack', questions)

@socketio.on('initForum')
def handle_my_custom_event(msg, methods=['GET', 'POST']):
    print("OOOOOOOO", msg)
    Session = sessionmaker(bind=engine)
    s = Session()
    query = s.query(Commentaire).filter(Commentaire.idQuestArch == msg['question'])
    i = 0
    if (not (query.first())):
        message = {"to": msg['user'], }
        socketio.emit('effaceForum', message)
    for q in query:
        i = i + 1
        if (i == 1):
            message = {"to": msg['question'], "id": q.id, "username": q.username,
                       "message": q.contenu, 'reference': q.refere, 'scoreLike': 0,
        'scoreDislike': 0, "init": "yes"}
        else:
            message = {"to": msg['question'], "id": q.id, "username": q.username,
                       "message": q.contenu, 'reference': q.refere, 'scoreLike': 0,
        'scoreDislike': 0, "init": "no"}
        socketio.emit('messageReceptionForum', message, callback=messageReceived)

@socketio.on('messageEmissionForum')
def handle_my_custom_event(msg, methods=['GET', 'POST']):
    print("OOOOOOO0AA", msg)
    Session = sessionmaker(bind=engine)
    s = Session()
    new_message = Commentaire(username=msg['username'], refere=msg['reference'],
                        contenu=msg["message"], idQuestArch=msg['idQuestion'])
    s.add(new_message)
    s.commit()
    query = s.query(func.max(Commentaire.id)).first()
    updated_msg = {
        'id': str(query[0]),
        'to': msg['idQuestion'],
        'message': msg['message'],
        'username': msg['username'],
        'reference': msg['reference'],
        'scoreLike': 0,
        'scoreDislike': 0,
        'init': "no",
    }
    socketio.emit('messageReceptionForum', updated_msg, callback=messageReceived)

## Chat

@socketio.on('initChoixMat')
def handle_event(msg, methods=['GET', 'POST']):
    Session = sessionmaker(bind=engine)
    s = Session()
    query = s.query(Matiere.nomMat).filter(Matiere.annee == msg["annee"], Matiere.nomMat != msg['matiere'])
    matieres = []
    for q in query:
        matieres.append(q[0])
    query = s.query(Utilisateur.annee).filter(Utilisateur.username == msg['user'])
    msg = [matieres, query[0], msg['user']]
    socketio.emit('initChoixMatBack', msg)

@socketio.on('initChoixPers')
def handle_event(msg, methods=['GET', 'POST']):
    Session = sessionmaker(bind=engine)
    s = Session()
    query = s.query(Utilisateur.username).filter(Utilisateur.annee == msg["annee"], Utilisateur.username != msg['user'])
    personnes = []
    for q in query:
        personnes.append(q[0])
    msg = [msg['user'], personnes]
    socketio.emit('initChoixPersBack', msg)

@socketio.on('init')
def handle_my_custom_event(msg, methods=['GET', 'POST']):
    Session = sessionmaker(bind=engine)
    s = Session()
    if (msg['choixChat'] == 'annee'):
        query = s.query(Tchat).filter(Tchat.type == 'annee', msg['matiere'] == Tchat.nomMat)
    else:
        query = s.query(Tchat).filter(Tchat.type == 'matiere', msg['matiere'] == Tchat.nomMat)
    i = 0
    if(not(query.first())):
        message = {"myUsername": session['username'], }
        socketio.emit('efface', message)
    for q in query:
        i = i + 1
        scoreLike = s.query(Like).filter(Like.idMessage == q.id).count()
        scoreDislike = s.query(Dislike).filter(Dislike.idMessage == q.id).count()
        if(i == 1):
            message = {"myUsername": session['username'], "matiere": q.nomMat, "id": q.id, "username": q.username, "message": q.contenu, 'reference': q.refere, "scoreLike": scoreLike, "scoreDislike": scoreDislike, "init": "yes" }
        else:
            message = {"myUsername": session['username'], "matiere": q.nomMat, "id": q.id, "username": q.username, "message": q.contenu, 'reference': q.refere, "scoreLike": scoreLike, "scoreDislike": scoreDislike, "init": "no" }
        socketio.emit('messageReception', message, callback=messageReceived)

@socketio.on('initPrive')
def handle_my_custom_event(msg, methods=['GET', 'POST']):
    Session = sessionmaker(bind=engine)
    s = Session()
    query = s.query(ChatPrive).filter(or_(and_(msg['user'] == ChatPrive.username, msg['recipient'] == ChatPrive.recipient), and_(msg['user'] == ChatPrive.recipient, msg['recipient'] == ChatPrive.username)))
    i = 0
    if(not(query.first())):
        message = {"myUsername": session['username'], }
        socketio.emit('effacePrive', message)
    for q in query:
        i = i + 1
        scoreLike = s.query(Like).filter(Like.idMessage == q.id).count()
        scoreDislike = s.query(Dislike).filter(Dislike.idMessage == q.id).count()
        if(i == 1):
            message = {"id": q.id, "recipient": q.recipient, "username": q.username, "message": q.contenu, 'reference': q.refere, "scoreLike": scoreLike, "scoreDislike": scoreDislike, "init": "yes" }
        else:
            message = {"id": q.id, "recipient": q.recipient, "username": q.username, "message": q.contenu, 'reference': q.refere, "scoreLike": scoreLike, "scoreDislike": scoreDislike, "init": "no" }
        socketio.emit('messageReceptionPrive', message, callback=messageReceived)

@socketio.on('messageEmission')
def handle_my_custom_event(msg, methods=['GET', 'POST']):
    Session = sessionmaker(bind=engine)
    s = Session()
    new_message=Tchat(username = msg['username'], nomMat = msg['matiere'], refere = msg['reference'],contenu = msg["message"],idFichier = 0, type = msg['choixChat'])
    s.add(new_message)
    s.commit()
    query = s.query(func.max(Tchat.id)).first()
    updated_msg = {
        'myUsername' : 'everybody',
        'id' : str(query[0]),
        'type' : msg['choixChat'],
        'matiere' : msg['matiere'],
        'message': msg['message'],
        'username': msg['username'],
        'reference': msg['reference'],
        'scoreLike': 0,
        'scoreDislike': 0,
        'init': "no",
    }
    socketio.emit('messageReception', updated_msg, callback=messageReceived)

@socketio.on('messageEmissionPrive')
def handle_my_custom_event(msg, methods=['GET', 'POST']):
    Session = sessionmaker(bind=engine)
    s = Session()
    new_message=ChatPrive(username = msg['username'], recipient = msg['recipient'], refere = msg['reference'], contenu = msg["message"])
    s.add(new_message)
    s.commit()
    query = s.query(func.max(ChatPrive.id)).first()
    updated_msg = {
        'id' : str(query[0]),
        'recipient' : msg['recipient'],
        'message': msg['message'],
        'username': msg['username'],
        'reference': msg['reference'],
        'scoreLike': 0,
        'scoreDislike': 0,
        'init': "no",
    }
    socketio.emit('messageReceptionPrive', updated_msg, callback=messageReceived)

@socketio.on('likeEmission')
def handle_my_custom(msg, methods=['GET', 'POST']):
    print("OOOOOOO", msg)
    Session = sessionmaker(bind=engine)
    s = Session()
    redundancy = s.query(Like).filter(Like.idMessage == msg['id'], Like.username == msg['username'], Like.type == msg['type']).first()
    if redundancy:
        return -1
    if(s.query(Dislike).filter(Dislike.idMessage == msg['id'], Dislike.username == msg['username'], Dislike.type == msg['type']).delete()):
        scoreDislike = s.query(Dislike).filter(Dislike.idMessage == msg['id'], Dislike.type == msg['type']).count()
        updated_msg = {
            'id': msg['id'],
            'scoreDislike': scoreDislike
        }
        if msg['type'] == 'gen':
            socketio.emit('dislikeReceptionGen', updated_msg, callback=messageReceived);
        if msg['type'] == 'prive':
            socketio.emit('dislikeReceptionPrive', updated_msg, callback=messageReceived);
        if msg['type'] == 'forum':
            socketio.emit('dislikeReceptionForum', updated_msg, callback=messageReceived);
    new_like = Like(username=msg['username'], idMessage=msg['id'], type = msg["type"])
    s.add(new_like)
    s.commit()
    scoreLike = s.query(Like).filter(Like.idMessage == msg['id'], Like.type == msg['type']).count()
    print("Lolololol", scoreLike)
    updated_msg = {
        'id': msg['id'],
        'scoreLike': scoreLike
    }
    if msg['type'] == 'gen':
        socketio.emit('likeReceptionGen', updated_msg, callback=messageReceived);
    if msg['type'] == 'prive':
        socketio.emit('likeReceptionPrive', updated_msg, callback=messageReceived);
    if msg['type'] == 'forum':
        socketio.emit('likeReceptionForum', updated_msg, callback=messageReceived);

@socketio.on('dislikeEmission')
def handle_my_custom(msg, methods=['GET', 'POST']):
    Session = sessionmaker(bind=engine)
    s = Session()
    redundancy = s.query(Dislike).filter(Dislike.idMessage == msg['id'], Dislike.username == msg['username'], Dislike.type == msg['type']).first()
    if redundancy:
        return -1
    if (s.query(Like).filter(Like.idMessage == msg['id'], Like.username == msg['username'], Like.type == msg['type']).delete()):
        scoreLike = s.query(Like).filter(Like.idMessage == msg['id'], Like.type == msg['type']).count()
        updated_msg = {
            'id': msg['id'],
            'scoreLike': scoreLike
        }
        if msg['type'] == 'gen':
            socketio.emit('likeReceptionGen', updated_msg, callback=messageReceived);
        if msg['type'] == 'prive':
            socketio.emit('likeReceptionPrive', updated_msg, callback=messageReceived);
        if msg['type'] == 'forum':
            socketio.emit('likeReceptionForum', updated_msg, callback=messageReceived);
    new_dislike = Dislike(username=msg['username'], idMessage=msg['id'], type = msg["type"])
    s.add(new_dislike)
    s.commit()
    scoreDislike = s.query(Dislike).filter(Dislike.idMessage == msg['id'], Dislike.type == msg['type']).count()
    updated_msg = {
        'id': msg['id'],
        'scoreDislike': scoreDislike
    }
    if msg['type'] == 'gen':
        socketio.emit('dislikeReceptionGen', updated_msg, callback=messageReceived);
    if msg['type'] == 'prive':
        socketio.emit('dislikeReceptionPrive', updated_msg, callback=messageReceived);
    if msg['type'] == 'forum':
        socketio.emit('dislikeReceptionForum', updated_msg, callback=messageReceived);

# Page Principale : choix sujet

@socketio.on('changeMat')
def handle_event(msg, methods=['GET', 'POST']):
    Session = sessionmaker(bind=engine)
    s = Session()
    query = s.query(Matiere.nomMat).filter(Matiere.annee == msg["annee"])
    matieres = []
    for q in query:
        matieres.append(q[0])
    socketio.emit('effChangeMat', matieres)

@socketio.on('changeFic')
def handle_event(msg, methods=['GET', 'POST']):
    Session = sessionmaker(bind=engine)
    s = Session()
    query = s.query(Fichier.nomFichier).filter(Fichier.nomMat == msg["matiere"])
    matieres = []
    for q in query:
        if(q[0][-5]=='s'):
            matieres.append(q[0])
    socketio.emit('effChangeFic', matieres)

## Administrateur
@app.route("/administrateur")
def administrateur():
    if not session.get('logged_in'):
        return redirect(url_for('do_admin_login'))
    else:
        return render_template("administrateur.html", myUsername=session['username'])

## Gérer propositions de corrections anciens

@app.route('/as')
def manage_files():
    if not session.get('logged_in'):
        return redirect(url_for('do_admin_login'))
    Session = sessionmaker(bind=engine)
    s = Session()
    statut = s.query(Utilisateur.status).filter(Utilisateur.username == session['username']).first()[0]
    if statut != 'administrateur':
        return redirect(url_for('home'))
    return render_template('manage_files.html', myUsername=session['username'])

@socketio.on('init_manage_files')
def handle_my_custom_event(msg, methods=['GET', 'POST']):
    annees = os.listdir("static/upload")
    for a in annees:
        if(a != ".DS_Store"):
            matieres = os.listdir("static/upload/"+a)
            if matieres:
                sous_message = []
                for m in matieres:
                    if(m != ".DS_Store"):
                        sous_message.append(m)
                message = { "annee": a , "matieres": sous_message}
                socketio.emit('les_annees', message)

@socketio.on('init_manage_files2')
def handle_my_custom_event(msg, methods=['GET', 'POST']):
    sujets = os.listdir("static/upload/"+msg['annee']+'/'+msg['matiere'])
    for s in sujets:
        if(s != ".DS_Store"):
            propositions = os.listdir("static/upload/"+msg['annee']+'/'+msg['matiere']+'/'+ s)
            if propositions:
                sous_message = []
                for p in propositions:
                    if(p != ".DS_Store"):
                        sous_message.append(p)
                message = {"annee": msg['annee'], "matiere": msg['matiere'], "sujet": s, "propositions": sous_message}
                socketio.emit('les_annees2', message)

@socketio.on('manage_file_suppression')
def handle_my_custom_event(msg, methods=['GET', 'POST']):
    os.remove(msg['lien'])

@socketio.on('manage_file_acceptation')
def handle_my_custom_event(msg, methods=['GET', 'POST']):
    filename = msg['lien'].rsplit("/")
    new_filename = 'static/asset/'+filename[2]+'/'+filename[3]+'/'+filename[4]+'_c.pdf'
    os.rename(msg['lien'], new_filename)

## Création de compte
@app.route('/create_account/<string:key>', methods=['GET','POST'])
def create_account(key):
    if request.method == 'POST':
        Session = sessionmaker(bind=engine)
        s = Session()
        #Check si l'username existe déjà
        query = s.query(Utilisateur.username).filter(Utilisateur.username.in_([request.form['username']]))
        if query.first():
            flash("Ce nom d'utilisateur existe déjà !")
            return redirect(url_for('create_account', key=key))
        # On récupère l'adresse mail correspondante, qui doit forcement exister
        mail = s.query(RaphMail.email).filter(RaphMail.key_email.in_([key]))
        user = Utilisateur(username=str(request.form['username']), password=str(request.form['password']), email=str(mail.first()[0]), status="en attente", annee=str(request.form['annee']))
        s.add(user)
        s.query(RaphMail).filter(RaphMail.key_email == key).delete()
        s.commit()
        return redirect(url_for('do_admin_login'))
    Session = sessionmaker(bind=engine)
    s = Session()
    annees = s.query(Annee.annee)
    print("LLLL", annees)
    return render_template('create_account.html', annees=annees, key=key)

@app.route('/new_account', methods=['GET','POST'])
def new_account():
    if request.method == 'POST':
        #Check si l'email existe déjà
        Session = sessionmaker(bind=engine)
        s = Session()
        query = s.query(Utilisateur.email).filter(Utilisateur.email.in_([request.form['email']]))
        if query.first():
            flash("Cette adresse mail est déjà utilisé !")
            return redirect(url_for('new_account'))
        #Envoie l'email
        mail_settings = {
            "MAIL_SERVER": 'smtp.gmail.com',
            "MAIL_PORT": 465,
            "MAIL_USE_TLS": False,
            "MAIL_USE_SSL": True,
            "MAIL_USERNAME": "raphael.monin69@gmail.com",
            "MAIL_PASSWORD": "18bbestwin",
        }
        app.config.update(mail_settings)
        mail = Mail(app)
        key = "".join(choice(ascii_lowercase) for i in range(10))
        msg = Message(subject="Création de compte Queriddle",
                      sender=app.config.get("MAIL_USERNAME"),
                      recipients=[request.form['email']],
                      body="Clique sur ce lien pour te créer un compte en moins de 30 secondes : http://127.0.0.1:5000/create_account/"+key)
        mail.send(msg)
        # Stock les données
        user2 = RaphMail(key_email=str(key), email=str(request.form['email']))
        s.add(user2)
        s.commit()
        flash("Un mail te permettant de te créer un compte t'as été envoyé")
        return render_template('login.html')
    return render_template('new_account.html')

## Modifier pseudo et mot de passe
@app.route('/modify_account/<string:key>', methods=['GET','POST'])
def modify_account(key):
    if request.method == 'POST':
        Session = sessionmaker(bind=engine)
        s = Session()
        # Check si l'username existe déjà
        query = s.query(Utilisateur.username).filter(Utilisateur.username.in_([request.form['username']]))
        if query.first():
            flash("Ce nom d'utilisateur existe déjà !")
            return redirect(url_for('create_account', key=key))
        # On récupère l'adresse mail correspondante, qui doit forcement exister
        mail = s.query(RaphMail.email).filter(RaphMail.key_email.in_([key]))
        s.query(Utilisateur).filter(Utilisateur.email==str(mail.first()[0])).\
            update({"username": str(request.form['username']), "password": hasher(str(request.form['password']))})
        s.query(RaphMail).filter(RaphMail.key_email == key).delete()
        s.commit()
        return redirect(url_for('do_admin_login'))
    return render_template('modify_account.html', key=key)

@app.route("/ask_modify_account", methods=['POST'])
def ask_modify_account():
    Session = sessionmaker(bind=engine)
    s = Session()
    key = "".join(choice(ascii_lowercase) for i in range(10))
    user = RaphMail(key_email=str(key), email=str(request.form['email']))
    s.add(user)
    s.commit()
    ## Envoie d'un email
    mail_settings = {
        "MAIL_SERVER": 'smtp.gmail.com',
        "MAIL_PORT": 465,
        "MAIL_USE_TLS": False,
        "MAIL_USE_SSL": True,
        "MAIL_USERNAME": "raphael.monin69@gmail.com",
        "MAIL_PASSWORD": "18bbestwin",
    }
    app.config.update(mail_settings)
    mail = Mail(app)
    msg = Message(subject="Modification de compte Queriddle",
                  sender=app.config.get("MAIL_USERNAME"),
                  recipients=[request.form['email']],
                  body="Clique sur ce lien pour modifier ton pseudo et ton mot de passe : http://127.0.0.1:5000/modify_account/" + key)
    mail.send(msg)
    flash("Un mail te permettant de changer ton pseudo et ton mot de passe t'as été envoyé")
    return redirect(url_for("logout"))

## Mon compte
@app.route('/my_account')
def my_account():
    if not session.get('logged_in'):
        return redirect(url_for('do_admin_login'))
    else:
        Session = sessionmaker(bind=engine)
        s = Session()
        query=s.query(Utilisateur).filter(Utilisateur.username == session['username'])[0]
        return render_template('my_account.html', myUsername = query.username, myStatus = query.status, myEmail = query.email, myAnnee=query.annee)

## Gérer les comptes
def fupgrade(statut):
    if statut == "en attente":
        return "utilisateur"
    if statut == "utilisateur":
        return "contributeur"
    if statut == "contributeur":
        return "administrateur"

@app.route("/Upgrade", methods=["POST"])
def upgrade():
    Session = sessionmaker(bind=engine)
    s = Session()
    s.query(Utilisateur).filter(Utilisateur.username == request.form['pseudo']).\
        update({"status": fupgrade(request.form['statut'])})
    s.commit()
    return redirect(url_for("manage_accounts"))

def fdegrade(statut):
    if statut == "utilisateur":
        return "en attente"
    if statut == "contributeur":
        return "utilisateur"
    if statut == "administrateur":
        return "contributeur"

@app.route("/Degrade", methods=["POST"])
def degrade():
    Session = sessionmaker(bind=engine)
    s = Session()
    if request.form['statut'] == "en attente":
        s.query(Like).filter(Like.username == request.form['pseudo']).delete()
        s.query(Dislike).filter(Dislike.username == request.form['pseudo']).delete()
        s.query(Tchat).filter(Tchat.username == request.form['pseudo']).delete()
        s.query(Utilisateur).filter(Utilisateur.username == request.form['pseudo']).delete()
    else:
        s.query(Utilisateur).filter(Utilisateur.username == request.form['pseudo']). \
            update({"status": fdegrade(request.form['statut'])})
    s.commit()
    return redirect(url_for("manage_accounts"))

@app.route("/manage_accounts")
def manage_accounts():
    if not session.get('logged_in'):
        return redirect(url_for('do_admin_login'))
    else:
        Session = sessionmaker(bind=engine)
        s = Session()
        query = s.query(Utilisateur)
        en_attentes = []
        utilisateurs = []
        contributeurs = []
        administrateurs = []
        for q in query:
            if q.status == "en attente":
                en_attentes.append(q)
            elif q.status == "utilisateur":
                utilisateurs.append(q)
            elif q.status == "contributeur":
                contributeurs.append(q)
            elif q.status == "administrateur":
                administrateurs.append(q)
        return render_template("manage_accounts.html", myUsername=session['username'], en_attentes=en_attentes, utilisateurs=utilisateurs, contributeurs=contributeurs, administrateurs=administrateurs)

## Gérer propositions de corrections
@app.route("/manage_corrections_suggestion")
def manage_corrections_suggestion():
    if not session.get('logged_in'):
        return redirect(url_for('do_admin_login'))
    else:
        annees = os.listdir("static/upload")
        years = []
        for a in annees:
            if (a != ".DS_Store"):
                matieres = os.listdir("static/upload/" + a)
                matters = []
                if matieres:
                    for m in matieres:
                        if (m != ".DS_Store"):
                            sujets = os.listdir("static/upload/" + a + "/" + m)
                            subject= []
                            if sujets:
                                for s in sujets:
                                    if (s != ".DS_Store"):
                                        propositions = os.listdir("static/upload/" + a + "/" + m + "/" + s)
                                        proposal = []
                                        if propositions:
                                            for p in propositions:
                                                proposal.append(p)
                                        if proposal != []:
                                            subject.append([s, proposal])
                            matters.append([m, subject])
                years.append([a, matters])
        return render_template('manage_corrections_suggestion.html', myUsername=session['username'], annees=years)

@app.route("/supprimer_proposition_correction", methods=['POST'])
def supprimer_proposition_correction():
    os.remove(request.form['lien'])
    return redirect(url_for('manage_corrections_suggestion'))

@app.route('/ajouter_proposition_correction', methods=['POST'])
def ajouter_proposition_correction():
    filename = request.form['lien'].rsplit("/")
    new_filename = 'static/asset/' + filename[2] + '/' + filename[3] + '/' + filename[4] + '_c.pdf'
    os.rename(request.form['lien'], new_filename)
    return redirect(url_for('manage_corrections_suggestion'))

## Proposition de correction
@app.route('/upload/<string:anneeChoisi>/<string:matiereChoisi>/<string:sujetChoisi>/<string:username>', methods=['POST'])
def upload_file(anneeChoisi, matiereChoisi, sujetChoisi, username):
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(url_for('home'))
        file = request.files['file']
        name = username + ".pdf"
        if file.filename == '':
            flash('Aucun fichier sélectionné')
            return redirect(url_for('home'))
        if file and allowed_file(file.filename):
            file.save(os.path.join('static/upload/'+anneeChoisi+'/'+matiereChoisi+'/'+sujetChoisi, name))
            flash('Votre proposition de correction a été envoyé avec succès')
            return redirect(url_for('home'))

## Gérer propositions de sujets
@app.route("/manage_subjects_suggestion")
def manage_subjects_suggestion():
    if not session.get('logged_in'):
        return redirect(url_for('do_admin_login'))
    else:
        annees = os.listdir("static/upload_subject")
        years = []
        for a in annees:
            if (a != ".DS_Store"):
                matieres = os.listdir("static/upload_subject/" + a)
                matters = []
                if matieres:
                    for m in matieres:
                        if (m != ".DS_Store"):
                            sujets = os.listdir("static/upload_subject/" + a + "/" + m)
                            propositions= []
                            for s in sujets:
                                if (s != ".DS_Store"):
                                    propositions.append(s)
                            matters.append([m, propositions])
                years.append([a, matters])
        return render_template('manage_subjects_suggestion.html', myUsername=session['username'], annees=years)

@app.route("/supprimer_proposition_sujet", methods=['POST'])
def supprimer_proposition_sujet():
    os.remove(request.form['lien'])
    return redirect(url_for('manage_subjects_suggestion'))

@app.route('/ajouter_proposition_sujet', methods=['POST'])
def ajouter_proposition_sujet():
    filename = request.form['lien'].rsplit("/")
    new_filename = 'static/asset/'+filename[2]+'/'+filename[3]+'/'+filename[4][:-4]+'_s.pdf'
    if not os.path.isfile(new_filename):
        os.rename(request.form['lien'], new_filename)
        path = 'static/upload/'+filename[2]+'/'+filename[3]+'/'+filename[4][:-4]
        os.mkdir(path)
        Session = sessionmaker(bind=engine)
        s = Session()
        newFichier = Fichier(nomFichier=request.form['proposition'][:-4]+"_s.pdf", contenu=b'', typeFichier='sujet', nomMat=request.form['matiere'])
        s.add(newFichier)
        s.commit()
    return redirect(url_for('manage_subjects_suggestion'))

##Proposition de sujet
@app.route("/suggest_subject")
def suggest_subject():
    if not session.get('logged_in'):
        return redirect(url_for('do_admin_login'))
    else:
        Session = sessionmaker(bind=engine)
        s = Session()
        annees = s.query(Annee.annee)
        return render_template('suggest_subject.html', myUsername=session['username'], annees=annees)

@app.route("/upload_sujet", methods=['POST'])
def upload_sujet():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(url_for('home'))
        file = request.files['file']
        name = request.form['nom_fichier'] + request.form['utilisateur'] + ".pdf"
        if file.filename == '':
            flash('Aucun fichier sélectionné')
            return redirect(url_for('suggest_subject'))
        if file and allowed_file(file.filename):
            file.save(os.path.join('static/upload_subject/'+ request.form['annee'] + '/' + request.form['matiere'], name))
            flash('Votre proposition de sujet a été envoyé avec succès')
            return redirect(url_for('suggest_subject'))

##Admin ajoute, supprime année matière sujet
@app.route("/admin_changement_annee")
def admin_changement_annee():
    if not session.get('logged_in'):
        return redirect(url_for('do_admin_login'))
    else:
        Session = sessionmaker(bind=engine)
        s = Session()
        annees = s.query(Annee.annee)
        return render_template('admin_changement_annee.html', myUsername=session['username'], annees=annees)

@app.route("/admin_changement_matiere/<string:anneeChoisi>")
def admin_changement_matiere(anneeChoisi):
    if not session.get('logged_in'):
        return redirect(url_for('do_admin_login'))
    else:
        Session = sessionmaker(bind=engine)
        s = Session()
        matieres=s.query(Matiere.nomMat).filter(Matiere.annee==anneeChoisi)
        return render_template('admin_changement_matiere.html', myUsername=session['username'], annee=anneeChoisi, matieres=matieres)

@app.route("/admin_changement_sujet/<string:anneeChoisi>/<string:matiereChoisi>")
def admin_changement_sujet(anneeChoisi, matiereChoisi):
    if not session.get('logged_in'):
        return redirect(url_for('do_admin_login'))
    else:
        Session = sessionmaker(bind=engine)
        s = Session()
        sujets = s.query(Fichier.nomFichier).filter(Fichier.nomMat==matiereChoisi, Fichier.typeFichier=="sujet")
        return render_template('admin_changement_sujet.html', myUsername=session['username'], annee=anneeChoisi, matiere=matiereChoisi, sujets=sujets)

@app.route("/supprimer_annee", methods=['POST'])
def supprimer_annee():
    Session = sessionmaker(bind=engine)
    s = Session()
    matieres = s.query(Matiere).filter(Matiere.annee==request.form['annee'])
    if matieres.first():
        flash("Par mesure de sécurité, vous devez d'abord suprimmer toutes les matières d'une annee pour pouvoir la supprimer")
        return redirect(url_for('admin_changement_annee'))
    s.query(Annee).filter(Annee.annee == request.form['annee']).delete()
    s.commit()
    path1 = './static/upload/' + request.form['annee']
    path2 = './static/asset/' + request.form['annee']
    path3 = './static/upload_subject/' + request.form['annee']
    os.rmdir(path1)
    os.rmdir(path2)
    os.rmdir(path3)
    return redirect(url_for('admin_changement_annee'))

@app.route("/ajouter_annee", methods=['POST'])
def ajouter_annee():
    Session = sessionmaker(bind=engine)
    s = Session()
    annee = s.query(Annee).filter(Annee.annee == request.form['annee'])
    if annee.first():
        flash("Ce nom d'année existe déjà !")
        return redirect(url_for('admin_changement_annee'))
    newAnnee = Annee(annee=request.form['annee'])
    s.add(newAnnee)
    s.commit()
    path1 = './static/upload/'+request.form['annee']
    path2 = './static/asset/' + request.form['annee']
    path3 = './static/upload_subject/' + request.form['annee']
    os.makedirs(path1)
    os.makedirs(path2)
    os.makedirs(path3)
    return redirect(url_for('admin_changement_annee'))

@app.route("/supprimer_matiere", methods=['POST'])
def supprimer_matiere():
    Session = sessionmaker(bind=engine)
    s = Session()
    fichiers = s.query(Fichier).filter(Fichier.nomMat==request.form['matiere'])
    if fichiers.first():
        flash("Par mesure de sécurité, vous devez d'abord suprimmer tous les sujets d'une matiere pour pouvoir la supprimer")
        return redirect(url_for('admin_changement_matiere', anneeChoisi=request.form['annee']))
    ids = s.query(Tchat.id).filter(Tchat.type == 'Matiere', Tchat.nomMat==request.form['matiere'])
    if ids:
        for id in ids:
            s.query(Like).filter(Like.idMessage == id[0]).delete()
            s.query(Dislike).filter(Dislike.idMessage == id[0]).delete()
    s.query(Tchat).filter(Tchat.type == 'Matiere', Tchat.nomMat==request.form['matiere']).delete()
    s.query(Matiere).filter(Matiere.nomMat == request.form['matiere']).delete()
    s.commit()
    path1 = './static/upload/' + request.form['annee'] + '/' + request.form['matiere']
    path2 = './static/asset/' + request.form['annee'] + '/' + request.form['matiere']
    path3 = './static/upload_subject/' + request.form['annee'] + '/' + request.form['matiere']
    os.rmdir(path1)
    os.rmdir(path2)
    os.rmdir(path3)
    return redirect(url_for('admin_changement_matiere', anneeChoisi=request.form['annee']))

@app.route("/ajouter_matiere", methods=['POST'])
def ajouter_matiere():
    Session = sessionmaker(bind=engine)
    s = Session()
    matiere = s.query(Matiere).filter(Matiere.nomMat == request.form['matiere'])
    if matiere.first():
        flash("Ce nom de matière existe déjà !")
        return redirect(url_for('admin_changement_matiere', anneeChoisi=request.form['annee']))
    newMat = Matiere(nomMat=request.form['matiere'], annee=request.form['annee'])
    s.add(newMat)
    s.commit()
    path1 = './static/upload/'+request.form['annee']+'/'+request.form['matiere']
    path2 = './static/asset/' + request.form['annee'] + '/' + request.form['matiere']
    path3 = './static/upload_subject/' + request.form['annee'] + '/' + request.form['matiere']
    os.makedirs(path1)
    os.makedirs(path2)
    os.makedirs(path3)
    return redirect(url_for('admin_changement_matiere', anneeChoisi=request.form['annee']))

@app.route("/supprimer_sujet", methods=['POST'])
def ajouter_sujet():
    corrigé = request.form['sujet'][:-6]+"_c.pdf"
    Session = sessionmaker(bind=engine)
    s = Session()
    s.query(Fichier).filter(Fichier.nomFichier == request.form['sujet']).delete()
    s.query(Fichier).filter(Fichier.nomFichier == corrigé).delete()
    s.commit()
    path1 = './static/asset/' + request.form['annee'] + '/' + request.form['matiere'] + '/' + request.form['sujet']
    path2 = './static/asset/' + request.form['annee'] + '/' + request.form['matiere'] + '/' + corrigé
    path3 = './static/upload/' + request.form['annee'] + '/' + request.form['matiere'] + '/' + request.form['sujet'][:-6]
    os.remove(path1)
    if os.path.isfile(path2):
        os.remove(path2)
    os.rmdir(path3)
    return redirect(url_for('admin_changement_sujet', anneeChoisi=request.form['annee'], matiereChoisi=request.form['matiere']))

## Main
if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
