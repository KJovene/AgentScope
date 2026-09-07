# syntax=docker/dockerfile:1

# ---------- base : dépendances installées ----------
FROM node:20-slim AS base
ENV CI=1
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install

# ---------- dev : serveur Vite, code monté par docker-compose ----------
FROM base AS dev
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]

# ---------- build : bundle statique ----------
FROM base AS build
COPY . .
RUN npm run build

# ---------- prod : Nginx sert le bundle et proxifie /api ----------
FROM nginx:1.27-alpine AS prod
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
