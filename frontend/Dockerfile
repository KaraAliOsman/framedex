# DEKOPEN frontend — static SPA + /api reverse proxy to the backend service.
# Build-time VITE_* vars are baked by vite; runtime routing is nginx envsubst.
FROM node:24.15.0-bookworm-slim AS build
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM nginx:1.29.2-alpine
COPY frontend/nginx.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html
