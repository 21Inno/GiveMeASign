from . import app
from . import db

from flask import Flask, redirect, jsonify, request, Response, render_template, url_for, flash, send_file
from flask_cors import CORS
import requests
import json
import os, binascii
from werkzeug.utils import secure_filename
import fnmatch
import spacy
import fr_core_news_sm
from .forms import RegisterAdminForm, LoginAdminForm, GroupeForm, EditGroupeForm
from .models import User, Group, UserHistory, Sign, sign_to_dict, SignProposition,prop_to_dict, group_Public, anonyme_user, Admin
from flask_login import login_required, login_user, logout_user, current_user
from .utils import *
from datetime import datetime
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
    nature_du_mot = get_pos(mot_select, nlp)

    #
    if nature_du_mot in ['VERB', 'AUX']:
        # mettre tous les verbes et auxillaires à l'infinitif
        new_phrase = get_infinitif(phrase, nlp)
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
            lemme.append(get_infinitif(mot, nlp))

        # eliminer les doublons
        lemme = list(set(lemme))

    elif nature_du_mot == 'GroupNom':
        lemme.append(mot_select)

    # -------------------------Recherche dans le corpus---------------------------------
    # la liste "lemme" contient maintenant le mot et toutes ses variations possibles
    # recuperer tous les gloss et leurs mots clés

    all_traduction_data, dico_of_gloss_keyword = getKeywords(lemme, api_sign_base)

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
    # good_sign_proposition = []        # lievre lievre1
    # for lem in lemme input :
    print(lemme_input)
    filters = [SignProposition.gloss.like(f'%{word}%') for word in lemme_input]
    print("filter : ", filters)

    good_sign_proposition = []

    if len(filters) != 0:
        proposition_object = SignProposition.query.filter(
            db.and_(*filters, SignProposition.group_name == _current_group)).all()
        for prop in proposition_object:
            good_sign_proposition.append((prop.gloss, prop.url, prop.keywords, prop.author_name, str(prop.group_name)))

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
    if current_user.is_authenticated:

        current_group = current_user.group.name
        _current_user = current_user.username
    else:
        current_group = "Public"
        _current_user = "ano"
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
                                      author_name=_current_user)
        db.session.add(proposition)
        db.session.commit()
        return 'File uploaded successfully'
    return render_template("record.html", mot=mot, group=current_group)


@app.route('/expert_main', methods=['GET', 'POST'])
def expert_main():
    if current_user.is_authenticated:
        current_group = current_user.group.name
        current_username = current_user.username

    else:
        current_group = "Public"
        current_username = "ano"

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


@app.route('/gifsAPI/<current_group>/<mot>/<filename>')
def get_gif(filename, mot, current_group):
    directory_gif2 = os.path.abspath(
        os.path.dirname(__file__)) + "\\static\\gifs\\" + current_group + "\\gifs_" + mot
    file_path = os.path.join(directory_gif2, filename)
    return send_file(file_path, mimetype='image/gif')


# -------------------------End translate views-----------------------

