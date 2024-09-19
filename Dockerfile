# Use an official Python runtime as a parent image
FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container
COPY . /app

# Install cron and Python dependencies
RUN pip3 install -r /app/requirements.txt

# Setup cron jobs
# COPY utils/crontab_updates /etc/cron.d/crontab_updates
# RUN chmod 0644 /etc/cron.d/crontab_updates && \
#     crontab /etc/cron.d/crontab_updates && \
#     touch /var/log/cron.log

# Make the entrypoint script executable and set it as the entrypoint
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Make port 8050 available to the world outside this container
EXPOSE 8050

# Define environment variable
ENV FLASK_APP app.py

# Command to run the application and cron jobs
CMD ["entrypoint.sh"]
