FROM node:22-alpine AS build
WORKDIR /web
RUN corepack enable
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY . .
ARG BACKEND_URL=http://api:8000
ENV BACKEND_URL=$BACKEND_URL
RUN pnpm build

FROM node:22-alpine
WORKDIR /web
RUN corepack enable
ENV NODE_ENV=production BACKEND_URL=http://api:8000
COPY --from=build /web ./
EXPOSE 3000
CMD ["pnpm", "start"]
