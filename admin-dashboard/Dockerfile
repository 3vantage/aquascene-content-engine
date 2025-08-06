# Admin Dashboard Dockerfile - React Application
FROM node:18-alpine as base

# Set working directory
WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install --omit=dev

# Development stage
FROM base as development
RUN npm install
COPY . .
EXPOSE 3000
CMD ["npm", "start"]

# Build stage
FROM base as builder
RUN npm install
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine as production

# Install curl for health checks
RUN apk add --no-cache curl

COPY --from=builder /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

# Add health check endpoint
RUN echo "OK" > /usr/share/nginx/html/health

EXPOSE 80
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost/health || exit 1

CMD ["nginx", "-g", "daemon off;"]