# --------------------------User features--------------------------------
@app.route('/login', methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        if current_user.role == "admin":
            # si l'utilisateur connecté est un admin, on le déconnecte pour
            # permettre la connection d'un user normal
            logout_user()
            # return redirect(url_for("login_admin"))
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
                user = User(username=_username_final, role="admin", group=group)
        else:
            if user.group_id != group.id:
                _username_final = group.name + '_' + _username
                user = User(username=_username, role="normal", group=group)

        # Add the user in the dict of users
        db.session.add(user)
        db.session.commit()
        login_user(user)
        memo_current_user[user] = [user.group.name, user.username]
        print('login done')

        next_page = request.args.get('next')
        if next_page:
            next_page = url_for('dashboard')
            print("ici" + str(next_page))
            return redirect(next_page)
        print("post")
        return jsonify({"group_user": _group, "username_user": _username})
        # return redirect(next_page)
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

    print(_current_group, _current_username)
    print(_current_user)
    print(_gloss_name, _keywords, _url)

    # datetime object containing current date and time
    now = datetime.now()

    new_sign = Sign(gloss=_gloss_name, keywords=_keywords1,
                    url=_url, datetime=now)
    new_user_history = UserHistory(user=_current_user, sign=new_sign)
    old_sign = Sign.query.filter_by(gloss=_gloss_name).first()
    if old_sign is not None:
        old_historique = UserHistory.query.filter_by(sign_id=old_sign.id, user_id=_current_user.id).first()
        db.session.delete(old_sign)
        db.session.delete(old_historique)

    db.session.add(new_sign)
    db.session.add(new_user_history)
    db.session.commit()
    return jsonify("Ajouté à l'historique")


@app.route('/dashboard')
def dashboard():
    if not current_user.is_authenticated:
        # if current_user.role == "admin":
        return redirect(url_for("login"))
    if current_user.role == "admin":
        return redirect(url_for("dashboard_admin"))
    my_history = []
    for hist in current_user.history:
        sign = Sign.query.filter_by(id=hist.sign_id).first()
        my_history.append(sign_to_dict(sign))

    print(my_history)
    my_history1 = my_history[::-1]
    print(my_history1)

    print(current_user.group)
    return render_template("dashboard.html", user=current_user, my_history=my_history1)


# Route for deleting a movie from my list
@app.route("/delete_in_history/<int:identifiant>", methods=["GET"])
@login_required
def delete(identifiant):
    _sign = Sign.query.get(identifiant)
    _historique = UserHistory.query.filter_by(sign_id=identifiant, user_id=current_user.id).first()

    # Check if the current_user has the movie in my list
    if _historique is not None:
        db.session.delete(_historique)
        db.session.delete(_sign)
        db.session.commit()

    return redirect(url_for("dashboard"))


@app.route('/logout', methods=["GET", "POST"])
def logout():
    logout_user()
    memo_current_user.popitem()
    return jsonify({"login_state": "false"})

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

    form = RegisterAdminForm()
    if form.validate_on_submit():
        # Add the user in the dict of users
        user = Admin(username=form.username.data, role="admin", email=form.email.data, password=form.password.data)

        db.session.add(user)
        db.session.commit()
        flash("Congratulations, you are now a registered user!", "info")

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
            # si l'utilisateur connecté est un user normal, on le déconnecte pour
            # permettre la connection de l'admin
            logout_user()
    # Form data
    form = LoginAdminForm()
    if form.validate_on_submit():

        admin = Admin.query.filter_by(username=form.username.data).first()
        if admin is None:
            flash("You are not registered yet.", "log_warning")
            return redirect(url_for("login_admin"))

        if not admin.check_password(form.password.data):
            flash("Username or password incorrect.", "log_warning")
            return redirect(url_for("login_admin"))

        # Ok for log in
        login_user(admin)
        flash("Logged in successfully.", "info")

        return redirect(url_for("dashboard_admin"))

    # GET
    return redirect(url_for("login_register_admin"))


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
        return redirect(url_for("login_admin"))
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
        group = Group(name=form.name.data, description=form.description.data, password=form.password.data,
                      admin_id=current_user.id)
        # add the admin as a simple user in the group
        _username_final = group.name + '_' + current_user.username

        user = User(username=_username_final, role="admin", group=group)
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
        _group.password = form.password.data

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
    liste=[]
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
    
    _sign = Sign.query.get(identifiant)
    _video = SignProposition.query.filter_by(id=identifiant).first()

    # Check if the current_user has the movie in my list
    if _video is not None:
        db.session.delete(_video)
        db.session.delete(_sign)
        db.session.commit()

    return redirect(url_for("dashboard_admin"))

@app.route('/logout_admin', methods=["GET", "POST"])
def logout_admin():
    logout_user()
    return redirect(url_for("index"))


# -------------------END admin-------------------------------


if __name__ == "__main__":
    app.run(debug=True)
