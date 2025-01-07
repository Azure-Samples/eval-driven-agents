# --------------------------------------------
# STEP 1: Build the Next.js application
# --------------------------------------------
    FROM node:18-alpine AS builder

    WORKDIR /app
    COPY package.json pnpm-lock.yaml ./
    RUN npm install -g pnpm
    RUN pnpm install
    
    COPY . .
    RUN pnpm run build
    
    # --------------------------------------------
    # STEP 2: Run the built application
    # --------------------------------------------
    FROM node:18-alpine AS runner
    
    ENV NODE_ENV=production
    WORKDIR /app
    
    COPY --from=builder /app/.next ./.next
    COPY --from=builder /app/package.json /app/pnpm-lock.yaml ./
    COPY --from=builder /app/public ./public
    COPY --from=builder /app/next.config.js ./
    COPY --from=builder /app/tailwind.config.js ./
    COPY --from=builder /app/postcss.config.js ./
    COPY --from=builder /app/tsconfig.json ./
    
    RUN npm install -g pnpm
    RUN pnpm install --prod
    
    EXPOSE 3000
    CMD ["pnpm", "start"]
    