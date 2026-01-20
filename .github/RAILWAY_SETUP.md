# GitHub Actions + Railway Setup

Guía para configurar CI/CD con GitHub Actions y deploy automático a Railway.

---

## 1. Obtener Railway Token

### Opción A: Desde Railway Dashboard

1. Ve a [railway.app/account/tokens](https://railway.app/account/tokens)
2. Click en "Create Token"
3. Dale un nombre: `github-actions-deploy`
4. Copia el token (solo se muestra una vez)

### Opción B: Desde Railway CLI

```bash
railway login
railway whoami --token
```

---

## 2. Configurar Secret en GitHub

1. Ve a tu repositorio en GitHub
2. Settings → Secrets and variables → Actions
3. Click en "New repository secret"
4. Nombre: `RAILWAY_TOKEN`
5. Valor: Pega el token de Railway
6. Click en "Add secret"

---

## 3. Vincular Railway Project

El workflow necesita saber a qué proyecto de Railway deployar.

### Método 1: Archivo de configuración (Recomendado)

Ejecuta localmente:

```bash
railway link
```

Esto crea un archivo `.railway.json` con el ID del proyecto. Commitéalo:

```bash
git add .railway.json
git commit -m "chore: add railway project config"
git push
```

### Método 2: Variable de entorno

En GitHub → Settings → Secrets and variables → Actions → Variables:

- `RAILWAY_PROJECT_ID`: ID del proyecto Railway
- `RAILWAY_SERVICE`: Nombre del servicio (opcional)

---

## 4. Workflows Creados

### `deploy.yml` - Deploy a Railway

**Trigger**: Push a `main`

**Jobs**:
1. ✅ **Test**: Ejecuta pytest con PostgreSQL
2. ✅ **Lint**: Ruff + MyPy
3. ✅ **Build**: Build y test de Docker image
4. 🚀 **Deploy**: Deploy a Railway (solo si todo pasa)

**Tiempo estimado**: 3-5 minutos

### `ci.yml` - Tests en PRs

**Trigger**: Pull Request a `main`

**Jobs**:
1. ✅ **Test**: Ejecuta pytest
2. ✅ **Docker**: Build de imagen

**Tiempo estimado**: 2-3 minutos

---

## 5. Verificar Setup

### Test local del workflow

```bash
# Instalar act (GitHub Actions local)
# https://github.com/nektos/act

# Ejecutar workflow localmente
act push -j test
```

### Primer deploy

```bash
# Hacer un cambio y push
git add .
git commit -m "test: trigger github actions"
git push
```

Ve a GitHub → Actions y verás el workflow ejecutándose.

---

## 6. Flujo de Trabajo

### Para features nuevos:

```bash
# 1. Crear branch
git checkout -b feature/nueva-funcionalidad

# 2. Hacer cambios y commit
git add .
git commit -m "feat: nueva funcionalidad"
git push origin feature/nueva-funcionalidad

# 3. Crear Pull Request en GitHub
# → CI workflow se ejecuta automáticamente
# → Tests, lint, docker build

# 4. Merge a main
# → Deploy workflow se ejecuta
# → Tests → Lint → Build → Deploy a Railway
```

### Para hotfixes:

```bash
git checkout main
git pull
# Hacer fix
git add .
git commit -m "fix: critical bug"
git push
# → Deploy automático a Railway
```

---

## 7. Monitoreo

### Ver logs de deploy

**En GitHub**:
- Actions → Deploy to Railway → Ver job "Deploy to Railway"

**En Railway**:
- Dashboard → Tu proyecto → Deployments → Ver logs

### Rollback si algo falla

**Opción 1: Desde Railway dashboard**
- Deployments → Click en deploy anterior → "Redeploy"

**Opción 2: Git revert**
```bash
git revert HEAD
git push
# → Nuevo deploy automático con código anterior
```

---

## 8. Configuración Avanzada

### Environments en GitHub

Para múltiples entornos (staging, production):

1. GitHub → Settings → Environments
2. Crear "production" environment
3. Agregar protection rules:
   - Required reviewers
   - Wait timer
4. Modificar `deploy.yml`:

```yaml
deploy:
  environment: production
  # ...
```

### Deploy preview en PRs

Para crear deployments temporales por PR:

```yaml
deploy-preview:
  if: github.event_name == 'pull_request'
  steps:
    - name: Deploy PR preview
      run: railway up --detach --environment pr-${{ github.event.number }}
```

### Notificaciones

Agregar al final de `deploy.yml`:

```yaml
      - name: Notify Slack
        if: failure()
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "❌ Deploy failed: ${{ github.sha }}"
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

---

## 9. Troubleshooting

### Error: "RAILWAY_TOKEN not found"

**Solución**: Verificar que el secret esté configurado correctamente en GitHub.

```bash
# Verificar en GitHub Settings → Secrets → RAILWAY_TOKEN
```

### Error: "No project linked"

**Solución**: Crear `.railway.json`:

```bash
railway link
git add .railway.json
git commit -m "chore: link railway project"
git push
```

### Deploy exitoso pero app no funciona

**Solución**: Verificar variables de entorno en Railway dashboard.

Asegurarse de que estén configuradas:
- `DATABASE_URL` (desde PostgreSQL service)
- `JWT_SECRET`
- `GEMINI_API_KEY`
- `CORS_ORIGINS`

### Tests fallan en CI pero pasan localmente

**Causa común**: Diferencias de entorno.

**Solución**: Verificar en `.github/workflows/deploy.yml` que las env vars de test estén correctas.

---

## 10. Badges para README

Agregar al README.md:

```markdown
[![Deploy](https://github.com/USER/REPO/actions/workflows/deploy.yml/badge.svg)](https://github.com/USER/REPO/actions/workflows/deploy.yml)
[![CI](https://github.com/USER/REPO/actions/workflows/ci.yml/badge.svg)](https://github.com/USER/REPO/actions/workflows/ci.yml)
```

---

## Referencias

- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Railway CLI Docs](https://docs.railway.app/develop/cli)
- [Railway GitHub Integration](https://docs.railway.app/deploy/integrations#github)
