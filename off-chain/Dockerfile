# Build stage for React
FROM node:14 AS builder

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Production stage with Python/Flask
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the built React app and Flask server
COPY --from=builder /app/build ./build
COPY app.py .

EXPOSE 3000

CMD ["python", "app.py"]
