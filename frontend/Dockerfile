# DEKOPEN frontend — static SPA + /api reverse proxy to the backend service.
# Build-time VITE_* vars are baked by vite; runtime routing is nginx envsubst.
FROM node:24.15.0-bookworm-slim AS build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
COPY docs/operations/ACTIVACION.md /app/docs/operations/ACTIVACION.md
ARG VITE_SUPABASE_URL
ARG VITE_SUPABASE_ANON_KEY
ARG VITE_POSTHOG_KEY
ARG VITE_POSTHOG_HOST
RUN npm run build

FROM nginx:1.29.2-alpine
COPY frontend/nginx.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/frontend/dist /usr/share/nginx/html
