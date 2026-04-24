FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine
WORKDIR /app
RUN npm install -g vite
COPY package*.json ./
RUN npm ci --omit=dev
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/vite.config.js ./vite.config.js

EXPOSE 5173

CMD ["vite", "preview", "--host", "0.0.0.0", "--port", "5173"]
