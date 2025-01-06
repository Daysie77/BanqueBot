from flask import Flask, request, render_template, jsonify, flash, session, redirect, url_for
from googleapiclient.discovery import build
import speech_recognition as sr
import re
import pymysql
import nltk
import pyttsx3
import os
from flask_bcrypt import Bcrypt
import requests
import time
# import torch
# from PIL import Image
# from transformers import MllamaForConditionalGeneration, AutoProcessor
# import ollama
# import openai
# from openai import OpenAI
from werkzeug.utils import secure_filename

nltk.download('punkt')
nltk.download('stopwords')

def generate_secret_key():
    return os.urandom(24)

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = generate_secret_key()

# Configuration de la clé API YouTube
youtube_api_key = 'AIzaSyB6-ZeoQYbdLi5scEbmpQRX-CJ_acupzlQ'
youtube = build('youtube', 'v3', developerKey=youtube_api_key)

# Centralisation de la connexion à la base de données
def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='',
        db='bd_final_chat',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    
# Téléchargement de photo de profil

UPLOAD_FOLDER_PARENT = 'static/uploads/images_profil_parent'
app.config['UPLOAD_FOLDER_PARENT'] = UPLOAD_FOLDER_PARENT
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'xlsx', 'xls', 'pdf', 'txt'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/update_profile_image', methods=['POST'])
def update_profile_image():
    if 'user_id' not in session:
        return redirect(url_for('connexion'))
    
    file = request.files.get('profileImage')
    if not file or file.filename == '':
        flash('Aucun fichier sélectionné', 'danger')
        return redirect(url_for('profil'))
    
    if allowed_file(file.filename):
        os.makedirs(app.config['UPLOAD_FOLDER_PARENT'], exist_ok=True)
        timestamp = int(time.time())
        filename = secure_filename(file.filename)
        unique_filename = f"{filename}_{timestamp}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER_PARENT'], unique_filename)
        file.save(file_path)
        
        full_image_path = os.path.normpath(os.path.join('uploads/images_profil_parent', unique_filename)).replace('\\', '/')
        user_id = session.get('user_id')
        
        if user_id:
            connection = get_db_connection()
            try:
                with connection.cursor() as cursor:
                    sql = "UPDATE users SET profileImage = %s WHERE id = %s"
                    cursor.execute(sql, (full_image_path, user_id))
                    connection.commit()
                    flash('Photo de profil mise à jour avec succès!', 'success')
            except pymysql.Error as e:
                flash(f'Erreur lors de la mise à jour du profil : {str(e)}', 'danger')
            finally:
                connection.close()
        else:
            flash('Erreur ID de l\'utilisateur', 'danger')
    return redirect(url_for('profil'))

# Fin traitement de photo de profil


# debut traitement télécharger fichier


# debut traitement télécharger fichier

@app.route('/')
def index():
    return render_template('accueil.html')

@app.route('/profil', methods=['GET', 'POST'])
def profil():
    if 'user_id' not in session:
        return redirect(url_for('connexion'))
    
    user_id = session['user_id']
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT nom, email, username, profileImage FROM users WHERE id = %s"
            cursor.execute(sql, (user_id,))
            user = cursor.fetchone()

            if request.method == 'POST':
                nom = request.form['nom']
                username = request.form['username']
                email = request.form['email']
                password = request.form.get('password')

                if password:
                    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
                    update_sql = "UPDATE users SET nom = %s, username = %s, email = %s, password = %s WHERE id = %s"
                    cursor.execute(update_sql, (nom, username, email, hashed_password, user_id))
                else:
                    update_sql = "UPDATE users SET nom = %s, username = %s, email = %s WHERE id = %s"
                    cursor.execute(update_sql, (nom, username, email, user_id))

                connection.commit()
                flash('Profil mis à jour avec succès', 'success')
                return redirect(url_for('profil'))
            
            if user:
                return render_template('users/profil.html', user=user)
            else:
                flash('Utilisateur non trouvé', 'danger')
                return redirect(url_for('connexion'))

    except pymysql.Error as e:
        flash(f'Erreur lors de la récupération des informations de l\'utilisateur : {str(e)}', 'danger')
        return redirect(url_for('connexion'))
    finally:
        connection.close()

