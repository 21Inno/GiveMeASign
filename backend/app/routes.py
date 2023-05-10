from . import app
from . import db

from flask import Flask, redirect, jsonify, request, Response, render_template, url_for, flash, send_file
from flask_cors import CORS
from sqlalchemy import exists

import requests
import json
import os, binascii
from werkzeug.utils import secure_filename

import fnmatch
import spacy
import fr_core_news_sm

from .forms import RegisterAdminForm, LoginAdminForm, GroupeForm, EditGroupeForm
from .models import User, Group, UserHistory, SignHistory, sign_to_dict, SignProposition, prop_to_dict, group_Public, \
    anonyme_user, Admin, PWReset
from flask_login import login_required, login_user, logout_user, current_user

from .util import utils, keygenerator, smtpConfig
import uuid
import pytz
import yagmail
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

import imageio

dico = {}
nlp = spacy.load("fr_core_news_sm")
CORS(app, resources=r'/*')

memo_current_user = {current_user: ["Public", "ano"]}


# -------------------- Translate views--------------------
@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")


@app.route("/translate", methods=["GET", "POST"])
def translate():
    """
    Cette app.route permet de traduire un mot en langue des signes LSFB
    Elle recupere le mot et son contexte via un json.load,
    elle fait appel à 3 point API du dico.corpus LSFB Unamur,
    elle utilise Spacy: une librairie open-source pour du NLP en python

    Return :
    --------
    :return: la fonction renvoie un jsonify contenant une liste des signes correspond au mot
    un element de cette liste est un tuple contenant (Gloss,line_gif,mots-clé)
    """
    _current_user = list(memo_current_user)[-1]

    if _current_user.is_authenticated:
        _current_group = memo_current_user[_current_user][0]
        _current_username = memo_current_user[_current_user][1]
    else:
        _current_group = "Public"
        _current_username = "ano"

    print(_current_group, _current_username)

    ##if request.method == 'POST':
    # Points API du dico.corpus-lsfb
    api_sign_base = 'https://dico.corpus-lsfb.be/api/annotation/signs/exact/'
    api_gif_base = 'https://corpus-lsfb.be/img/pictures/'
    api_lemme_base = 'https://dico.corpus-lsfb.be/api/traduction/lemmes/'

    # Récupérer un mot et son contexte
    mot_select = json.loads(request.data, strict=False)["selected_word"].lower()
    phrase = json.loads(request.data, strict=False)["contextWords"].lower()  # get form js le phase
    print(mot_select)
    print(phrase)
    # PoS tagging du mot selectionné
    nature_du_mot = utils.get_pos(mot_select, nlp)

    #
    if nature_du_mot in ['VERB', 'AUX']:
        # mettre tous les verbes et auxillaires à l'infinitif
        new_phrase = utils.get_infinitif(phrase, nlp)
    else:
        new_phrase = phrase
    # obtenir les formes fléchies ou lemmes du mot
    lemme = []
    if nature_du_mot not in ['GroupNom', 'DET', 'ADP']:
        # si le mot est un verbe ou nom
        # requete pour lemme et forme flechie
        req = api_lemme_base + mot_select
        response_api = requests.get(req)
        data = response_api.text
        parse_json = json.loads(data)
        traduction_ = parse_json

        for mot in traduction_:
            lemme.append(utils.get_infinitif(mot, nlp))

        # eliminer les doublons
        lemme = list(set(lemme))

    elif nature_du_mot == 'GroupNom':
        lemme.append(mot_select)

    # -------------------------Recherche dans le corpus---------------------------------
    # la liste "lemme" contient maintenant le mot et toutes ses variations possibles
    # recuperer tous les gloss et leurs mots clés

    all_traduction_data, dico_of_gloss_keyword = utils.getKeywords(lemme, api_sign_base)

    # print(dico_of_gloss_keyword)

    # retenir les gloss pertinents
    final_gloss_dict = {}
    for gloss in dico_of_gloss_keyword:
        tmp_keywords = dico_of_gloss_keyword[gloss]
        for key in tmp_keywords:
            if key in new_phrase:
                # si un gloss est retenu, il n'est plus nessecaire de parcourir les autres mots clés
                if gloss not in list(final_gloss_dict.keys()):
                    final_gloss_dict[gloss] = tmp_keywords

    # si aucun gloss n'est pertinant alors on selectione tous les gloss
    if len(final_gloss_dict) == 0:
        for gloss in dico_of_gloss_keyword:
            # if mot in list(dico_of_gloss_keyword.keys()):
            final_gloss_dict[gloss] = dico_of_gloss_keyword[gloss]
    print([trad for trad in all_traduction_data])
    # get a list of sign
    requete_gif_list_corpus = [
        (trad['_gloss'], api_gif_base + trad['_url'], final_gloss_dict[trad['_gloss']], "CorpusLSFB", "CorpusLSFB")
        for trad in
        all_traduction_data if trad['_gloss'] in list(final_gloss_dict.keys())]
    # ------------------------ Fin recherche dans le corpus ----------------------

    # -------------------------Recherche dico parallele -----------------------------
    lemme_input = lemme
    if len(lemme_input) == 0:
        lemme_input = [mot_select]
    # good_sign_proposition = []        # lievre lievre1
    # for lem in lemme input :
    print(lemme_input)
    filters = [SignProposition.gloss.like(f'%{word}%') for word in lemme_input]
    print("filter : ", filters)

    good_sign_proposition = []

    if len(filters) != 0:
        if _current_group != 'Public':
            proposition_object = SignProposition.query.filter(
                db.and_(*filters, db.or_(SignProposition.certified == 'True',
                                         SignProposition.group_name == _current_group))).all()
            for prop in proposition_object:
                good_sign_proposition.append(
                    (prop.gloss, prop.url, prop.keywords, prop.author_name, str(prop.group_name)))
        else:
            print(_current_group)
            proposition_object = SignProposition.query.filter(
                db.and_(*filters, SignProposition.certified == 'True')).all()
            for prop in proposition_object:
                good_sign_proposition.append(
                    (prop.gloss, prop.url, prop.keywords, prop.author_name, str(prop.group_name)))
    gifs_ = requete_gif_list_corpus + good_sign_proposition
    print(gifs_)

    print(jsonify(gifs_))
    # ---------------------------      ----------------------------
    return jsonify({"corpus": gifs_, "groupName": _current_group})


