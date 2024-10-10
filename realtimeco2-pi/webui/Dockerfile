FROM node:20.18.0-alpine
RUN apk update && apk add --no-cache libc6-compat
RUN corepack enable pnpm

COPY . /app

WORKDIR /app
RUN pnpm install
RUN npx prisma generate
RUN pnpm run build

CMD ["node", ".output/server/index.mjs"]