@app.route('/inscription', methods=['GET', 'POST'])
def inscription():
    connection = get_db_connection()
    cursor = connection.cursor()

    if request.method == 'POST':
        nom = request.form['nom']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash("Les mots de passe ne sont pas identiques !", 'info')
            return redirect(url_for('inscription'))

        select_query = "SELECT id FROM users WHERE email = %s"
        cursor.execute(select_query, (email,))
        user_exist = cursor.fetchone()

        if user_exist:
            flash("Cet utilisateur existe déjà. Veuillez entrer un autre email.", 'danger')
        else:
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            default_profile_image = 'uploads/images_profil_parent/bot_avatar.jpg'
            insert_query = "INSERT INTO users (nom, username, email, password, profileImage) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(insert_query, (nom, username, email, hashed_password, default_profile_image))
            connection.commit()
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            user_id = cursor.fetchone()['id']
            session['user_id'] = user_id
            flash('Inscription réussie! Connectez-vous maintenant.', 'success')
            return redirect(url_for('connexion'))
    return render_template('users/inscrip.html')

@app.route('/connexion', methods=['GET', 'POST'])
def connexion():
    connection = get_db_connection()
    cursor = connection.cursor()

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        select_query = "SELECT id, nom, username, email, password FROM users WHERE email = %s"
        cursor.execute(select_query, (email,))
        user = cursor.fetchone()

        if user and bcrypt.check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            flash('Connexion réussie!', 'success')
            return redirect(url_for('interface'))
        else:
            flash('Email ou mot de passe incorrect', 'danger')

    return render_template('users/cone.html')

@app.route('/Interface')
def interface():
    if 'user_id' in session:
        user_id = session['user_id']
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                sql = "SELECT nom, email, profileImage FROM users WHERE id = %s"
                cursor.execute(sql, (user_id,))
                user = cursor.fetchone()
                if user:
                    return render_template('clone_chatgpt.html', user=user)
                else:
                    flash('Utilisateur non trouvé', 'danger')
                    return redirect(url_for('connexion'))
        except pymysql.Error as e:
            flash(f'Erreur lors de la récupération des informations de l\'utilisateur : {str(e)}', 'danger')
            return redirect(url_for('connexion'))

        finally:
            connection.close()
    else:
        return redirect(url_for('connexion'))


@app.route('/Déconnexion', methods=['POST'])
def deconnexion():
    if request.method == 'POST' and 'confirm' in request.form and request.form['confirm'] == 'yes':
        session.pop('user_id', None)
        flash('Déconnexion réussie!', 'success')
        return redirect(url_for('connexion'))
    return redirect(url_for('interface'))

@app.route('/confirmation_deconnexion')
def deco():
    if 'user_id' in session:
        user_id = session['user_id']
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                sql = "SELECT nom, email, profileImage FROM users WHERE id = %s"
                cursor.execute(sql, (user_id,))
                user = cursor.fetchone()
                if user:
                    return render_template('users/deco.html', user=user)
                else:
                    flash('Utilisateur non trouvé', 'danger')
                    return redirect(url_for('connexion'))
        except pymysql.Error as e:
            flash(f'Erreur lors de la récupération des informations de l\'utilisateur : {str(e)}', 'danger')
        finally:
            connection.close()
    else:
        return redirect(url_for('connexion'))



