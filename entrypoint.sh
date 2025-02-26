#!/bin/bash

# echo "Starting cron..."
# cron
# echo "Cron started."


# Run the database initialization script
# python3 -m utils.init_db

# Start the web server with gunicorn
gunicorn -w 4 --timeout 2000 -b 0.0.0.0:8050 app:application
