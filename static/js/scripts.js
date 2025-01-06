let currentConversationId = null;
let recognition;
let isRecording = false;

document.addEventListener("DOMContentLoaded", function () {
    loadConversations();

    const conversationId = getCurrentConversationIdFromURL();
    if (conversationId) {
        loadMessages(conversationId);
    }

});

// Code lorsqu'on clique sur une conversation elle reste sélectionnée en rouge
function loadConversations() {
    fetch('/get_conversations')
        .then(response => response.json())
        .then(data => {
            const conversationList = document.getElementById('conversation-list');
            conversationList.innerHTML = ''; // Clear existing list items

            data.forEach(conversation => {
                const listItem = document.createElement('a');
                listItem.href = `javascript:void(0)`; // Prevent page reload
                listItem.className = 'list-group-item list-group-item-action';
                listItem.textContent = conversation.title;
                listItem.dataset.id = conversation.id;

                listItem.addEventListener('click', function () {
                    // Supprimer la classe "selected" de tous les éléments
                    const allItems = document.querySelectorAll('.list-group-item');
                    allItems.forEach(item => item.classList.remove('selected'));

                    // Ajouter la classe "selected" à l'élément cliqué
                    listItem.classList.add('selected');

                    // Charger les messages pour la conversation sélectionnée
                    loadMessages(conversation.id);
                });
                
                conversationList.appendChild(listItem);
            });
        });
}

function getCurrentConversationIdFromURL() {
    const pathParts = window.location.pathname.split('/');
    const lastPathSegment = pathParts[pathParts.length - 1];
    return /^\d+$/.test(lastPathSegment) ? parseInt(lastPathSegment, 10) : null;
}

// Chargement des messages d'une conversation spécifique
function loadMessages(conversation_id) {
    currentConversationId = conversation_id;
    fetch(`/get_messages/${conversation_id}`)
        .then(response => response.json())
        .then(data => {
            const chatlog = document.getElementById('chatlog');
            chatlog.innerHTML = ''; // Clear existing messages

            data.forEach(message => {
                const messageElement = document.createElement('div');
                messageElement.className = `message ${message.sender}`;
                messageElement.innerHTML = `<div class="message-content">${message.content}</div>`;
                chatlog.appendChild(messageElement);
            });
            chatlog.scrollTop = chatlog.scrollHeight;
        });
}




// Fonction pour afficher le pop-up
function showPopup() {
    document.getElementById('titlePopup').style.display = 'block';
}

// Fonction pour cacher le pop-up
function hidePopup() {
    document.getElementById('titlePopup').style.display = 'none';
}

// Fonction pour démarrer une nouvelle conversation avec le titre saisi
function startNewConversation() {
    const conversationTitle = document.getElementById('conversationTitle').value;
    if (conversationTitle.trim() === '') {
        alert('Veuillez saisir un titre pour la conversation.');
        return;
    }

    fetch('/start_new_conversation', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ title: conversationTitle })
    })
        .then(response => response.json())
        .then(data => {
            hidePopup();
            loadConversations();
            currentConversationId = data.conversation_id;
            document.getElementById('chatlog').innerHTML = '';
        })
        .catch(error => console.error('Error:', error));
}

