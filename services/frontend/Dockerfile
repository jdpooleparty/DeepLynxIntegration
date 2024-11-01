# Build stage
FROM node:18 as builder

WORKDIR /app

# Create .npmrc for better network resilience
RUN echo "fetch-retry-mintimeout=20000" >> .npmrc && \
    echo "fetch-retry-maxtimeout=120000" >> .npmrc && \
    echo "fetch-retries=5" >> .npmrc && \
    echo "network-timeout=100000" >> .npmrc

# Copy package files
COPY package*.json ./

# Install dependencies with specific flags for stability
RUN npm install --no-audit --prefer-offline --network-timeout=100000

# Copy source files
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration if needed
# COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080

# Configure nginx to handle SPA routing
RUN echo 'server { \
    listen 8080; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html; \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

CMD ["nginx", "-g", "daemon off;"]