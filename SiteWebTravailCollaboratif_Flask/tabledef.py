from sqlalchemy import *
from sqlalchemy import create_engine, ForeignKey
from sqlalchemy import Column, Date, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref, sessionmaker
import hashlib
import datetime
import os.path

engine = create_engine('sqlite:///base.db', echo=True)
Base = declarative_base()


def hasher(mystring):
    hash_object = hashlib.md5(mystring.encode())
    return hash_object.hexdigest()

class Annee(Base):
    __tablename__ = "annees"
    annee = Column(String, primary_key=True)

    def __init__(self, annee):
        self.annee = annee

class Utilisateur(Base):
    __tablename__ = "utilisateurs"
    username = Column(String, primary_key=True)
    email = Column(String)
    password = Column(String)
    status = Column(String)
    annee = Column(Integer, ForeignKey("annees.annee"))

    annee_rel = relationship("Annee", foreign_keys=[annee])

    def __init__(self, email="", username="", password="", status="", annee=""):
        self.email = email
        self.username = username
        self.password = hasher(password)
        self.status = status
        self.annee = annee

class Matiere(Base):
    __tablename__ = "matieres"
    nomMat = Column(String, primary_key=True)
    annee = Column(Integer, ForeignKey("annees.annee"))
    score = Column(Integer)
    annee_rel = relationship("Annee", foreign_keys=[annee])

    def __init__(self, nomMat, annee):
        self.nomMat = nomMat
        self.score = 0
        self.annee = annee


class Fichier(Base):
    __tablename__ = "fichiers"
    id = Column(Integer, primary_key=True)
    nomFichier = Column(String)
    contenu = Column(Binary)
    typeFichier = Column(String)
    nomMat = Column(String, ForeignKey("matieres.nomMat"))

    mat_rel = relationship("Matiere", foreign_keys=[nomMat])

    def __init__(self, nomFichier, contenu, typeFichier, nomMat):
        self.nomFichier = nomFichier
        self.contenu = contenu
        self.typeFichier = typeFichier
        self.nomMat = nomMat


