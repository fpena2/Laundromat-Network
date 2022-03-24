# Start the gunicorn server
`gunicorn --worker-class eventlet -w 1 app:app`

# Leave gunicorn process running in background
`source ./run_script & disown`

# Killing all gunicorn disowned processes
`pkill -f gunicorn`

# Installing python-librtmp on Ubuntu
```
sudo apt-get install librtmp-dev
sudo pip install python-librtmp
```

# Installing MongoDB on Ubuntu
```
\\ Read MongoDB docs to add the right package repository to apt-get

sudo apt-get install mongodb-org
```

# Starting nginx and mongodb services
```
sudo service nginx start		\\ nginx
sudo service mongod start		\\ mongodo
sudo service redis start		\\ redis
```

