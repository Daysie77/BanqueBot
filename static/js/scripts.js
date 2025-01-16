let currentConversationId = null;
let recognition;
let isRecording = false;

// document.addEventListener("DOMContentLoaded", function () {
//     loadConversations();

//     const conversationId = getCurrentConversationIdFromURL();
//     if (conversationId) {
//         loadMessages(conversationId);
//     }

// });

document.addEventListener('DOMContentLoaded', function () {
    loadConversations();

    // Charger la conversation active si elle existe dans localStorage
    const activeConversationId = localStorage.getItem('activeConversationId');
    if (activeConversationId) {
        loadMessages(activeConversationId); // Charger les messages de la conversation active
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

                // Récupérer l'ID de la conversation active depuis localStorage
                const activeConversationId = localStorage.getItem('activeConversationId');

                // Vérifier si cet élément correspond à la conversation active
                if (activeConversationId == conversation.id) {
                    listItem.classList.add('selected'); // Surligner l'élément actif
                    loadMessages(conversation.id); // Charger automatiquement les messages
                }

                listItem.addEventListener('click', function () {
                    // Supprimer la classe "selected" de tous les éléments
                    const allItems = document.querySelectorAll('.list-group-item');
                    allItems.forEach(item => item.classList.remove('selected'));

                    // Ajouter la classe "selected" à l'élément cliqué
                    listItem.classList.add('selected');

                    // Sauvegarder l'ID de la conversation sélectionnée dans localStorage
                    localStorage.setItem('activeConversationId', conversation.id);

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
            chatlog.innerHTML = ''; // Efface les messages existants

            data.forEach(message => {
                const messageElement = document.createElement('div');
                messageElement.className = `message ${message.sender}`;

                // Affiche le texte du message
                if (message.content) {
                    const messageContent = document.createElement('div');
                    messageContent.className = 'message-content';
                    messageContent.textContent = message.content;
                    messageElement.appendChild(messageContent);
                }

                // Affiche le fichier si présent
                if (message.file_url) {
                    const fileContainer = document.createElement('div');
                    fileContainer.className = 'file-container';

                    // Vérifie si le fichier est une image
                    if (/\.(png|jpg|jpeg|gif)$/i.test(message.file_url)) {
                        const img = document.createElement('img');
                        img.src = message.file_url;
                        img.alt = 'Image envoyée';
                        img.className = 'file-image'; // Ajout de classe CSS
                        fileContainer.appendChild(img);
                    } 
                    // Sinon, afficher un lien de téléchargement pour d'autres types de fichiers
                    else {
                        const filePreview = document.createElement('div');
                        filePreview.className = 'file-preview';

                        // Ajoute une icône dynamique pour les fichiers non-images
                        const fileIcon = document.createElement('i');
                        const fileExtension = message.file_url.split('.').pop().toLowerCase();

                        // Détermine la classe d'icône en fonction de l'extension
                        switch (fileExtension) {
                            case 'pdf':
                                fileIcon.className = 'fas fa-file-pdf file-icon'; // Icône PDF
                                fileIcon.style.color = '#dc3545'; // Couleur rouge
                                break;
                            case 'doc':
                            case 'docx':
                                fileIcon.className = 'fas fa-file-word file-icon'; // Icône Word
                                fileIcon.style.color = '#007bff'; // Couleur bleue
                                break;
                            case 'xls':
                            case 'xlsx':
                                fileIcon.className = 'fas fa-file-excel file-icon'; // Icône Excel
                                fileIcon.style.color = '#28a745'; // Couleur verte
                                break;
                            // case 'csv':
                            //     fileIcon.className = 'fas fa-file-csv file-icon'; // Icône CSV
                            //     fileIcon.style.color = '#28a745'; // Couleur verte
                            //     break;
                            case 'txt':
                                fileIcon.className = 'fas fa-file-alt file-icon'; // Icône fichier texte
                                fileIcon.style.color = '#6c757d'; // Couleur grise
                                break;
                            case 'zip':
                            case 'rar':
                                fileIcon.className = 'fas fa-file-archive file-icon'; // Icône archive
                                fileIcon.style.color = '#ffc107'; // Couleur jaune
                                break;
                            case 'mp3':
                            case 'wav':
                                fileIcon.className = 'fas fa-file-audio file-icon'; // Icône audio
                                fileIcon.style.color = '#17a2b8'; // Couleur cyan
                                break;
                            case 'mp4':
                            case 'avi':
                            case 'mkv':
                                fileIcon.className = 'fas fa-file-video file-icon'; // Icône vidéo
                                fileIcon.style.color = '#6610f2'; // Couleur violette
                                break;
                            default:
                                fileIcon.className = 'fas fa-file file-icon'; // Icône par défaut
                                fileIcon.style.color = '#6c757d'; // Couleur grise
                        }

                        filePreview.appendChild(fileIcon);

                        // Ajoute les détails du fichier (nom et lien)
                        const fileDetails = document.createElement('div');
                        fileDetails.className = 'file-details';

                        const fileName = document.createElement('a');
                        fileName.href = message.file_url;
                        fileName.textContent = message.file_url.split('/').pop();
                        fileName.target = '_blank';
                        fileName.className = 'file-name'; // Ajout de classe CSS

                        const fileType = document.createElement('span');
                        fileType.className = 'file-type';
                        fileType.textContent = `Fichier ${fileExtension}`; // Affiche le type du fichier

                        fileDetails.appendChild(fileName);
                        fileDetails.appendChild(fileType);
                        filePreview.appendChild(fileDetails);
                        fileContainer.appendChild(filePreview);
                    }

                    messageElement.appendChild(fileContainer);
                }

                chatlog.appendChild(messageElement);
            });

            // Scroll vers le bas du chatlog
            chatlog.scrollTop = chatlog.scrollHeight;
        })
        .catch(error => {
            console.error('Erreur lors du chargement des messages :', error);
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
// function sendMessage() {
//     const userInput = document.getElementById('userInput').value;
//     const fileInput = document.getElementById("fileInput");
//     const chatlog = document.getElementById('chatlog');

//     // Vérifiez si le champ de texte est vide et si aucun fichier n'est sélectionné
//     if (userInput.trim() === '' && !fileInput.files[0]) return;

//     // Créez un conteneur pour le message utilisateur
//     const userMessage = document.createElement('div');
//     userMessage.className = 'message user';

//     // Affichez le fichier (image ou autre) si présent
//     if (fileInput.files[0]) {
//         const file = fileInput.files[0];
//         const fileContainer = document.createElement('div');
//         fileContainer.className = 'file-container'; // Classe CSS pour le style

//         if (file.type.startsWith("image/")) {
//             const imgPreview = document.createElement("img");
//             imgPreview.src = URL.createObjectURL(file);
//             imgPreview.alt = "Image envoyée";
//             imgPreview.style.maxWidth = "200px";
//             imgPreview.style.maxHeight = "200px";
//             imgPreview.style.marginBottom = "10px"; // Espacement avec le texte
//             fileContainer.appendChild(imgPreview);
//         } else {
//             const filePreview = document.createElement("div");
//             filePreview.textContent = file.name;
//             filePreview.style.marginBottom = "10px"; // Espacement avec le texte
//             filePreview.style.color = "gray";
//             fileContainer.appendChild(filePreview);
//         }

//         userMessage.appendChild(fileContainer);
//     }

//     // Affichez le texte en dessous du fichier
//     if (userInput.trim() !== '') {
//         const userMessageContent = document.createElement('div');
//         userMessageContent.className = 'message-content';
//         userMessageContent.textContent = userInput;
//         userMessage.appendChild(userMessageContent);
//     }

//     // Ajoutez le message utilisateur au chatlog
//     chatlog.appendChild(userMessage);
//     chatlog.scrollTop = chatlog.scrollHeight;

//     // Préparez les données pour l'envoi
//     const formData = new FormData();
//     formData.append('user_input', userInput);

//     // Assurez-vous que la variable `currentConversationId` est définie avec l'ID de la conversation active
//     const conversationId = currentConversationId;  // Si cette variable n'existe pas encore, créez-la avec l'ID de la conversation actuelle
//     formData.append('conversation_id', conversationId);  // Ajouter le `conversation_id` à la requête

//     if (fileInput.files[0]) {
//         formData.append('file', fileInput.files[0], fileInput.files[0].name);
//     }

//     // Envoyer la requête au serveur
//     fetch('/chat', {
//         method: 'POST',
//         body: formData
//     })
//     .then(response => response.json())
//     .then(data => {
//         // Créez un conteneur pour le message du bot
//         const botMessage = document.createElement('div');
//         botMessage.className = 'message bot';

//         // Afficher le texte du bot
//         const botMessageContent = document.createElement('div');
//         botMessageContent.className = 'message-content';
//         botMessageContent.textContent = data.response;
//         botMessage.appendChild(botMessageContent);

        
//         // Ajoutez le message du bot au chatlog
//         chatlog.appendChild(botMessage);

//         // Synthèse vocale pour la réponse du bot
//         const utterance = new SpeechSynthesisUtterance(data.response);
//         utterance.voice = speechSynthesis.getVoices().find(voice => voice.name === 'Google UK English Female');
//         speechSynthesis.speak(utterance);

//         chatlog.scrollTop = chatlog.scrollHeight;
//     })
//     .catch(error => {
//         console.error('Erreur lors de l\'envoi du message:', error);
//         alert('Une erreur est survenue lors de l\'envoi du message.');
//     });

//     // Réinitialiser le champ texte et fichier
//     document.getElementById('userInput').value = '';
//     fileInput.value = '';
//     document.getElementById("filePreviewContainer").innerHTML = "";
// }


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
            filePreview.className = "file-preview";

            // Ajoute une icône dynamique pour les fichiers non-images
            const fileIcon = document.createElement('i');
            const fileExtension = file.name.split('.').pop().toLowerCase();

            // Détermine la classe d'icône en fonction de l'extension
            switch (fileExtension) {
                case 'pdf':
                    fileIcon.className = 'fas fa-file-pdf file-icon'; // Icône PDF
                    fileIcon.style.color = '#dc3545'; // Couleur rouge
                    break;
                case 'doc':
                case 'docx':
                    fileIcon.className = 'fas fa-file-word file-icon'; // Icône Word
                    fileIcon.style.color = '#007bff'; // Couleur bleue
                    break;
                case 'xls':
                case 'xlsx':
                    fileIcon.className = 'fas fa-file-excel file-icon'; // Icône Excel
                    fileIcon.style.color = '#28a745'; // Couleur verte
                    break;
                // case 'csv':
                //     fileIcon.className = 'fas fa-file-csv file-icon'; // Icône CSV
                //     fileIcon.style.color = '#28a745'; // Couleur verte
                //     break;
                case 'txt':
                    fileIcon.className = 'fas fa-file-alt file-icon'; // Icône fichier texte
                    fileIcon.style.color = '#6c757d'; // Couleur grise
                    break;
                case 'zip':
                case 'rar':
                    fileIcon.className = 'fas fa-file-archive file-icon'; // Icône archive
                    fileIcon.style.color = '#ffc107'; // Couleur jaune
                    break;
                case 'mp3':
                case 'wav':
                    fileIcon.className = 'fas fa-file-audio file-icon'; // Icône audio
                    fileIcon.style.color = '#17a2b8'; // Couleur cyan
                    break;
                case 'mp4':
                case 'avi':
                case 'mkv':
                    fileIcon.className = 'fas fa-file-video file-icon'; // Icône vidéo
                    fileIcon.style.color = '#6610f2'; // Couleur violette
                    break;
                default:
                    fileIcon.className = 'fas fa-file file-icon'; // Icône par défaut
                    fileIcon.style.color = '#6c757d'; // Couleur grise
            }

            filePreview.appendChild(fileIcon);

            // Ajoute les détails du fichier (nom et type)
            const fileDetails = document.createElement("div");
            fileDetails.className = "file-details";

            const fileName = document.createElement("span");
            fileName.textContent = file.name;
            fileName.className = "file-name"; // Classe CSS pour le style

            const fileType = document.createElement("span");
            fileType.textContent = `Fichier ${fileExtension}`;
            fileType.className = "file-type"; // Classe CSS pour le style

            fileDetails.appendChild(fileName);
            fileDetails.appendChild(fileType);
            filePreview.appendChild(fileDetails);
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
    const conversationId = currentConversationId; // Si cette variable n'existe pas encore, créez-la avec l'ID de la conversation actuelle
    formData.append('conversation_id', conversationId); // Ajouter le `conversation_id` à la requête

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