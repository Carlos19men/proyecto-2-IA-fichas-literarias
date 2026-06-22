# Etapa de construcción
FROM node:20-alpine AS builder

WORKDIR /app

# Copiar archivos de configuración del workspace
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/admin/package.json ./apps/admin/

# Instalar pnpm y dependencias
RUN npm install -g pnpm
RUN pnpm install --frozen-lockfile

# Copiar el código fuente del admin
COPY apps/admin ./apps/admin
COPY src ./src

# Construir la aplicación
WORKDIR /app/apps/admin
RUN pnpm build

# Etapa de producción
FROM node:20-alpine AS runner

WORKDIR /app

# Crear usuario no-root por seguridad
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copiar desde el builder
COPY --from=builder /app/apps/admin/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/apps/admin/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/apps/admin/.next/static ./.next/static

# Cambiar al usuario no-root
USER nextjs

# Exponer puerto
EXPOSE 3000

# Variable de entorno para el puerto
ENV PORT 3000

# Comando de inicio
CMD ["node", "server.js"]