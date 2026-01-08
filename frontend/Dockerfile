# Production Dockerfile for Transfer2Read Frontend
# Multi-stage build for Next.js 15 with optimized production image
# Node.js 24.12.0 LTS on Alpine Linux for minimal image size

# ============================================
# Stage 1: Dependencies
# ============================================
FROM node:24.12.0-alpine AS deps

# Install libc6-compat for Alpine compatibility with some npm packages
RUN apk add --no-cache libc6-compat

WORKDIR /app

# Copy package files for dependency installation
COPY package.json package-lock.json* ./

# Install dependencies with clean cache
# Note: Using npm install instead of npm ci to handle dependency resolution
RUN npm install && \
    npm cache clean --force

# ============================================
# Stage 2: Builder
# ============================================
FROM node:24.12.0-alpine AS builder

WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules

# Copy all source files
COPY . .

# Set environment variable for Next.js to enable standalone output
ENV NEXT_TELEMETRY_DISABLED=1

# Build Next.js application
# Next.js will create optimized production build in .next folder
RUN npm run build

# ============================================
# Stage 3: Production Runtime
# ============================================
FROM node:24.12.0-alpine AS runner

WORKDIR /app

# Set production environment
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Create non-root user for security
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy Next.js standalone output (includes minimal dependencies)
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Switch to non-root user
USER nextjs

# Expose port 3000
EXPOSE 3000

# Set port environment variable
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Start Next.js production server
CMD ["node", "server.js"]
