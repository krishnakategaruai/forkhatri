# syntax=docker/dockerfile:1.7
# ForKhatri web entrance — production image (linux/amd64, linux/arm64).
# The default Next.js zone at `/` (docs/ParentApp/07-tech-reqs.md TR22).
# NEXT_PUBLIC_* values are inlined into the client bundle, so they are build
# arguments, not runtime settings. Deployment kit: deploy/README.md.
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

FROM node:22-alpine AS build
WORKDIR /app
ARG NEXT_PUBLIC_IDENTITY_API
ENV NEXT_TELEMETRY_DISABLED=1 \
    NEXT_OUTPUT_STANDALONE=1 \
    NODE_OPTIONS=--max-old-space-size=2048 \
    NEXT_PUBLIC_IDENTITY_API=${NEXT_PUBLIC_IDENTITY_API}
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN test -n "$NEXT_PUBLIC_IDENTITY_API" || (echo "NEXT_PUBLIC_IDENTITY_API build argument is required" >&2; exit 1) \
 && mkdir -p public \
 && npm run build

FROM node:22-alpine AS run
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    HOSTNAME=0.0.0.0 \
    PORT=3100
COPY --from=build --chown=node:node /app/public ./public
COPY --from=build --chown=node:node /app/.next/standalone ./
COPY --from=build --chown=node:node /app/.next/static ./.next/static
USER node
EXPOSE 3100
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD node -e "fetch('http://127.0.0.1:'+(process.env.PORT||3100)+'/').then(r=>process.exit(r.status<500?0:1)).catch(()=>process.exit(1))"
CMD ["node", "server.js"]