# Route pour le chat, prend en charge à la fois l'entrée vocale et textuelle
@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.form.get('user_input', '')
    user_id = session.get('user_id')
    conversation_id = request.form.get('conversation_id')  # L'ID de la conversation doit être envoyé depuis le frontend

    if not user_id or not conversation_id:
        return jsonify({'error': 'User or conversation not found'}), 400

    # Gestion du fichier envoyé
    file_url = None
    if 'file' in request.files:
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER_PARENT'], filename)
            file.save(file_path)
            # Générer l'URL publique du fichier
            file_url = url_for('static', filename=f'uploads/images_profil_parent/{filename}')

    # Enregistrement dans la base de données
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            # Sauvegarder le message de l'utilisateur
            save_conversation_to_database(user_input, 'user', conversation_id, cursor, conn, file_url)

            # Traitement de la réponse du bot
            bot_response = process_user_input(user_input, user_id)
            save_conversation_to_database(bot_response, 'bot', conversation_id, cursor, conn)

    return jsonify({
        'response': bot_response,
        'file_url': file_url
    })


# Fonction pour traiter l'entrée utilisateur (textuelle ou vocale) avec le chatbot
def process_user_input(user_input, user_id):
    # Traiter avec le chatbot et synthèse vocale
    bot_response = talk_to_daysie(user_input, user_id)
    return bot_response



## Initialisation du client OpenAI avec les paramètres pour Hugging Face ####################

# client = OpenAI(
#     base_url="https://api-inference.huggingface.co/v1/",
#     api_key="hf_YfGAQGotEqZEKGuLllSBBqXXXXXXXXXXXX"  # Remplacez par votre clé d'API Hugging Face
# )

# def talk_to_daysie(user_input, user_id):
#     with get_db_connection() as conn:
#         with conn.cursor() as cursor:
#             # Récupérer ou créer une conversation
#             cursor.execute("SELECT id FROM conversations WHERE user_id = %s ORDER BY created_at DESC LIMIT 1", (user_id,))
#             conversation = cursor.fetchone()

#             if not conversation:
#                 sql_insert_conversation = "INSERT INTO conversations (user_id, title) VALUES (%s, %s)"
#                 conversation_data = (user_id, generate_conversation_title(user_input))
#                 cursor.execute(sql_insert_conversation, conversation_data)
#                 conn.commit()
#                 conversation_id = cursor.lastrowid
#             else:
#                 conversation_id = conversation['id']

#             save_conversation_to_database(user_input, 'user', conversation_id, cursor, conn)

#             # Préparation des messages pour l'API de Hugging Face
#             messages = [
#                 {"role": "user", "content": user_input}
#             ]

#             # Envoi de la requête au modèle Llama-2-7b-chat-hf
#             try:
#                 stream = client.chat.completions.create(
#                     model="meta-llama/Llama-2-7b-chat-hf",
#                     messages=messages,
#                     max_tokens=500,
#                     stream=True
#                 )

#                 bot_response = ""
#                 for chunk in stream:
#                     bot_response += chunk.choices[0].delta.content

#                 # Sauvegarde de la réponse du bot dans la base de données
#                 save_conversation_to_database(bot_response, 'bot', conversation_id, cursor, conn)

#                 # Synthèse vocale avec pyttsx3
#                 engine = pyttsx3.init()
#                 voices = engine.getProperty('voices')
#                 for voice in voices:
#                     if "female" in voice.name.lower():
#                         engine.setProperty('voice', voice.id)
#                         break
#                 engine.say(bot_response)
#                 engine.runAndWait()

#                 return bot_response

#             except Exception as e:
#                 error_message = f"Erreur de communication avec le modèle Llama-2: {str(e)}"
#                 save_conversation_to_database(error_message, 'bot', conversation_id, cursor, conn)
#                 return error_message
            
            
            
# #############################################################            
# from huggingface_hub import login

# # # Modèle et jeton
# MODEL_ID = "meta-llama/Llama-3.2-90B-Vision-Instruct"
# TOKEN = "hf_mbkgFkvhRPvGjLVhZiFvClXXXXXXXXXXX"  # Remplacez par votre jeton personnel
# login(token="hf_sSxUFSWBlSTivmtbJHXXXXXXXXXXX")

# # Charger le modèle et le processeur au début pour éviter des rechargements multiples
# model = MllamaForConditionalGeneration.from_pretrained(
#     MODEL_ID,
#     torch_dtype=torch.bfloat16,
#     device_map="auto",
#     token=TOKEN
# )
# processor = AutoProcessor.from_pretrained(MODEL_ID, token=TOKEN)