// Envoi de message dans une conversation spécifique
function sendMessage() {
    const userInput = document.getElementById('userInput').value;
    const fileInput = document.getElementById("fileInput");
    const chatlog = document.getElementById('chatlog');

    // Vérifiez si le champ de texte est vide et si aucun fichier n'est sélectionné
    if (userInput.trim() === '' && !fileInput.files[0]) return;

    // Créez un conteneur pour le message utilisateur
    const userMessage = document.createElement('div');
    userMessage.className = 'message user';

    // Affichez le fichier (image ou autre) si présent
    if (fileInput.files[0]) {
        const file = fileInput.files[0];
        const fileContainer = document.createElement('div');
        fileContainer.className = 'file-container'; // Classe CSS pour le style

        if (file.type.startsWith("image/")) {
            const imgPreview = document.createElement("img");
            imgPreview.src = URL.createObjectURL(file);
            imgPreview.alt = "Image envoyée";
            imgPreview.style.maxWidth = "200px";
            imgPreview.style.maxHeight = "200px";
            imgPreview.style.marginBottom = "10px"; // Espacement avec le texte
            fileContainer.appendChild(imgPreview);
        } else {
            const filePreview = document.createElement("div");
            filePreview.textContent = file.name;
            filePreview.style.marginBottom = "10px"; // Espacement avec le texte
            filePreview.style.color = "gray";
            fileContainer.appendChild(filePreview);
        }

        userMessage.appendChild(fileContainer);
    }

    // Affichez le texte en dessous du fichier
    if (userInput.trim() !== '') {
        const userMessageContent = document.createElement('div');
        userMessageContent.className = 'message-content';
        userMessageContent.textContent = userInput;
        userMessage.appendChild(userMessageContent);
    }

    // Ajoutez le message utilisateur au chatlog
    chatlog.appendChild(userMessage);
    chatlog.scrollTop = chatlog.scrollHeight;

    // Préparez les données pour l'envoi
    const formData = new FormData();
    formData.append('user_input', userInput);

    // Assurez-vous que la variable `currentConversationId` est définie avec l'ID de la conversation active
    const conversationId = currentConversationId;  // Si cette variable n'existe pas encore, créez-la avec l'ID de la conversation actuelle
    formData.append('conversation_id', conversationId);  // Ajouter le `conversation_id` à la requête

    if (fileInput.files[0]) {
        formData.append('file', fileInput.files[0], fileInput.files[0].name);
    }

    // Envoyer la requête au serveur
    fetch('/chat', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        // Créez un conteneur pour le message du bot
        const botMessage = document.createElement('div');
        botMessage.className = 'message bot';

        // Afficher le texte du bot
        const botMessageContent = document.createElement('div');
        botMessageContent.className = 'message-content';
        botMessageContent.textContent = data.response;
        botMessage.appendChild(botMessageContent);

        // Afficher le fichier (si renvoyé) du bot
        if (data.file_url) {
            const fileContainer = document.createElement('div');
            fileContainer.className = 'file-container';

            if (data.file_url.endsWith('.png') || data.file_url.endsWith('.jpg') || data.file_url.endsWith('.jpeg')) {
                const img = document.createElement('img');
                img.src = data.file_url;
                img.alt = "Image envoyée par le bot";
                img.style.maxWidth = "200px";
                img.style.marginBottom = "10px";
                fileContainer.appendChild(img);
            } else {
                const fileLink = document.createElement('a');
                fileLink.href = data.file_url;
                fileLink.target = "_blank";
                fileLink.textContent = "Télécharger le fichier envoyé par le bot";
                fileContainer.appendChild(fileLink);
            }
            botMessage.appendChild(fileContainer);
        }

        // Ajoutez le message du bot au chatlog
        chatlog.appendChild(botMessage);

        // Synthèse vocale pour la réponse du bot
        const utterance = new SpeechSynthesisUtterance(data.response);
        utterance.voice = speechSynthesis.getVoices().find(voice => voice.name === 'Google UK English Female');
        speechSynthesis.speak(utterance);

        chatlog.scrollTop = chatlog.scrollHeight;
    })
    .catch(error => {
        console.error('Erreur lors de l\'envoi du message:', error);
        alert('Une erreur est survenue lors de l\'envoi du message.');
    });

    // Réinitialiser le champ texte et fichier
    document.getElementById('userInput').value = '';
    fileInput.value = '';
    document.getElementById("filePreviewContainer").innerHTML = "";
}


// test de formattage de texte

// test de formattage de texte

document.getElementById('userInput').addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});


function adjustTextareaHeight() {
    const textarea = document.getElementById('userInput');
    textarea.style.height = 'auto';
    textarea.style.height = (textarea.scrollHeight) + 'px';
}

document.getElementById('userInput').addEventListener('input', adjustTextareaHeight);

function showProfile() {
    alert('Profil: John Doe\nEmail: johndoe@example.com');
}

function logout() {
    alert('Déconnexion');
}


let timeoutId;

window.onload = function () {
    initSpeechRecognition();
};

