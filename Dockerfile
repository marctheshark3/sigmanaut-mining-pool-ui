# Use an official Python runtime as a parent image
FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Create necessary directories with proper permissions
RUN mkdir -p /app/flask_session && \
    chmod 777 /app/flask_session

# Copy requirements first to leverage Docker cache
COPY requirements.txt /app/
RUN pip3 install -r requirements.txt

# Copy the application code
COPY . /app/

# Create symbolic link for conf directory
RUN mkdir -p /app/utils && ln -s /app/conf /app/utils/conf

# Make the entrypoint script executable
COPY entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh

# Create a non-root user and switch to it
RUN useradd -m appuser && \
    chown -R appuser:appuser /app
USER appuser

# Make port 8050 available
EXPOSE 8050

# Define environment variable
ENV FLASK_APP=app.py
ENV PYTHONPATH=/app

# Command to run the application
CMD ["entrypoint.sh"]