# def talk_to_daysie(user_input, user_id, image_url=None):
#     # Connexion à la base de données
#     with get_db_connection() as conn:
#         with conn.cursor() as cursor:
#             # Récupérer ou créer une conversation
#             cursor.execute("SELECT id FROM conversations WHERE user_id = %s ORDER BY created_at DESC LIMIT 1", (user_id,))
#             conversation = cursor.fetchone()

#             if not conversation:
#                 sql_insert_conversation = "INSERT INTO conversations (user_id, title) VALUES (%s, %s)"
#                 conversation_data = (user_id, generate_conversation_title(user_input))
#                 cursor.execute(sql_insert_conversation, conversation_data)
#                 conn.commit()
#                 conversation_id = cursor.lastrowid
#             else:
#                 conversation_id = conversation['id']

#             save_conversation_to_database(user_input, 'user', conversation_id, cursor, conn)

#             # Préparer les entrées pour le modèle
#             try:
#                 if image_url:
#                     # Si une image est fournie, la télécharger
#                     image = Image.open(requests.get(image_url, stream=True).raw)
#                 else:
#                     image = None

#                 # Construire les messages utilisateur
#                 messages = [
#                     {"role": "system", 
#                      "content": "Tu es un assistant virtuel spécialisé dans le domaine bancaire, travaillant pour la Société Générale Côte d'Ivoire.\
#                             Tu es capable de répondre à toutes les questions concernant les services financiers, les produits bancaires, les crédits,\
#                             les investissements et la gestion de compte. Tu excelles à offrir des conseils personnalisés et des informations précises, \
#                             en mettant en avant les offres et services spécifiques de la Société Générale Côte d'Ivoire."
#                     },
#                     {"role": "user", "content": user_input}
#                 ]

#                 input_text = processor.apply_chat_template(messages, add_generation_prompt=True)
#                 inputs = processor(
#                     image,
#                     input_text,
#                     add_special_tokens=False,
#                     return_tensors="pt",
#                 ).to(model.device)

#                 # Générer la réponse
#                 output = model.generate(**inputs, max_new_tokens=500)
#                 bot_response = processor.decode(output[0])

#             except Exception as e:
#                 # En cas d'erreur, enregistrer l'erreur dans la base de données et renvoyer un message d'erreur
#                 error_message = f"Erreur de communication avec le modèle Hugging Face : {str(e)}"
#                 save_conversation_to_database(error_message, 'bot', conversation_id, cursor, conn)
#                 return error_message

#             # Sauvegarder la réponse du bot dans la base de données
#             save_conversation_to_database(bot_response, 'bot', conversation_id, cursor, conn)

#             # Synthèse vocale avec pyttsx3 (si nécessaire)
#             engine = pyttsx3.init()
#             voices = engine.getProperty('voices')
#             for voice in voices:
#                 if "female" in voice.name.lower():
#                     engine.setProperty('voice', voice.id)
#                     break
#             engine.say(bot_response)
#             engine.runAndWait()

#            return bot_response

## Initialisation du client OpenAI avec les paramètres pour Hugging Face ####################

# ############# Fonction avec API de openai #############################
# Initialisation du client OpenAI avec l'ID de votre organisation et de votre projet
# client = OpenAI(
#   organization='org-xz6mbRZjn0nOElF26XXXXXXXXXX',
#   api_key="sk-proj-_4zPzHR7GRvyouYExdWWhUZmbFf85KDqJTNEYO9xxxxxxxxxxxxx",

# )

# def talk_to_daysie(user_input, user_id):
#     # Connexion à la base de données
#     with get_db_connection() as conn:
#         with conn.cursor() as cursor:
#             # Récupérer ou créer une conversation
#             cursor.execute("SELECT id FROM conversations WHERE user_id = %s ORDER BY created_at DESC LIMIT 1", (user_id,))
#             conversation = cursor.fetchone()