function initSpeechRecognition() {
    recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = 'fr-FR';
    recognition.interimResults = true;
    recognition.continuous = true;

    recognition.onresult = function (event) {
        const transcript = Array.from(event.results)
            .map(result => result[0])
            .map(result => result.transcript)
            .join('');

        document.getElementById('userInput').value = transcript;
        adjustTextareaHeight();

        // Réinitialiser le délai à chaque nouveau résultat
        clearTimeout(timeoutId);

        if (event.results[0].isFinal) {
            // Ajouter un délai avant d'envoyer le message pour vérifier si l'utilisateur a terminé de parler
            timeoutId = setTimeout(() => {
                sendMessage();
            }, 2000); // Délai de 2 secondes
        }
    };

    recognition.onerror = function (event) {
        console.error('Speech recognition error:', event.error);
    };

    recognition.onend = function () {
        // Redémarrer la reconnaissance vocale si nécessaire
        if (isRecording) {
            recognition.start();
        }
    };
}

function startRecording() {
    if (isRecording) {
        recognition.stop();
        isRecording = false;
        document.getElementById('microphoneButton').classList.remove('recording');
    } else {
        recognition.start();
        isRecording = true;
        document.getElementById('microphoneButton').classList.add('recording');

        const utterance = new SpeechSynthesisUtterance("Parlez maintenant");
        utterance.voice = speechSynthesis.getVoices().find(voice => voice.name === 'Google UK English Female');
        speechSynthesis.speak(utterance);
    }
}


// Téléchargement de fichier
// Activer le bouton pour choisir un fichier
document.getElementById("fileUploadButton").addEventListener("click", function () {
    document.getElementById("fileInput").click();
});

// Affichage de l'aperçu des fichiers avec possibilité de suppression
document.getElementById("fileInput").addEventListener("change", function (event) {
    const file = event.target.files[0];
    const previewContainer = document.getElementById("filePreviewContainer");
    previewContainer.innerHTML = ""; // Réinitialise l'aperçu

    if (file) {
        const previewItem = document.createElement("div");
        previewItem.classList.add("preview-item");

        // Ajout de l'image ou du texte
        if (file.type.startsWith("image/")) {
            const img = document.createElement("img");
            img.src = URL.createObjectURL(file);
            img.alt = "Aperçu de l'image";
            previewItem.appendChild(img);
        } else {
            const fileInfo = document.createElement("div");
            fileInfo.textContent = file.name;
            previewItem.appendChild(fileInfo);
        }

        // Bouton pour supprimer l'aperçu
        const removeButton = document.createElement("button");
        removeButton.classList.add("remove-preview");
        removeButton.innerHTML = "&times;"; // Symbole de croix
        removeButton.addEventListener("click", function () {
            previewContainer.innerHTML = ""; // Supprime l'aperçu
            document.getElementById("fileInput").value = ""; // Réinitialise le champ fichier
        });

        previewItem.appendChild(removeButton);
        previewContainer.appendChild(previewItem);
    }
});

// Fin code de Téléchargement de fichier

// // Affichage d'emoji


// function openStickers() {
//     // Exemple de code pour afficher des stickers dans une boîte de dialogue
//     const stickers = [
//         '😊', '😂', '❤️', '🎉', '👍', '👏'
//     ];

//     // Créer une boîte de dialogue ou une autre interface pour afficher les stickers
//     const stickersContainer = document.createElement('div');
//     stickersContainer.className = 'stickers-container';

//     stickers.forEach(sticker => {
//         const stickerElement = document.createElement('span');
//         stickerElement.className = 'sticker';
//         stickerElement.textContent = sticker;
//         stickerElement.onclick = () => selectSticker(sticker);
//         stickersContainer.appendChild(stickerElement);
//     });

//     // Afficher les stickers à l'endroit approprié dans votre interface
//     // Par exemple, vous pouvez les ajouter à un élément spécifique dans votre interface
//     const chatInputContainer = document.querySelector('.input-group');
//     chatInputContainer.appendChild(stickersContainer);
// }

// function selectSticker(sticker) {
//     // Actions à effectuer lorsque l'utilisateur sélectionne un sticker
//     document.getElementById('userInput').value += sticker;
// }