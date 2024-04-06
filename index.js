// Create new websocket connection
const socket = new WebSocket("ws://127.0.0.1:3001");

const messages = document.getElementById('messages')
const form = document.getElementById('form');
const input = document.getElementById('input');

form.addEventListener('submit', (event) => {
    event.preventDefault();
    let msgdisplay = document.createElement('li')
    msgdisplay.appendChild(document.createTextNode('client: ' + input.value))
    messages.appendChild(msgdisplay);
    if (input.value) {
        socket.send(input.value);
        input.value = '';
    }
});

socket.addEventListener("message", (event) => {
    let msgdisplay = document.createElement('li')
    msgdisplay.appendChild(document.createTextNode('server: ' + event.data))
    messages.appendChild(msgdisplay);
    console.log('server: ' + event.data);
});