#             if not conversation:
#                 sql_insert_conversation = "INSERT INTO conversations (user_id, title) VALUES (%s, %s)"
#                 conversation_data = (user_id, generate_conversation_title(user_input))
#                 cursor.execute(sql_insert_conversation, conversation_data)
#                 conn.commit()
#                 conversation_id = cursor.lastrowid
#             else:
#                 conversation_id = conversation['id']

#             save_conversation_to_database(user_input, 'user', conversation_id, cursor, conn)

#             # Définir les messages pour OpenAI, y compris le rôle de l'assistant bancaire
#             messages = [
#                 {
#                     "role": "system",
#                     "content": "Tu es un assistant virtuel spécialisé dans le domaine bancaire, travaillant pour la Société Générale Côte d'Ivoire.\
#                         Tu es capable de répondre à toutes les questions concernant les services financiers, les produits bancaires, les crédits,\
#                         les investissements et la gestion de compte. Tu excelles à offrir des conseils personnalisés et des informations précises, \
#                         en mettant en avant les offres et services spécifiques de la Société Générale Côte d'Ivoire."
#                 },
#                 {
#                     "role": "user",
#                     "content": user_input
#                 }
#             ]

#             try:
#                 # Envoi de la requête à l'API OpenAI
#                 response = client.chat.completions.create(
#                     model="gpt-4o-mini",  # Remplacez par le modèle approprié si nécessaire
#                     messages=messages,
#                     temperature=0.7
#                 )

#                 # Récupération de la réponse de l'assistant
#                 bot_response = response.choices[0].message.content

#             except Exception as e:
#                 # En cas d'erreur, enregistrer l'erreur dans la base de données et renvoyer un message d'erreur
#                 error_message = f"Erreur de communication avec l'API OpenAI: {str(e)}"
#                 save_conversation_to_database(error_message, 'bot', conversation_id, cursor, conn)
#                 return error_message

#             # Sauvegarder la réponse du bot dans la base de données
#             save_conversation_to_database(bot_response, 'bot', conversation_id, cursor, conn)

#             # Synthèse vocale avec pyttsx3 (si nécessaire)
#             engine = pyttsx3.init()
#             voices = engine.getProperty('voices')
#             for voice in voices:
#                 if "female" in voice.name.lower():
#                     engine.setProperty('voice', voice.id)
#                     break
#             engine.say(bot_response)
#             engine.runAndWait()

#             return bot_response

############# Fonction avec API de openai #############################

############# Fonction avec API de together #############################

# from together import Together

# def talk_to_daysie(user_input, user_id):
#     # Connexion à la base de données
#     with get_db_connection() as conn:
#         with conn.cursor() as cursor:
#             # Récupérer ou créer une conversation
#             cursor.execute("SELECT id FROM conversations WHERE user_id = %s ORDER BY created_at DESC LIMIT 1", (user_id,))
#             conversation = cursor.fetchone()

#             if not conversation:
#                 sql_insert_conversation = "INSERT INTO conversations (user_id, title) VALUES (%s, %s)"
#                 conversation_data = (user_id, generate_conversation_title(user_input))
#                 cursor.execute(sql_insert_conversation, conversation_data)
#                 conn.commit()
#                 conversation_id = cursor.lastrowid
#             else:
#                 conversation_id = conversation['id']

#             save_conversation_to_database(user_input, 'user', conversation_id, cursor, conn)
            
#             # Set the API key as an environment variable
#             os.environ["TOGETHER_API_KEY"] = "1ab9e53eb3620d0eb9fff72b29a9385ac3c43064fa3e1XXXXXXXXXXXXXXX"

#             # Initialize the Together client without API_KEY argument
#             client = Together()
            
