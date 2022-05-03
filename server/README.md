# Start the gunicorn server
A shell script has been provided to start the server: `start.sh`

Execute the command
`./start.sh` to begin the server.
The script must be given executable rights if that has not already been done

# Leave gunicorn process running in background
To leave the server running in the background on the same terminal
`source ./start.sh & disown`

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

