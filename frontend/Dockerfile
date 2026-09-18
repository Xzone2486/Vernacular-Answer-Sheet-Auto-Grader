# Stage 1: Build
FROM node:22-alpine as builder

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Stage 2: Serve
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
# Copy custom nginx config if needed, default is ok for now.
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