#             try:
#                 response = client.chat.completions.create(
#                     model="meta-llama/Llama-Vision-Free",
#                     messages=[
#                         {
#                             "role": "system",
#                             "content": "Tu es un assistant virtuel spécialisé dans le domaine bancaire, travaillant pour la Société Générale.\
#                                 Tu es capable de répondre à toutes les questions concernant les services financiers, les produits bancaires, \
#                                 les crédits, les investissements et la gestion de compte. Tu excelles à offrir des conseils personnalisés et \
#                                 des informations précises, en mettant en avant les offres et services spécifiques de la Société Générale. \
#                                 Tu vas sur le site google << https://wwww.google.com >> pour prendre des informations plus précises.\
#                                 Tu dois limiter tes réponses en donnant seulement les informations essentielles à moins que l'utilisateur te demande plus de précision."
#                         },
#                         {
#                             "role": "user",
#                             "content": user_input
#                         }
#                     ],
#                     max_tokens=500,
#                     temperature=0.7,
#                     top_p=0.7,
#                     top_k=50,
#                     repetition_penalty=1,
#                     stop=["<|eot_id|>", "<|eom_id|>"],
#                     stream=True
#                 )

#                 # Accumuler la réponse dans une variable
#                 bot_response = ""
#                 for token in response:
#                     if (
#                         hasattr(token, 'choices') and token.choices and 
#                         hasattr(token.choices[0], 'delta') and hasattr(token.choices[0].delta, 'content')
#                     ): 
#                         bot_response += token.choices[0].delta.content

#                 print(f"Réponse API : {bot_response}")  # Debug uniquement, à supprimer si non nécessaire

#             except Exception as e:
#                 # En cas d'erreur, enregistrer l'erreur dans la base de données et renvoyer un message d'erreur
#                 error_message = f"Erreur de communication avec l'API Together.AI : {str(e)}"
#                 save_conversation_to_database(error_message, 'bot', conversation_id, cursor, conn)
#                 return error_message

#             # Sauvegarder la réponse du bot dans la base de données
#             save_conversation_to_database(bot_response, 'bot', conversation_id, cursor, conn)

#             # Synthèse vocale avec pyttsx3
#             engine = pyttsx3.init()
#             voices = engine.getProperty('voices')
#             for voice in voices:
#                 if "female" in voice.name.lower():
#                     engine.setProperty('voice', voice.id)
#                     break
#             engine.say(bot_response)
#             engine.runAndWait()

#             # Retourner la réponse
#             return bot_response

############# Fonction avec API de together #############################

############# Fonction avec API de Ollama #############################
coze_url = 'https://api.coze.com/open_api/v2/chat'
coze_headers = {
    # Remplacez par votre jeton d'accès personnel
    'Authorization': 'Bearer pat_uDtKUUgE40OhQJza8mItCOezv5vkRbxxxxxxxxxxxxx',
    'Content-Type': 'application/json',
    'Accept': '*/*',
    'Host': 'api.coze.com',
    'Connection': 'keep-alive'
}

# Fonction pour parler avec le chatbot et utiliser pyttsx3 pour la synthèse vocale


# def talk_to_daysie(user_input, user_id):
#     # Connection à la base de données
#     with get_db_connection() as conn:
#         with conn.cursor() as cursor:
#             # Récupérer ou créer une conversation
#             cursor.execute("SELECT id FROM conversations WHERE user_id = %s ORDER BY created_at DESC LIMIT 1", (user_id,))
#             conversation = cursor.fetchone()

#             if not conversation:
#                 # Insérer une nouvelle conversation
#                 sql_insert_conversation = "INSERT INTO conversations (user_id, title) VALUES (%s, %s)"
#                 conversation_data = (user_id, generate_conversation_title(user_input))
#                 cursor.execute(sql_insert_conversation, conversation_data)
#                 conn.commit()
#                 conversation_id = cursor.lastrowid
#             else:
#                 conversation_id = conversation['id']

#             # Insérer le message de l'utilisateur
#             save_conversation_to_database(user_input, 'user', conversation_id, cursor, conn)

