### Install and use supervisor to instantiate the processes 

        sudo pip3 install supervisor
        echo_supervisord_conf
        echo_supervisord_conf > supervisord.conf
        supervisord
        superviosrctl stop <>
        supervisorctl update

### Sample supervisor program

        [program:reeds]
        directory=$PWD
        command=env/bin/python reeds_server/server.py
        autostart=true
        autorestart=true
        startretries=2
        stderr_logfile=./reeds.err.log
        stdout_logfile=./reeds.out.log

### NGINX deployment

        sudo npm run build
        sudo rm -rf /usr/share/nginx/dist
        sudo cp dist -R /usr/share/nginx/dist
        chmod -Rv o+rx /usr/share/nginx/dist
        sudo service nginx start

### NGINX configuration

server {
        listen       80;
        listen       [::]:80;
        server_name  _;
        server_tokens off;
        add_header "X-XSS-Protection" "1; mode=block" always;
        add_header "X-Frame-Options" "SAMEORIGIN" always;
        root         /usr/share/nginx/html;

        # Load configuration files for the default server block.
        include /etc/nginx/default.d/*.conf;

        error_page 404 /404.html;
        location /api/ {
                proxy_pass http://localhost:5001;
        }
        location /notifications/ {
                proxy_pass http://localhost:5002;
        }
        location / {
                root /usr/share/nginx/dist;
        }

        location = /404.html {
        }

        error_page 500 502 503 504 /50x.html;
        location = /50x.html {
        }
    }








