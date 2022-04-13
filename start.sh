gunicorn --worker-class eventlet -w 1 --log-file server.log app:app
#cd /home/ubuntu/flask-app/
#source myenv/bin/activate
#gunicorn --worker-class eventlet -w 1 app:app
