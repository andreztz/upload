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
});
