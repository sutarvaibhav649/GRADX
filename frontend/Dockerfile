# Stage 1: Build Angular app
FROM node:20-alpine AS build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --force || npm install

# Copy source code
COPY . .

# Build the app (outputs to dist/GRADX as shown in your build)
RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:alpine

# Copy built app from the correct location (GRADX folder from your build output)
COPY --from=build /app/dist/GRADX /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]