#             # Appel à l'API Coze
#             data = {
#                 # Assurez-vous que ce soit une chaîne ou un nombre selon les spécifications
#                 "conversation_id": str(conversation_id),
#                 "bot_id": "743598207*****",  # Remplacez par l'ID de votre bot
#                 "user": "290322018****",  # Assurez-vous que l'ID utilisateur est correct
#                 "query": user_input,
#                 "stream": False
#             }

#             # Affichage des données envoyées pour debug
#             print(f"Sending request to Coze API: {data}")
#             response = requests.post(coze_url, headers=coze_headers, json=data)

#             # Affichage de la réponse pour debug
#             print(f"Response status code: {response.status_code}")
#             if response.status_code == 200:
#                 response_json = response.json()
#                 print(f"Response JSON: {response_json}")

#                 if response_json.get('code') == 0:
#                     messages = response_json.get('messages', [])
#                     for message in messages:
#                         if message['type'] == 'answer':
#                             bot_response = message['content']
#                             save_conversation_to_database(
#                                 bot_response, 'bot', conversation_id, cursor, conn)

#                             # Synthèse vocale avec pyttsx3
#                             engine = pyttsx3.init()
#                             voices = engine.getProperty('voices')
#                             for voice in voices:
#                                 if "female" in voice.name.lower():
#                                     engine.setProperty('voice', voice.id)
#                                     break
#                             engine.say(bot_response)
#                             engine.runAndWait()

#                             return bot_response

#                     user_message = "Désolé, je n'ai pas de réponse pour cela."
#                     save_conversation_to_database(user_message, 'bot', conversation_id, cursor, conn)
#                     return user_message
#                 else:
#                     error_message = response_json.get('msg', 'Erreur inconnue')
#                     save_conversation_to_database(
#                         error_message, 'bot', conversation_id, cursor, conn)
#                     return error_message

#             else:
#                 error_message = f"Erreur de communication avec l'api Coze: {response.text}"
#                 save_conversation_to_database(error_message, 'bot', conversation_id, cursor, conn)
#                 return error_message
  
# """"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

def talk_to_daysie(user_input, user_id, file_url=None):
    # Connexion à la base de données
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            # Récupérer ou créer une conversation
            cursor.execute(
                "SELECT id FROM conversations WHERE user_id = %s ORDER BY created_at DESC LIMIT 1", 
                (user_id,)
            )
            conversation = cursor.fetchone()

            if not conversation:
                # Insérer une nouvelle conversation
                sql_insert_conversation = "INSERT INTO conversations (user_id, title) VALUES (%s, %s)"
                conversation_data = (user_id, generate_conversation_title(user_input))
                cursor.execute(sql_insert_conversation, conversation_data)
                conn.commit()
                conversation_id = cursor.lastrowid
            else:
                conversation_id = conversation['id']

            # Insérer le message de l'utilisateur avec ou sans fichier
            save_conversation_to_database(user_input, 'user', conversation_id, cursor, conn, file_url)

            # Appel à l'API Coze
            data = {
                "conversation_id": str(conversation_id),
                "bot_id": "743598207946****",  # Remplacez par l'ID de votre bot
                "user": "2903220******",  # Assurez-vous que l'ID utilisateur est correct
                "query": user_input,
                "stream": False
            }

            # Affichage des données envoyées pour debug
            print(f"Sending request to Coze API: {data}")
            response = requests.post(coze_url, headers=coze_headers, json=data)

            # Affichage de la réponse pour debug
            print(f"Response status code: {response.status_code}")
            if response.status_code == 200:
                response_json = response.json()
                print(f"Response JSON: {response_json}")

                if response_json.get('code') == 0:
                    messages = response_json.get('messages', [])
                    bot_response = None  # Initialisation de la réponse du bot

                    for message in messages:
                        if message['type'] == 'answer':
                            bot_response = message['content']
                            save_conversation_to_database(
                                bot_response, 'bot', conversation_id, cursor, conn
                            )
                            break  # Une seule réponse est traitée

                    if bot_response:
                        # Synthèse vocale avec pyttsx3
                        engine = pyttsx3.init()
                        voices = engine.getProperty('voices')

                        # Sélectionnez une voix féminine, si disponible
                        for voice in voices:
                            if "female" in voice.name.lower():
                                engine.setProperty('voice', voice.id)
                                break

                        # Ajoutez la réponse au moteur vocal et exécutez-la
                        # engine.say(bot_response)
                        # engine.runAndWait()

                        return bot_response

                    # Aucun message de type 'answer' n'a été trouvé
                    user_message = "Désolé, je n'ai pas de réponse pour cela."
                    save_conversation_to_database(user_message, 'bot', conversation_id, cursor, conn)
                    return user_message

                else:
                    # Gestion des erreurs renvoyées par l'API
                    error_message = response_json.get('msg', 'Erreur inconnue')
                    save_conversation_to_database(
                        error_message, 'bot', conversation_id, cursor, conn
                    )
                    return error_message

            else:
                # Gestion des erreurs de communication avec l'API
                error_message = f"Erreur de communication avec l'API Coze: {response.text}"
                save_conversation_to_database(error_message, 'bot', conversation_id, cursor, conn)
                return error_message



