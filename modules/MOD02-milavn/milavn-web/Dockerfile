# syntax=docker/dockerfile:1.7
# Milavn web — production image (linux/amd64, linux/arm64).
# A Next.js zone served under NEXT_PUBLIC_BASE_PATH (`/milavn`) on the one
# ForKhatri origin (docs/ParentApp/07-tech-reqs.md TR22). NEXT_PUBLIC_* values
# are inlined into the client bundle, so they are build arguments.
# MILAVN_API_INTERNAL_URL is the API on the private network, used by the
# server-rendered public activity page and the /media rewrite.
# Deployment kit: deploy/README.md (repo root).
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

FROM node:22-alpine AS build
WORKDIR /app
ARG NEXT_PUBLIC_BASE_PATH=/milavn
ARG NEXT_PUBLIC_API_BASE
ARG NEXT_PUBLIC_IDENTITY_API
ARG NEXT_PUBLIC_FORKHATRI_ENTRANCE_URL
ARG MILAVN_API_INTERNAL_URL=
ENV NEXT_TELEMETRY_DISABLED=1 \
    NEXT_OUTPUT_STANDALONE=1 \
    NODE_OPTIONS=--max-old-space-size=2048 \
    NEXT_PUBLIC_BASE_PATH=${NEXT_PUBLIC_BASE_PATH} \
    NEXT_PUBLIC_API_BASE=${NEXT_PUBLIC_API_BASE} \
    NEXT_PUBLIC_IDENTITY_API=${NEXT_PUBLIC_IDENTITY_API} \
    NEXT_PUBLIC_FORKHATRI_ENTRANCE_URL=${NEXT_PUBLIC_FORKHATRI_ENTRANCE_URL} \
    MILAVN_API_INTERNAL_URL=${MILAVN_API_INTERNAL_URL}
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN for v in NEXT_PUBLIC_API_BASE NEXT_PUBLIC_IDENTITY_API NEXT_PUBLIC_FORKHATRI_ENTRANCE_URL; do \
      eval "test -n \"\$$v\"" || { echo "$v build argument is required" >&2; exit 1; }; \
    done \
 && mkdir -p public \
 && npm run build

FROM node:22-alpine AS run
WORKDIR /app
ARG NEXT_PUBLIC_BASE_PATH=/milavn
ARG MILAVN_API_INTERNAL_URL=
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    HOSTNAME=0.0.0.0 \
    PORT=3001 \
    HEALTH_PATH=${NEXT_PUBLIC_BASE_PATH} \
    MILAVN_API_INTERNAL_URL=${MILAVN_API_INTERNAL_URL}
COPY --from=build --chown=node:node /app/public ./public
COPY --from=build --chown=node:node /app/.next/standalone ./
COPY --from=build --chown=node:node /app/.next/static ./.next/static
USER node
EXPOSE 3001
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD node -e "fetch('http://127.0.0.1:'+(process.env.PORT||3001)+(process.env.HEALTH_PATH||'/')).then(r=>process.exit(r.status<500?0:1)).catch(()=>process.exit(1))"
CMD ["node", "server.js"]