@app.route('/upload/<mot>', methods=['GET', 'POST'])
def upload(mot):
    """Cette methode permet de recuperer et de stocker les videos
       qui ont ete enregistrees pour ajouter un nouveau signe

       Parameters:
       ----------
       mot : le nom de la video qui sera enregistree (str)

       Return:
       -------
       nous renvoie vers la page html après le post
       un messsage de succès apres la reception de la video
       ""    ""    d echec si la reception ne s est pas faite
    """
    """user = list(memo_current_user)[-1]
    _current_user_ = User.query.filter_by(username=memo_current_user[user][1]).first()"""

    current_group = "Public"
    _current_user = "ano"
    blocked = False
    certified_state = "waiting"
    if current_user.is_authenticated:
        if current_user.role == "normal":
            current_group = current_user.group.name
            _current_user = current_user.username
            certified_state = 'False'

        # un user bloqué par un prof ne peut pas uploader de vidéo
        if current_user.blocked:
            blocked = True
            print("aaaa")
            flash('Vous avez été bloqué par votre professeur', 'info')
            return render_template("record.html", mot=mot, group=current_group, blocked=blocked)

    if request.method == 'POST':

        directory = os.path.abspath(os.path.dirname(__file__)) + "/static/videos/" + current_group
        directory_gif = os.path.abspath(os.path.dirname(__file__)) + "\\static\\gifs\\" + current_group

        if not os.path.isdir(directory):
            os.mkdir(directory)
        if not os.path.isdir(directory_gif):
            os.mkdir(directory_gif)
        # create a directory to save the video if
        # it not already existed
        directory2 = os.path.abspath(os.path.dirname(__file__)) + "/static/videos/" + current_group + "/videos_" + mot
        directory_gif2 = os.path.abspath(
            os.path.dirname(__file__)) + "\\static\\gifs\\" + current_group + "\\gifs_" + mot
        if not os.path.isdir(directory2):
            os.mkdir(directory2)
        if not os.path.isdir(directory_gif2):
            os.mkdir(directory_gif2)
        # print(request.files)

        # check if there is a video file
        if 'video' not in request.files:
            return 'No video file provided'

        video_file = request.files.get('video')

        filename = secure_filename(video_file.filename)  # permet de securiser le fichier

        keywords = request.files.get('keywords').filename

        # on va nommer les videos par leur nom + un identifiant
        # en fonction de leur ordre de sauvegarde dans le dossier
        count = len(fnmatch.filter(os.listdir(directory2), '*.*'))
        path = os.path.join(directory2, filename + "_" + str(count) + '.mp4')
        path_gif = os.path.join(directory_gif2, filename + "_" + str(count) + '.gif')
        try:
            if not video_file.filename + str(count) in dico["videos_" + mot]:
                dico["videos_" + mot].append(video_file.filename + "_" + str(count))

        except:
            dico["videos_" + mot] = [video_file.filename + str(count)]

        print(dico)
        video_file.save(path)  # enregistrement de la vidéo
        # video_clip = VideoFileClip(path)  # creation du gif
        # video_clip.write_gif(path_gif)  # enregistrement du gif
        vid = imageio.get_reader(path)
        fps = vid.get_meta_data()['fps']
        writer = imageio.get_writer(path_gif, fps=fps)

        for img in vid:
            writer.append_data(img)

        writer.close()
        print("les keywords", keywords)
        gif_name = filename + "_" + str(count) + '.gif'
        api_gif = url_for('get_gif', filename=gif_name, mot=mot, current_group=current_group)
        # save DB
        proposition = SignProposition(gloss=video_file.filename + "_" + str(count), keywords=keywords,
                                      url=api_gif, group_name=current_group,
                                      author_name=_current_user, certified=certified_state)
        db.session.add(proposition)
        db.session.commit()
        return 'File uploaded successfully'
    return render_template("record.html", mot=mot, group=current_group, blocked=blocked)

