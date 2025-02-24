# Use an official Node.js runtime as a parent image
FROM node:14

# Set the working directory to /app
WORKDIR /app

# Copy package.json and package-lock.json to the working directory
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application code to the working directory
COPY . .

# Set the PUBLIC_URL environment variable
ENV PUBLIC_URL="https://dev.ergominers.com/miner-id-minter"

# Add verbose logging
RUN echo "Contents of /app:"
RUN ls -la /app
RUN echo "Contents of /app/src:"
RUN ls -la /app/src || echo "src directory not found"
RUN echo "Local npm packages:"
# RUN npm list --depth=0

RUN npm run build

# Expose port 3000
EXPOSE 3000

# Start the application using npm start
CMD ["npm", "start"]
