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
                messageElement.innerHTML = `<img src="/static/${message.sender}.jpg" class="avatar">
                                             <div class="message-content">${message.content}</div>`;
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


function sendMessage() {
    const userInput = document.getElementById('userInput').value;
    if (userInput.trim() === '') return;

    const chatlog = document.getElementById('chatlog');
    const userMessage = document.createElement('div');
    userMessage.className = 'message user';
    userMessage.innerHTML = `<img src="/static/user.jpg" class="avatar"><div class="message-content">${userInput}</div>`;
    chatlog.appendChild(userMessage);

    const formData = new FormData();
    formData.append('user_input', userInput);
    formData.append('conversation_id', currentConversationId);
    if (selectedFile) {
        formData.append('file', selectedFile, selectedFile.name);
    }

    fetch('/chat', {
        method: 'POST',
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            const botMessage = document.createElement('div');
            botMessage.className = 'message bot';

            if (data.response.startsWith("https://www.youtube.com/embed/")) {
                const iframe = document.createElement('iframe');
                iframe.src = data.response + "?autoplay=1";
                iframe.width = "560";
                iframe.height = "315";
                iframe.frameBorder = "0";
                iframe.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture";
                iframe.allowFullscreen = true;
                botMessage.appendChild(iframe);
            } else {
                botMessage.innerHTML = `<img src="/static/icons/bot_avatar.jpg" class="avatar"><div class="message-content">${data.response}</div>`;

                const utterance = new SpeechSynthesisUtterance(data.response);
                utterance.voice = speechSynthesis.getVoices().find(voice => voice.name === 'Google UK English Female');
                speechSynthesis.speak(utterance);
            }

            chatlog.appendChild(botMessage);
            chatlog.scrollTop = chatlog.scrollHeight;
        });

    document.getElementById('userInput').value = '';
}

document.getElementById('userInput').addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});


let selectedFile = null;

function fileSelected(event) {
    selectedFile = event.target.files[0];

    const fileName = selectedFile.name;
    const fileMessage = document.createElement('div');
    fileMessage.className = 'message user file';
    fileMessage.innerHTML = `<img src="/static/user.jpg" class="avatar"><div class="message-content">${fileName} <progress id="fileProgress" value="0" max="100"></progress></div>`;
    document.getElementById('chatlog').appendChild(fileMessage);
}

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