############# Fonction avec API de Ollama #############################

# Fonction pour générer un titre de conversation
def generate_conversation_title(user_input):
    return "Conversation - " + user_input[:30]

# Fonction pour sauvegarder la conversation dans la base de données
def save_conversation_to_database(content, sender, conversation_id, cursor, conn, file_url=None):
    """
    Sauvegarde un message (et son fichier, si présent) dans la base de données.
    """
    sql_insert_message = """
        INSERT INTO messages (conversation_id, content, file_url, sender)
        VALUES (%s, %s, %s, %s)
    """
    cursor.execute(sql_insert_message, (conversation_id, content, file_url, sender))
    conn.commit()



# Route pour récupérer les messages d'une conversation spécifique
@app.route('/get_conversations', methods=['GET'])
def get_conversations():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify([])

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('SELECT id, title FROM conversations WHERE user_id = %s', (user_id,))
            conversations = cursor.fetchall()

    return jsonify(conversations)




@app.route('/get_messages/<int:conversation_id>', methods=['GET'])
def get_messages(conversation_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify([])

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            # Vérifier que la conversation appartient à l'utilisateur
            cursor.execute(
                'SELECT id FROM conversations WHERE id = %s AND user_id = %s',
                (conversation_id, user_id)
            )
            conversation = cursor.fetchone()
            if not conversation:
                return jsonify([])

            # Récupérer les messages, y compris les URLs des fichiers
            cursor.execute(
                'SELECT sender, content, file_url FROM messages WHERE conversation_id = %s ORDER BY created_at ASC',
                (conversation_id,)
            )
            messages = cursor.fetchall()

    return jsonify(messages)




@app.route('/conversation/<int:conversation_id>', methods=['GET'])
def conversation(conversation_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('connexion'))

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM conversations WHERE id = %s AND user_id = %s", (conversation_id, user_id))
            conversation = cursor.fetchone()
            if not conversation:
                return "Unauthorized", 403

            cursor.execute(
                "SELECT content, sender FROM messages WHERE conversation_id = %s", (conversation_id,))
            messages = cursor.fetchall()
            cursor.execute(
                "SELECT nom, profileImage FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()

    return render_template('clone_chatgpt.html', messages=messages, conversation_id=conversation_id, user=user)


@app.route('/start_new_conversation', methods=['POST'])
def start_new_conversation():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('connexion'))

    data = request.get_json()
    conversation_title = data.get('title')
    if not conversation_title:
        return jsonify({'error': 'Titre de la conversation requis'}), 400

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            sql_insert_conversation = "INSERT INTO conversations (user_id, title) VALUES (%s, %s)"
            cursor.execute(sql_insert_conversation, (user_id, conversation_title))
            conn.commit()
            conversation_id = cursor.lastrowid

    return jsonify({'conversation_id': conversation_id, 'title': conversation_title})



if __name__ == '__main__':
    app.run(debug=True)
