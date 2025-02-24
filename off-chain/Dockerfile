# Build stage
FROM node:14 AS builder

# Set the working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application code
COPY . .

# Build the application
RUN npm run build

# Development stage with Python
FROM python:3.9-slim

# Install Node.js
RUN apt-get update && apt-get install -y \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_14.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy Python requirements and install
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the app
COPY . .
COPY --from=builder /app/build ./build

# Expose port 3000
EXPOSE 3000

# Start the Flask app
CMD ["python", "app.py"]

# Production stage
FROM nginx:alpine

# Copy the build output from builder stage
COPY --from=builder /app/build /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 3000
EXPOSE 3000

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