class Tchat(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    contenu = Column(String)
    score = Column(Integer)
    refere = Column(Integer)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    type = Column(String)
    username = Column(Integer, ForeignKey("utilisateurs.username"))
    nomMat = Column(String)

    user_rel = relationship("Utilisateur", foreign_keys=[username])

    def __init__(self, contenu, refere, username, idFichier, nomMat, type, score=0):
        self.contenu = contenu
        self.score = score
        self.refere = refere
        self.username = username
        self.idFichier = idFichier
        self.nomMat = nomMat
        self.type = type

class ChatPrive(Base):
    __tablename__ = "chatprive"
    id = Column(Integer, primary_key=True)
    contenu = Column(String)
    score = Column(Integer)
    refere = Column(Integer)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    username = Column(Integer, ForeignKey("utilisateurs.username"))
    recipient = Column(Integer, ForeignKey("utilisateurs.username"))

    user_rel = relationship("Utilisateur", foreign_keys=[username])
    rec_rel = relationship("Utilisateur", foreign_keys=[recipient])

    def __init__(self, contenu, refere, username, recipient, score=0):
        self.contenu = contenu
        self.refere = refere
        self.username = username
        self.recipient = recipient
        self.score = score

class QuestionArchive(Base):
    __tablename__ = "questionsArchivees"
    id = Column(Integer, primary_key=True)
    question = Column(String)
    score = Column(Integer)
    username = Column(Integer, ForeignKey("utilisateurs.username"))
    annee = Column(String, ForeignKey("annees.annee"))
    nomMat = Column(String, ForeignKey("matieres.nomMat"))
    idFichier = Column(Integer, ForeignKey("fichiers.id"))

    user_rel = relationship("Utilisateur", foreign_keys=[username])
    ann_rel = relationship("Annee", foreign_keys=[annee])
    mat_rel = relationship("Matiere", foreign_keys=[nomMat])
    fich_rel = relationship("Fichier", foreign_keys=[idFichier])

    def __init__(self, question, username, annee, nomMat, idFichier, score=0):
        self.question = question
        self.score = score
        self.username = username
        self.annee = annee
        self.nomMat = nomMat
        self.idFichier = idFichier


class Commentaire(Base):
    __tablename__ = "commentaires"
    id = Column(Integer, primary_key=True)
    contenu = Column(String)
    username = Column(Integer, ForeignKey("utilisateurs.username"))
    idQuestArch = Column(Integer, ForeignKey("questionsArchivees.id"))
    refere = Column(Integer)

    user_rel = relationship("Utilisateur", foreign_keys=[username])
    user_rel = relationship("QuestionArchive", foreign_keys=[idQuestArch])

    def __init__(self, contenu, username, idQuestArch, refere):
        self.contenu = contenu
        self.username = username
        self.idQuestArch = idQuestArch
        self.refere = refere


class RaphMail(Base):
    __tablename__ = "raphmails"
    # On met ça en primary pour être sur de chez sur
    # Que personne aura la même clé d'url
    key_email = Column(String, primary_key=True)
    email = Column(String)

    def __init__(self, key_email, email):
        self.key_email = key_email
        self.email = email

class Like(Base):
    __tablename__="likes"
    id = Column(Integer, primary_key=True)
    idMessage=Column(Integer)
    username=Column(String,ForeignKey("utilisateurs.username"))
    type = Column(String)

    user_rel = relationship("Utilisateur", foreign_keys=[username])

    def __init__(self, idMessage,username, type):
        self.idMessage=idMessage
        self.username=username
        self.type = type

class Dislike(Base):
    __tablename__="dislikes"
    id = Column(Integer, primary_key=True)
    idMessage=Column(Integer)
    username=Column(String,ForeignKey("utilisateurs.username"))
    type = Column(String)

    user_rel = relationship("Utilisateur", foreign_keys=[username])

    def __init__(self, idMessage,username, type):
        self.idMessage=idMessage
        self.username=username
        self.type = type

'''
les méthodes from_asset font 2 choses,
en cherchant dans le dossier asset, où se trouvent les ressources, on :
1- Créé toutes les matieres ou fichiers associés
2- on renvoie un json des matieres par années 
'''
def db_from_asset():
    Session = sessionmaker(bind=engine)
    annees = os.listdir("static/asset")
    for annee in annees:
        new_annee = Annee(annee=annee)
        session.add(new_annee)
        matieres = os.listdir(os.path.join(os.getcwd(),"static/asset", annee))
        for matiere in matieres:
            new_matiere = Matiere(nomMat=matiere, annee=annee)
            session.add(new_matiere)
            fichiers = os.listdir(os.path.join(os.getcwd(),"static/asset", annee, matiere))
            for fichier in fichiers:
                if fichier[-5] == "s":
                    new_fichier = Fichier(nomFichier=fichier, contenu=b'', typeFichier='sujet', nomMat=matiere)
                else:
                    new_fichier = Fichier(nomFichier=fichier, contenu=b'', typeFichier='corrigé', nomMat=matiere)
                session.add(new_fichier)
    session.commit()

# create tables
Base.metadata.create_all(engine)
if __name__ == '__main__':
    if os.path.isfile("base.db"):
        os.remove("base.db")
        # create tables
        Base.metadata.create_all(engine) ## TODO peut inclure des erreurs

    # create a Session
    Session = sessionmaker(bind=engine)
    session = Session()

    user = Utilisateur(username="Raphael", password="Monin", email="raphael.monin@insa-lyon.fr", status="administrateur", annee="3TC")
    session.add(user)
    user = Utilisateur(username="Marlon-Bradley", password="Paniah", email="to complete", status="contributeur", annee="3TC")
    session.add(user)
    user = Utilisateur(username="Maxime", password="Bernard", email="to complete", status="utilisateur", annee="3TC")
    session.add(user)
    user = Utilisateur(username="Tom", password="Ltr", email="to complete", status="utilisateur", annee="3TC")  # j'ai changé mon mdp batar
    session.add(user)
    user = Utilisateur(username="Basile", password="Deneire", email="to complete", status="en attente", annee="3TC")
    session.add(user)
    db_from_asset()

    # commit the record the database
    session.commit()