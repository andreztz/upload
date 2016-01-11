function getWebSocketURL(){
    var loc = window.location, new_uri;
    if (loc.protocol === "https:") {
        new_uri = "wss:";
    } else {
        new_uri = "ws:";
    }
    new_uri += "//" + loc.host;
    new_uri += loc.pathname + "pending?id=" + window.UPLOAD_ID;
    return new_uri;
}

function humanReadableFilesize(bytes){
    var prefixes = ['Ki', 'Mi', 'Gi', 'Ti'];
    var prefix = '';
    while (bytes >= 1024 && prefixes.length){
        bytes = Math.floor(bytes/1024);
        prefix = prefixes.shift();
    }
    return [bytes, ' ', prefix, 'B'].join('');
}

function makeFileDisplayElement(file){
    var elem = document.createElement('li');

    var nameSpan = document.createElement('span');
    nameSpan.classList.add('filename');
    nameSpan.textContent = file.name;
    elem.appendChild(nameSpan);

    var sizeSpan = document.createElement('span');
    sizeSpan.classList.add('filesize');
    sizeSpan.textContent = humanReadableFilesize(file.size);
    elem.appendChild(sizeSpan);
    return elem;
}

window.addEventListener('DOMContentLoaded', function(){
    var uploadForm = document.getElementById('uploadForm');
    var display = document.getElementById('filesToUpload')
    window.uploadForm = uploadForm;


    var filesInput = uploadForm.upload;

    filesInput.addEventListener('change', function(evt){
        while (display.firstChild){
            display.removeChild(display.firstChild);
        }
        var file, displayElement;
        for (var i = 0; i < filesInput.files.length; i++){
            file = filesInput.files[i];
            displayElement = makeFileDisplayElement(file);
            display.appendChild(displayElement);
        }
    });

    uploadForm.addEventListener('submit', function(evt){
        evt.preventDefault();
        var req = new XMLHttpRequest();
        req.addEventListener("progress", function(){
            console.log('progress', arguments);
        }, false);
        req.open('post', uploadForm.action, true);
        req.send(new FormData(uploadForm));
        return false;
    });


    var ws = new WebSocket(getWebSocketURL());

    ws.onmessage = function(evt){
        console.log('evt', evt);
    }
});