@app.route('/gifsAPI/<current_group>/<mot>/<filename>')
def get_gif(filename, mot, current_group):
    directory_gif2 = os.path.abspath(
        os.path.dirname(__file__)) + "\\static\\gifs\\" + current_group + "\\gifs_" + mot
    file_path = os.path.join(directory_gif2, filename)
    return send_file(file_path, mimetype='image/gif')


# -------------------------End translate views -----------------------

# ------------------------- Expert pages --------------------
@app.route('/expert_main', methods=['GET', 'POST'])
def expert_main():
    if current_user.is_authenticated:
        current_group = current_user.group.name
        current_username = current_user.username

    else:
        current_group = "Public"
        current_username = "anonyme"

    main_folder = 'app/static/videos/' + current_group + '/'

    subdirectories = {}
    print(main_folder)
    print(os.listdir(main_folder))
    for subdir in os.listdir(main_folder):
        print(subdir)
        if os.path.isdir(main_folder + subdir):
            print(subdir.replace('videos_', ''))
            num_files = len(
                [f for f in os.listdir(main_folder + subdir) if os.path.isfile(os.path.join(main_folder + subdir, f))])
            subdirectories[subdir.replace('videos_', '')] = num_files
    print(subdirectories)
    return render_template('allProposition.html', subdirectories=subdirectories)


@app.route('/proposition/<sub>', methods=['GET', 'POST'])
def proposition_videos(sub):
    if current_user.is_authenticated:
        current_group = current_user.group.name
        current_username = current_user.username

    else:
        current_group = "Public"
        current_username = "ano"
    directory = 'app/static/videos/' + current_group + '/videos_' + sub
    videos_ = [f for f in os.listdir(directory) if f.endswith('.mp4')]
    return render_template('video_for_sign.html', videos=videos_, word=sub)


@app.route("/dashboard_expert/")
def dashboard_expert():
    if not current_user.is_authenticated:
        # if current_user.role == "admin":
        return redirect(url_for("login_admin"))
    if current_user.username != 'Public_admin':
        return redirect(url_for("dashboard_admin"))
    dico_sign_group = {}
    _sign_prop = SignProposition.query.filter_by(certified="waiting").all()
    print(_sign_prop)
    for _sign in _sign_prop:
        group = _sign.group_name
        if group in dico_sign_group:
            dico_sign_group[group] += 1
        else:
            dico_sign_group[group] = 1
    print(dico_sign_group)
    return render_template("dashboard_expert.html", groups=dico_sign_group)


@app.route('/dashboard_expert/signGroup/<name>/')
def check_sign_expert(name):
    if not current_user.is_authenticated:
        # if current_user.role == "admin":
        return redirect(url_for("login_admin"))
    _propositions = SignProposition.query.filter_by(group_name=name, certified="waiting").all()
    liste = []
    for prop in _propositions:
        liste.append(prop_to_dict(prop))
    print(liste)

    return render_template("sign_expert_check.html", liste=liste, admin_name=current_user.username)


