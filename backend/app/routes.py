from . import app
from . import db

from sqlalchemy import text, distinct

from flask import Flask, redirect, jsonify, request, Response, render_template, url_for, flash
from flask_cors import CORS
import requests
import json
import os, binascii
from werkzeug.utils import secure_filename
import fnmatch
import spacy
import fr_core_news_sm
# from init import app

from .models import User, Group, UserHistory, Sign, sign_to_dict
from flask_login import login_required, login_user, logout_user, current_user
from werkzeug.urls import url_parse
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from .utils import *
import websocket

dico = {}
nlp = spacy.load("fr_core_news_sm")
CORS(app, resources=r'/*')


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
    # print(final_gloss_dict)

    # get a list of sign
    requete_gif_list = [(trad['_gloss'], api_gif_base + trad['_url'], final_gloss_dict[trad['_gloss']]) for trad in
                        all_traduction_data if trad['_gloss'] in list(final_gloss_dict.keys())]
    print(jsonify(requete_gif_list))

    return jsonify(requete_gif_list)

    # Ensure that the API returns a 200 (OK) status code
    # print('ok get')


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
    if request.method == 'POST':

        directory = os.path.abspath(os.path.dirname(__file__)) + "/static/videos"
        if not os.path.isdir(directory):
            os.mkdir(directory)

        # create a directory to save the video if
        # it not already existed
        directory2 = os.path.abspath(os.path.dirname(__file__)) + "/static/videos/" + "videos_" + mot

        if not os.path.isdir(directory2):
            os.mkdir(directory2)
        # print(request.files)

        # check if there is a video file
        if 'video' not in request.files:
            return 'No video file provided'

        video_file = request.files.get('video')
        filename = secure_filename(video_file.filename)  # permet de securiser le fichier

        # on va nommer les videos par leur nom + un identifiant
        # en fonction de leur ordre de sauvegarde dans le dossier
        count = len(fnmatch.filter(os.listdir(directory2), '*.*'))
        path = os.path.join(directory2, filename + "_" + str(count) + '.mp4')
        try:
            if not video_file.filename + str(count) in dico["videos_" + mot]:
                dico["videos_" + mot].append(video_file.filename + str(count))
        except:
            dico["videos_" + mot] = [video_file.filename + str(count)]
        print(dico)
        video_file.save(path)  # enregistrement de la vidéo

        return 'File uploaded successfully'
    return render_template("record.html", mot=mot)


@app.route('/', methods=['GET', 'POST'])
def expert_main():
    main_folder = 'app/static/videos/'

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
    directory = 'app/static/videos/videos_' + sub
    videos_ = [f for f in os.listdir(directory) if f.endswith('.mp4')]
    return render_template('video_for_sign.html', videos=videos_, word=sub)


# Login
@app.route('/login', methods=["GET", "POST"])
def login_to_group():
    if request.method == 'POST':
        _group = request.form['group-name']
        _username = request.form['username']
        _password = request.form['password']
        group = Group.query.filter_by(name=_group).first()
        user = User.query.filter_by(username=_username).first()
        print(_group, _username, _password)
        if group is None:
            # flash("You are not registered yet.", "log_warning")
            print("pas de group")
            return redirect(url_for("login_to_group"))

        if not group.check_password(_password):
            print("bad pwd")
            # flash("GroupName or password incorrect.", "log_warning")
            return redirect(url_for("login_to_group"))

        if user is None:
            user = User(username=_username, role='normal', group=group)
        else:
            if user.group_id != group.id:
                user = User(username=_username, role='normal', group=group)
        login_user(user)
        print('login done')

        # Add the user in the dict of users
        db.session.add(user)
        db.session.commit()

        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('dashboard')
            print("ici")
        #ws = websocket.create_connection("http://127.0.0.1:5000/")
        #ws.send(json.dumps({'user_logged_in': True}))

        return redirect(next_page)

    return render_template('login.html')


@app.route('/dashboard')
@login_required
def dashboard():
    my_history = []
    for hist in current_user.history:
        sign = Sign.query.filter_by(id=hist.sign_id).first()
        my_history.append(sign_to_dict(sign))
    print(my_history)
    return render_template("dashboard.html", user=current_user, my_history=my_history)
    # return 'Welcome to the dashboard!'


if __name__ == "__main__":
    app.run(debug=True)
