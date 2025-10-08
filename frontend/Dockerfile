# Use an official Node.js runtime as a parent image
FROM node:18-alpine

# Set the working directory in the container
WORKDIR /app

# Copy package.json and package-lock.json (or yarn.lock)
COPY package*.json ./

# Install project dependencies
RUN npm install

# Copy the rest of the application code
COPY . .

# Build the Next.js application for production
RUN npm run build

# Expose port 3000 to the network
EXPOSE 3000

# The default command to run when starting the container
# This will be overridden by docker-compose.yml in development
CMD ["npm", "run", "dev"]
