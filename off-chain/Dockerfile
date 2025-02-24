# Build stage for React
FROM node:14 AS builder

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .

# Set PUBLIC_URL for the build
ARG PUBLIC_URL=/miner-id-minter
ENV PUBLIC_URL=${PUBLIC_URL}
ENV REACT_APP_PUBLIC_URL=${PUBLIC_URL}

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

# Set environment variables for runtime
ENV PUBLIC_URL=/miner-id-minter

EXPOSE 3000

CMD ["python", "app.py"]
