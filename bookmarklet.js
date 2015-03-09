javascript:(
    function(){
        var HOST='127.0.0.1', PORT='8070';
        var mount_point, style, request;
        mount_point = document.getElementById('BM_YDS_notification-box');
        if (mount_point == null) {
            style = document.createElement('style');
            style.type = 'text/css';
            style.innerHTML = '#BM_YDS_notification-box {display: none; word-wrap: break-word; font-size: 14px; color: white; -moz-opacity: 0.0; opacity:.0; filter: alpha(opacity=0);position: fixed; padding: 10px; bottom: 50px; border-radius: 8px; width: 200px; height: 50px; right: 20px; background-color: black;z-index:1001;}';
            mount_point = document.createElement('div');
            mount_point.id = 'BM_YDS_notification-box';
            mount_point.innerHTML = '';

            document.getElementsByTagName('head')[0].appendChild(style);
            document.getElementsByTagName('body')[0].appendChild(mount_point);
        }

        function dispatcher(raw_data) {
            var data;
            data = JSON.parse(raw_data);
            if (data['status'] === 'ok'){
                success(data['msg']);
            }
            else if (data['status'] === 'error') {
                error(data['msg']);
            }
        }

        function success(msg){
            show_notification(msg);
        }

        function error(msg){
            show_notification(msg);
        }

        function show_notification(msg) {
            mount_point.innerHTML = '[YDS]: '+ msg;
            mount_point.style.display = 'block';
            mount_point.style.opacity = 0.1;
            fadeIn(mount_point, 0.1, 8);
        }

        function fadeIn(div, step, iter) {
            iter = iter - 1;
            div.style.opacity = parseFloat(div.style.opacity) + step;
            if (iter == 0) {
                setTimeout(function(){fadeOut(div, step, 9);}, 5000);
            }
            else {
                setTimeout(function(){fadeIn(div, step, iter)}, 50)
            }
        }

        function fadeOut(div, step, iter) {
            iter = iter - 1;
            div.style.opacity = parseFloat(div.style.opacity) - step;
            if (iter == 0) {
                div.style.display = 'none';
            }
            else {
                setTimeout(function(){fadeOut(div, step, iter)}, 50)
            }
        }

        request = new XMLHttpRequest();
        request.open('GET', 'https://'+ HOST +':' + PORT + '/save?url=' + encodeURIComponent(window.location));
        request.onreadystatechange =  function () {
            if (request.readyState == 4) {
                if (request.status == 200) {
                    dispatcher(request.responseText);
                }
                else {
                    error('Error occurred during connection')
                }
            }
        };
        request.send(null);

        show_notification('Request sent');
} )();