@app.route("/send_to_expert/<int:idSign>/")
def send_to_expert(idSign):
    _videoProp = SignProposition.query.filter_by(id=idSign).first()
    if _videoProp is not None:
        _videoProp.certified = 'waiting'

        db.session.commit()
    return redirect(url_for("show_groupVideos", name=_videoProp.group_name))


@app.route("/dashboard_expert/validate_sign/<int:idSign>/")
def validate_sign(idSign):
    if not current_user.is_authenticated:
        # if current_user.role == "admin":
        return redirect(url_for("login_admin"))
    _videoProp = SignProposition.query.filter_by(id=idSign).first()
    # Check if the current_user has the movie in my list

    if _videoProp is not None:
        _videoProp.certified = 'True'

        db.session.commit()

    return redirect(url_for("check_sign_expert", name=_videoProp.group_name))


# ---------------------- Expert page end --------------------------


# -------------------------- User features --------------------------------

@app.route('/islog/')
def is_log():
    if current_user.is_authenticated:
        if current_user.role == "normal":
            return jsonify({"_log": "true", "_username": current_user.username, "_role": current_user.role,
                            "_group": current_user.group.name})
        else:
            return jsonify({"_log": "true", "_username": current_user.username, "_role": current_user.role})
    else:
        return jsonify({"_log": "false"})


