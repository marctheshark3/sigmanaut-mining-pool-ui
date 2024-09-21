# Use an official Node.js runtime as a parent image
FROM node:14

# Set the working directory to /app
WORKDIR /app

# Copy package.json and package-lock.json to the working directory
COPY package*.json ./

# Install dependencies
RUN npm install
RUN npm install react-scripts@5.0.1 -g
RUN npm i @fleet-sdk/core

# Copy the rest of the application code to the working directory
COPY . .

# Build the React app
RUN npm run build

# Expose port 3000
EXPOSE 3000

# Install serve to run the built app
RUN npm install -g serve

# Start the application using serve, listening on all interfaces
CMD ["serve", "-s", "build", "-l", "tcp://0.0.0.0:3000"]
