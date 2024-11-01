FROM node:lts-alpine

WORKDIR /app

# Add necessary build tools and configure npm
RUN apk add --no-cache python3 make g++

# Copy package files first to leverage Docker cache
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application
COPY . .

# Expose port 8080
EXPOSE 8080

# Start the development server
CMD ["npm", "run", "serve"]