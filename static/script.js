window.addEventListener('DOMContentLoaded', function(){
    var uploadForm = document.getElementById('uploadForm');
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

    var es = new EventSource('/pending?id=' + window.UPLOAD_ID);
    es.onmessage = function(evt){
        console.log('evt', evt);
    }
});