@app.route('/login/', methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        if current_user.role == "admin":

            return redirect(url_for("dashboard_admin"))
        else:
            return redirect(url_for("dashboard"))
    if request.method != 'GET':
        _group = request.form['group-name']
        _username = request.form['username']
        _password = request.form['password']

        group = Group.query.filter_by(name=_group).first()

        print(_group, _username, _password)

        if group is None:
            print("pas de group")
            return redirect(url_for("login"))

        if not group.check_password(_password):
            print("bad pwd")
            return redirect(url_for("login"))

        _complete_username = group.name + '_' + _username
        user = User.query.filter_by(username=_complete_username).first()

        if user is None:
            user = Admin.query.filter_by(username=_username).first()
            if user is None:
                _username_final = group.name + '_' + _username
                user = User(username=_username_final, role="normal", group=group, blocked=False)
                db.session.add(user)
                db.session.commit()
        else:
            if user.group_id != group.id:
                _username_final = group.name + '_' + _username
                user = User(username=_username_final, role="normal", group=group, blocked=False)
                db.session.add(user)
                db.session.commit()
        login_user(user)
        memo_current_user[user] = [user.group.name, user.username]
        print('login done')
        print(current_user.username, current_user.role)
        return redirect(url_for('dashboard'))
    print("get login")
    return render_template('login.html')


@app.route('/addHistory', methods=["GET", "POST"])
def addHistory():
    _current_user = list(memo_current_user)[-1]

    if _current_user.is_authenticated:
        _current_group = memo_current_user[_current_user][0]
        _current_username = memo_current_user[_current_user][1]
    else:
        _current_group = "Public"
        _current_username = "ano"

    _gloss_name = json.loads(request.data, strict=False)["gloss_name"]
    _keywords = json.loads(request.data, strict=False)["keywords"]
    if type(_keywords) == list:
        _keywords1 = ", ".join(_keywords)
    else:
        _keywords1 = _keywords
    _url = json.loads(request.data, strict=False)["url"]
    _mot_select = json.loads(request.data, strict=False)["selected_word"].lower()

    print(_current_group, _current_username)
    print(_current_user)
    print(_gloss_name, _keywords, _url)

    # datetime object containing current date and time
    now = datetime.now()

    new_sign = SignHistory(mot=_mot_select,gloss=_gloss_name, keywords=_keywords1,
                           url=_url, datetime=now)
    new_user_history = UserHistory(user=_current_user, sign_history=new_sign)
    old_sign = SignHistory.query.filter_by(gloss=_gloss_name).first()
    if old_sign is not None:
        old_historique = UserHistory.query.filter_by(sign_id=old_sign.id, user_id=_current_user.id).first()
        db.session.delete(old_sign)
        db.session.delete(old_historique)

    db.session.add(new_sign)
    db.session.add(new_user_history)
    db.session.commit()
    return jsonify("Ajouté")


@app.route('/dashboard/', methods=["GET", "POST"])
@login_required
def dashboard():
    _current_user = current_user
    print(_current_user.username)
    if not _current_user.is_authenticated:
        # if current_user.role == "admin":
        return redirect(url_for("login"))
    if _current_user.role == "admin":
        print(_current_user.username)
        print("ici vers dashboard_admin")
        return redirect(url_for("dashboard_admin"))
    my_history = []
    for hist in _current_user.history:
        sign = SignHistory.query.filter_by(id=hist.sign_id).first()
        if sign is not None:
            my_history.append(sign_to_dict(sign))

    print(my_history)
    my_history1 = my_history[::-1]
    print(my_history1)

    return render_template("dashboard.html", user=_current_user, my_history=my_history1)


# Route for deleting a movie from my list
@app.route("/delete_in_history/<int:identifiant>", methods=["GET"])
@login_required
def delete(identifiant):
    print(current_user.username)
    _sign = SignHistory.query.get(identifiant)
    _historique = UserHistory.query.filter_by(sign_id=identifiant, user_id=current_user.id).first()

    # Check if the current_user has the movie in my list
    if _historique is not None:
        db.session.delete(_historique)
        db.session.delete(_sign)
        db.session.commit()

    return redirect(url_for("dashboard"))


@app.route('/logout/', methods=["GET", "POST"])
def logout():
    logout_user()
    memo_current_user.popitem()
    return redirect(url_for('login'))


# ---------------------------End user features--------------------

# ---------------------------Admin features---------------------

@app.route('/register_admin/', methods=["GET", "POST"])
def register_admin():
    # check is current user already authenticated
    if current_user.is_authenticated:
        if current_user.role == "admin":
            return redirect(url_for("dashboard_admin"))
        else:
            return redirect(url_for("dashboard"))

    # Form data
    login_form= LoginAdminForm()
    register_form = RegisterAdminForm()
    if register_form.validate_on_submit():
        # Add the user in the dict of users
        user = Admin(username=register_form.username.data, role="admin", email=register_form.email.data)
        user.set_password(register_form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Vous êtes bien enregistré", "info")
        return redirect(url_for("login_admin"))

    return redirect(url_for("login_register_admin"))


@app.route('/login_register/', methods=["GET", "POST"])
def login_register_admin():
    login_form = LoginAdminForm()
    register_form = RegisterAdminForm()

    return render_template("login_register.html", login_form=login_form, register_form=register_form)


@app.route("/login_admin/", methods=["GET", "POST"])
def login_admin():
    # check is current user already authenticated
    if current_user.is_authenticated:
        if current_user.role == "admin":
            return redirect(url_for("dashboard_admin"))
        else:

            # logout_user()
            redirect(url_for("dashboard"))
    # Form data
    register_form=RegisterAdminForm()
    login_form = LoginAdminForm()
    if login_form.validate_on_submit():

        admin = Admin.query.filter_by(username=login_form.username.data).first()
        if admin is None:
            flash("You are not registered yet.", "log_warning")
            return redirect(url_for("login_admin"))

        if not admin.check_password(login_form.password.data):
            flash("Username or password incorrect.", "log_warning")
            return redirect(url_for("login_admin"))

        # Ok for log in
        login_user(admin)
        flash("Logged in successfully.", "info")

        return redirect(url_for("dashboard_admin"))

    # GET
    return render_template("login_admin.html", login_form=login_form, register_form = register_form)


@app.route('/dashboard_admin/')
def dashboard_admin():
    if not current_user.is_authenticated:
        # if current_user.role == "admin":
        return redirect(url_for("login_admin"))
        # else:
        # return redirect(url_for("login"))
    # get the groups create by the current admin
    if current_user.role == "admin":
        admin_current = current_user
    else:
        return redirect(url_for("dashboard"))

    #  si expert
    if current_user.username == 'Public_admin':
        return redirect(url_for("dashboard_expert"))

    # si simple admin
    _groups = admin_current.groups
    dico_group = {}
    if len(_groups) == 0:
        return render_template("dashboard_adminEmpty.html", admin_name=admin_current.username)
    for group in _groups:
        dico_group[group] = len(group.users)
    return render_template("dashboard_admin.html", groups=dico_group, admin_name=admin_current.username)


@app.route("/dashboard_admin/addGroup/", methods=["GET", "POST"])
def adminAddGroup():
    if not current_user.is_authenticated:
        return redirect(url_for("login_admin"))

    if current_user.role != "admin":
        return redirect(url_for("dashboard"))

    # Form data
    form = GroupeForm()
    if form.validate_on_submit():
        # create the group
        group = Group(name=form.name.data, description=form.description.data, admin_id=current_user.id)
        group.set_password(form.password.data)
        # add the admin as a simple user in the group
        _username_final = group.name + '_' + current_user.username

        user = User(username=_username_final, role="normal", group=group, blocked=False)

        db.session.add(group)
        db.session.add(user)

        db.session.commit()
        flash("Congratulations, you have add a new group!", "info")
        return redirect(url_for("dashboard_admin"))

    return render_template("add_group.html", form=form)


@app.route("/dashboard_admin/editGroup/<int:groupId>", methods=["GET", "POST"])
def adminEditGroup(groupId):
    if not current_user.is_authenticated:
        # if current_user.role == "admin":
        return redirect(url_for("login_admin"))
        # else:
        # return redirect(url_for("login"))
    if current_user.role != "admin":
        return redirect(url_for("dashboard"))

    # Form data
    form = EditGroupeForm()
    _group = Group.query.get(groupId)
    if form.validate_on_submit():
        # create the group

        _group.name = form.name.data
        _group.description = form.description.data
        _group.set_password(form.password.data)

        db.session.commit()
        flash("Congratulations, you have add a new group!", "info")
        return redirect(url_for("dashboard_admin"))
    form.name.data = _group.name
    form.description.data = _group.description

    return render_template("edit_group.html", group=_group, form=form, admin_name=current_user.username)


@app.route('/dashboard_admin/deleteGroup/<int:groupId>')
def deleteGroup(groupId):
    _group = Group.query.get(groupId)
    _users = User.query.filter_by(group_id=groupId).all()
    db.session.delete(_group)
    for user in _users:
        db.session.delete(user)
    db.session.commit()
    return redirect(url_for("dashboard_admin"))


@app.route('/dashboard_admin/videoGroup/<name>/')
def show_groupVideos(name):
    if not current_user.is_authenticated:
        # if current_user.role == "admin":
        return redirect(url_for("login_admin"))
        # else:
        # return redirect(url_for("login"))
    if current_user.role != "admin":
        return redirect(url_for("dashboard"))

    _propositions = SignProposition.query.filter_by(group_name=name).all()
    liste = []
    for prop in _propositions:
        liste.append(prop_to_dict(prop))
    print(liste)
    return render_template("video_group.html", liste=liste, admin_name=current_user.username)


# Route for deleting a movie from my list
@app.route("/dashboard_admin/delete_video/<int:identifiant>", methods=["GET"])
def delete_video(identifiant):
    if not current_user.is_authenticated:
        # if current_user.role == "admin":
        return redirect(url_for("login_admin"))
        # else:
        # return redirect(url_for("login"))
    if current_user.role != "admin":
        return redirect(url_for("dashboard"))

    # _sign = SignHistory.query.get(identifiant)
    _videoProp = SignProposition.query.filter_by(id=identifiant).first()
    # Check if the current_user has the movie in my list

    if _videoProp is not None:
        _sign_history = SignHistory.query.filter_by(gloss=_videoProp.gloss, url=_videoProp.url).all()
        for _sign in _sign_history:
            db.session.delete(_sign)

        db.session.delete(_videoProp)

        # db.session.delete(_sign)
        db.session.commit()

    return redirect(url_for("dashboard_admin"))


@app.route("/dashboard_admin/block/<username>/", methods=["GET"])
def block(username):
    if not current_user.is_authenticated:
        # if current_user.role == "admin":
        return redirect(url_for("login_admin"))
        # else:
        # return redirect(url_for("login"))
    if current_user.role != "admin":
        return redirect(url_for("dashboard"))

    # get the block user in the DB
    blocked_user = User.query.filter_by(username=username).first()
    # change his blocked attribute in the DB
    blocked_user.blocked = not blocked_user.blocked
    users = User.query.all
    db.session.commit()
    return redirect(url_for("view_user", users_group=blocked_user.group_id))


@app.route("/dashboard_admin/users/<int:users_group>/")
def view_user(users_group):
    if not current_user.is_authenticated:
        # if current_user.role == "admin":
        return redirect(url_for("login_admin"))
        # else:
        # return redirect(url_for("login"))
    if current_user.role != "admin":
        return redirect(url_for("dashboard"))
    liste = []
    _users = User.query.filter_by(group_id=users_group).all()
    for user in _users:
        # change his blocked attribute in the DB
        liste.append(user)

    return render_template("users.html", users=liste, admin_name=current_user.username)


@app.route('/logout_admin', methods=["GET", "POST"])
def logout_admin():
    logout_user()
    return redirect(url_for("login_register_admin"))


###################
# Password Forget #
###################

# Display  forgot password page
@app.route("/pwresetrq", methods=["GET"])
def pwresetrq_get():
    """
    display a form to enter the email of password recuparation
    """
    return render_template('forgotPage.html')


# Send a request to change password
@app.route("/pwresetrq", methods=["POST"])
def pwresetrq_post():
    """
    the view send a request to change password
    :return: return to login page
    """
    if db.session.query(Admin).filter_by(email=request.form["email"]).first():

        user = db.session.query(Admin).filter_by(email=request.form["email"]).one()
        # check if user already has reset their password, so they will update
        # the current key instead of generating a separate entry in the table.
        if db.session.query(PWReset).filter_by(user_id=user.id).first():

            pwalready = db.session.query(PWReset).filter_by(user_id=user.id).first()
            # if the key hasn't been used yet, just send the same key.
            if pwalready.has_activated == False:

                pwalready.datetime = datetime.now()
                key = pwalready.reset_key
            else:

                key = keygenerator.make_key()
                pwalready.reset_key = key
                pwalready.datetime = datetime.now()
                pwalready.has_activated = False
        else:
            key = keygenerator.make_key()

            user_reset = PWReset(reset_key=str(key), user_id=user.id)
            db.session.add(user_reset)
        db.session.commit()

        # send the email
        email = smtpConfig.EMAIL
        pwd = smtpConfig.PASSWORD

        yag = yagmail.SMTP(user=email, password=pwd)
        contents = ['Please go to this URL to reset your password:',
                    request.host + url_for("pwreset_get", id=(str(key)))]
        yag.send(request.form["email"], 'Reset your password', contents)
        flash("Hello " + user.username + ", check your email for a link to reset your password.", "success")

        return redirect(url_for("login_register_admin"))
    else:

        flash("Your email was never registered.", "danger")
        return redirect(url_for("pwresetrq_get"))


# Display the reset password page
@app.route("/pwreset/<id>", methods=["GET"])
def pwreset_get(id):
    """
    Display a form to enter new password
    :param id: id of password reset link
    :return:
    """
    key = id
    pwresetkey = db.session.query(PWReset).filter_by(reset_key=id).one()
    generated_by = datetime.utcnow().replace(tzinfo=pytz.utc) - timedelta(hours=24)
    # if the pwd has been already change by the URL
    if pwresetkey.has_activated is True:
        flash("You already reset your password with the URL you are using." +
              "If you need to reset your password again, please make a" +
              " new request here.", "danger")

        return redirect(url_for("pwresetrq_get"))
    # if the password reset link expired
    if pwresetkey.datetime.replace(tzinfo=pytz.utc) < generated_by:
        flash("Your password reset link expired.  Please generate a new one" +
              " here.", "danger")

        return redirect(url_for("pwresetrq_get"))
    # Display a form to enter new pasword
    return render_template('resetPassword.html', id=key)


# Send the new password
@app.route("/pwreset/<id>", methods=["POST"])
def pwreset_post(id):
    """
    update the user's password
    :param id: id of password reset link
    :return: to login page
    """
    # check the new password
    if request.form["password"] != request.form["password2"]:
        flash("Your password and password verification didn't match.", "danger")
        return redirect(url_for("pwreset_get", id=id))
    if len(request.form["password"]) < 1:
        flash("Your password needs to be at least 1 characters", "danger")
        return redirect(url_for("pwreset_get", id=id))

    user_reset = db.session.query(PWReset).filter_by(reset_key=id).one()
    try:
        # update the password
        exists(db.session.query(Admin).filter_by(id=user_reset.user_id)
        .update(
            {'password': request.form["password"], 'password_hash': generate_password_hash(request.form["password"])}))
        db.session.commit()

    except IntegrityError:
        flash("Something went wrong", "danger")
        db.session.rollback()
        return redirect(url_for("login_register_admin"))

    user_reset.has_activated = True
    db.session.commit()
    flash("Your new password is saved.", "success")
    return redirect(url_for("login_register_admin"))


# -------------------END admin-------------------------------


"""if __name__ == "__main__":
    app.run(debug=True)
"""
