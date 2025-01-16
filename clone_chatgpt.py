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
            file_url = url_for('static', filename=f'uploads/images_profil_parent/{filename}', _external=True)

    # Enregistrement dans la base de données
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            # Sauvegarder le message de l'utilisateur
            # save_conversation_to_database(user_input, 'user', conversation_id, cursor, conn, file_url)

            # Traitement de la réponse du bot
            bot_response = process_user_input(user_input, user_id, file_url)

    return jsonify({
        'response': bot_response,
        'file_url': file_url
    })


# Fonction pour traiter l'entrée utilisateur (textuelle ou vocale) avec le chatbot
def process_user_input(user_input, user_id, file_url=None):
    # Traiter avec le chatbot et synthèse vocale
    bot_response = talk_to_daysie(user_input, user_id, file_url)
    return bot_response


coze_url = 'https://api.coze.com/open_api/v2/chat'
coze_headers = {
    # Remplacez par votre jeton d'accès personnel
    'Authorization': 'Bearer pat_rqXTegZKq9iN35WPhDFSlyFr1yfSR66IQe2inmeuytTUM7y0FRRPwTF9BCoC20NM',
    'Content-Type': 'application/json',
    'Accept': '*/*',
    'Host': 'api.coze.com',
    'Connection': 'keep-alive'
}


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
                "bot_id": "7457826308001693701",  # Remplacez par l'ID de votre bot
                "user": "29032201862555",  # Assurez-vous que l'ID utilisateur est correct
                "query": user_input,
                "stream": False,
                "file_url": file_url  # Inclure l'URL du fichier dans les données de requête
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
                    #bot_response = None  # Initialisation de la réponse du bot

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
                'SELECT content, file_url, sender FROM messages WHERE conversation_id = %s ORDER BY created_at ASC',
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
                "SELECT content, file_url, sender FROM messages WHERE conversation_id = %s", (conversation_id,))
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
