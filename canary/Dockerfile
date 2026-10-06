FROM node:22-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:22-alpine
WORKDIR /app
ENV NODE_ENV=production HOST=0.0.0.0 PORT=8000
COPY --from=builder /app/dist ./dist
COPY package.json ./
COPY api ./api
COPY src/server ./src/server
USER node
EXPOSE 8000
CMD ["node", "src/server/serve.js"]
