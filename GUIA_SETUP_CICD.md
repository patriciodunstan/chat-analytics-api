# Guía Paso a Paso: Setup CI/CD

Sigue estos pasos en orden para configurar GitHub Actions + Railway.

---

## Paso 1: Obtener Railway Token

### Opción A: Desde Railway Dashboard (Recomendado)

1. **Ir a Railway**:
   - Abre: https://railway.app/account/tokens

2. **Crear Token**:
   - Click en **"Create Token"**
   - Nombre: `github-actions` (o el que prefieras)
   - Click en **"Create"**

3. **Copiar Token**:
   - ⚠️ **IMPORTANTE**: Copia el token AHORA (solo se muestra una vez)
   - Guárdalo temporalmente en un lugar seguro

📋 **Token copiado**: `_____________________________________________`

aad5c734-112a-41f3-8267-66d6b2276974

---

## Paso 2: Vincular Proyecto Railway

Necesitamos saber a qué proyecto deployar.

### En la terminal:

```bash
# 1. Asegurarse de estar en el directorio del proyecto
cd c:\Users\patriciods\chat-analytics-api

# 2. Ver proyectos disponibles
railway projects

# 3. Vincular al proyecto correcto
railway link

# Selecciona el proyecto de chat-analytics-api cuando te pregunte
```

**Resultado esperado**: Se crea un archivo `.railway.json` en tu proyecto.

```bash
# 4. Verificar que se creó el archivo
cat .railway.json

# Debería mostrar algo como:
# {
#   "projectId": "abc123...",
#   "environmentId": "xyz789..."
# }
```

---

## Paso 3: Configurar Secret en GitHub

1. **Ir a tu repositorio en GitHub**:
   - https://github.com/patriciodunstan/chat-analytics-api

2. **Navegar a Settings**:
   - Click en **"Settings"** (arriba a la derecha)

3. **Ir a Secrets**:
   - En el menú izquierdo: **"Secrets and variables"** → **"Actions"**

4. **Crear Secret**:
   - Click en **"New repository secret"**

   **Configuración**:
   - Name: `RAILWAY_TOKEN`
   - Secret: Pega el token que copiaste en el Paso 1
   - Click en **"Add secret"**

5. **Verificar**:
   - Deberías ver `RAILWAY_TOKEN` en la lista de secrets
   - El valor estará oculto (●●●●●●)

✅ **Secret configurado correctamente**

---

## Paso 4: Verificar Variables de Entorno en Railway

Asegurarse de que Railway tiene todas las variables necesarias:

### En terminal:

```bash
# Ver variables actuales
railway variables
```

**Variables requeridas** (deberían estar configuradas):
- ✅ `DATABASE_URL` (auto-configurada si agregaste PostgreSQL)
- ✅ `JWT_SECRET`
- ✅ `GEMINI_API_KEY`
- ✅ `CORS_ORIGINS`
- ✅ `ENVIRONMENT=production`

### Si falta alguna:

```bash
# Agregar variable faltante
railway variables set VARIABLE_NAME="valor"

# Ejemplo:
railway variables set JWT_SECRET="$(openssl rand -hex 32)"
railway variables set GEMINI_API_KEY="tu-api-key"
railway variables set CORS_ORIGINS="https://tu-frontend.com"
railway variables set ENVIRONMENT="production"
```

---

## Paso 5: Commit de Archivos de CI/CD

```bash
# 1. Ver qué archivos nuevos hay
git status

# Deberías ver:
# - .github/workflows/deploy.yml
# - .github/workflows/ci.yml
# - .github/RAILWAY_SETUP.md
# - .railway.json (si hiciste railway link)

# 2. Agregar todos los archivos
git add .github/
git add .railway.json  # Si existe
git add README.md

# 3. Commit
git commit -m "ci: add GitHub Actions workflows for CI/CD with Railway"

# 4. Push
git push
```

---

## Paso 6: Verificar que Funciona

### En GitHub:

1. **Ir a Actions**:
   - https://github.com/patriciodunstan/chat-analytics-api/actions

2. **Ver el Workflow ejecutándose**:
   - Deberías ver un workflow "Deploy to Railway" corriendo
   - Click en él para ver detalles

3. **Esperar a que termine** (~5 minutos):
   - ✅ Test (tests con PostgreSQL)
   - ✅ Lint (validación de código)
   - ✅ Build (build de Docker)
   - ✅ Deploy (deploy a Railway)

### Si todo sale bien:

- ✅ GitHub Actions: Verde
- ✅ Railway: Nuevo deployment
- ✅ App funcionando en Railway

### En Railway:

```bash
# Ver status del deployment
railway status

# Ver logs
railway logs
```

---

## Paso 7: Test del Deploy

```bash
# Obtener URL de la app
railway open

# O ver la URL
railway domain

# Probar health check
curl https://tu-app.up.railway.app/health

# Debería responder:
# {"status":"healthy","environment":"production"}
```

---

## ✅ Checklist Final

Marca cada item cuando lo completes:

- [ ] **Paso 1**: Railway Token obtenido y guardado
- [ ] **Paso 2**: `railway link` ejecutado, `.railway.json` creado
- [ ] **Paso 3**: Secret `RAILWAY_TOKEN` configurado en GitHub
- [ ] **Paso 4**: Variables de entorno verificadas en Railway
- [ ] **Paso 5**: Archivos commiteados y pusheados
- [ ] **Paso 6**: GitHub Actions ejecutado exitosamente
- [ ] **Paso 7**: App funcionando en Railway

---

## 🐛 Troubleshooting

### Error: "No project linked"

```bash
railway link
git add .railway.json
git commit -m "chore: link railway project"
git push
```

### Error: "RAILWAY_TOKEN not found"

1. Verifica en GitHub → Settings → Secrets que existe `RAILWAY_TOKEN`
2. El nombre debe ser exactamente `RAILWAY_TOKEN` (mayúsculas)

### Error en tests de GitHub Actions

```bash
# Ver logs detallados en:
# GitHub → Actions → Click en el workflow → Click en el job fallido
```

### Deploy exitoso pero app no funciona

```bash
# Ver logs en Railway
railway logs

# Verificar variables de entorno
railway variables
```

---

## 📝 Notas Importantes

1. **Token de Railway**: Nunca lo commits en git, solo en GitHub Secrets
2. **`.railway.json`**: SÍ se debe commitear (solo tiene IDs, no secrets)
3. **Primer deploy**: Puede tardar más (5-10 min) por build de Docker
4. **Deploys siguientes**: ~3-5 minutos

---

## 🎯 Siguiente: Workflow de Desarrollo

Una vez configurado, el flujo será:

```bash
# 1. Hacer cambios
git checkout -b feature/nueva-funcionalidad
# ... hacer cambios ...
git commit -m "feat: nueva funcionalidad"
git push

# 2. Crear PR en GitHub
# → CI se ejecuta automáticamente (tests + build)

# 3. Merge a main
# → Deploy automático a Railway

# 4. Verificar
railway logs
```

---

## ¿Listo para empezar?

Comienza por el **Paso 1** y sigue en orden. ¡Éxito! 🚀
