# frontend/Dockerfile

# ------------------------------------
# STAGE 1: BUILD (Handles Installation and Code Compilation)
# Purpose: To perform the slow npm install and npm run build steps.
# ------------------------------------
FROM node:20-alpine AS builder
WORKDIR /app

# 1. CACHING LAYER: Copy package files first. 
# This layer only rebuilds if package.json changes (very rarely).
COPY package.json yarn.lock* package-lock.json* ./

# 2. Install dependencies (SLOWEST STEP - will use cache)
RUN npm install

# 3. Copy source code (FAST STEP - changes often)
COPY . .

# 4. Build Next.js application (Slow but necessary)
RUN npm run build


# ------------------------------------
# STAGE 2: RUNNER (Handles Execution)
# Purpose: To create a small, fast, production-ready image.
# ------------------------------------
FROM node:18-alpine AS runner
WORKDIR /app
# Set environment to production (important for Next.js)
ENV NODE_ENV=production

# 5. Copy ONLY the necessary built artifacts from the 'builder' stage
# This makes the final image much smaller.
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

EXPOSE 3000

# Override the default start command for local development:
# CMD is usually 'npm start', but docker-compose will override this to 'npm run dev'
CMD ["npm", "start"]