import requests
import json

def get_infinitif(phrase,nlp):
    """

    :param phrase: une phrase
    :param nlp: fonction de la librairie Spacy
    :return: une phrase dans laquelle les auxilliaires et les verbes sont à l'infinitif
    """
    # Analyse la phrase

    doc = nlp(phrase)
    new_sentence = [str(token) for token in doc]

    for index in range(len(doc)):
        print(doc[index].text, doc[index].pos_)
        # Vérifie si le token est un verbe et affiche sa forme infinitive

        # si un verbe est précédé d'un auxillaire on ne le traduit pas
        if doc[index].pos_ == "VERB":
            if doc[index - 1].pos_ != "AUX":
                new_sentence[index] = doc[index].lemma_

        elif doc[index].pos_ == "AUX":
            new_sentence[index] = doc[index].lemma_

    new_sentence = " ".join([str(i) for i in new_sentence])
    return new_sentence


def get_pos(mot,nlp):
    """
    Obtenir le PoS Tagging d'un mot
    :param mot: le mot
    :param nlp: fonction de la librairie Spacy
    :return: le PoS Tagging d'un mot 'AUX'/'VERB'/'GroupNom'
    """
    # Analyse la phrase
    doc = nlp(mot)

    if len(doc) == 1:
        return str(doc[0].pos_)
    else:
        #if le mot est un groupe nominal
        return 'GroupNom'

def getKeywords(interpretation, api_sign_base):
    """
    Obtenir les mots clés
    :param interpretation: liste des interprétations possibles du mot
    :param api_sign_base: point api pour la traduction d'un signe
    :return: une liste avec toutes les données sur les signes correspondant,
             un dictionnaire {'gloss' :[mot-clé,..],..}

    """
    dico_of_gloss_keyword = {}
    all_traduction_data = []
    for word in interpretation:
        requete = api_sign_base + word
        response_API = requests.get(requete)
        print(requete)
        data = response_API.text
        parse_json = json.loads(data)
        traduction_list = parse_json
        all_traduction_data += traduction_list


        for choice in traduction_list:
            dico_of_gloss_keyword[choice['_gloss']] = str(choice['_keywords']).split(", ")

    return all_traduction_data, dico_of_gloss_keyword