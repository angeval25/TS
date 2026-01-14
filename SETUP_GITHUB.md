# Guía de Configuración para GitHub Actions

## Pasos para configurar el proyecto en GitHub

### 1. Inicializar el repositorio Git (si aún no lo has hecho)

```bash
git init
git add .
git commit -m "Initial commit: Jira CSV Processor"
git branch -M main
git remote add origin <URL-de-tu-repositorio>
git push -u origin main
```

### 2. Configurar Secrets en GitHub

1. Ve a tu repositorio en GitHub
2. Click en **Settings** (Configuración)
3. En el menú lateral, click en **Secrets and variables** → **Actions**
4. Click en **New repository secret** y agrega los siguientes:

   **Secret 1: JIRA_SERVER**
   - Name: `JIRA_SERVER`
   - Value: `https://tpgsoc.atlassian.net` (o tu URL de Jira)

   **Secret 2: JIRA_EMAIL**
   - Name: `JIRA_EMAIL`
   - Value: Tu email de Jira

   **Secret 3: JIRA_API_TOKEN**
   - Name: `JIRA_API_TOKEN`
   - Value: Tu token de API de Jira

   **Secret 4: FIRST_RESPONSE_ASSIGNEES** (Opcional)
   - Name: `FIRST_RESPONSE_ASSIGNEES`
   - Value: Lista de nombres separados por comas (ej: `Persona 1,Persona 2,Persona 3`)
   - Si no se configura, el workflow funcionará pero no buscará First Response

### 3. Verificar el Workflow

El workflow está configurado para ejecutarse automáticamente:
- **6:00 AM UTC** (cada día)
- **3:00 PM UTC** (15:00, cada día)
- **12:00 AM UTC** (medianoche, cada día)

También puedes ejecutarlo manualmente:
1. Ve a la pestaña **Actions** en GitHub
2. Selecciona el workflow **Process Jira CSV**
3. Click en **Run workflow**

### 4. Ajustar Zona Horaria (Opcional)

Si necesitas cambiar los horarios a una zona horaria específica, edita `.github/workflows/process-jira.yml`:

```yaml
schedule:
  # Para hora de Colombia (UTC-5), ajusta:
  - cron: '0 11 * * *'   # 6:00 AM COT = 11:00 AM UTC
  - cron: '0 20 * * *'   # 3:00 PM COT = 8:00 PM UTC
  - cron: '0 5 * * *'    # 12:00 AM COT = 5:00 AM UTC
```

### 5. Verificar que el Workflow Funciona

1. Después de hacer push, ve a **Actions** en GitHub
2. Deberías ver el workflow listo para ejecutarse
3. Puedes ejecutarlo manualmente para probar
4. Revisa los logs para asegurarte de que todo funciona correctamente

## Archivos Importantes

- ✅ `.github/workflows/process-jira.yml` - Workflow de GitHub Actions
- ✅ `requirements.txt` - Dependencias de Python
- ✅ `config.example.py` - Plantilla de configuración
- ✅ `.gitignore` - Excluye archivos sensibles
- ✅ `README.md` - Documentación del proyecto

## Notas

- El archivo `Libro1.csv` se actualizará automáticamente en el repositorio
- Los cambios se harán commit automáticamente con el mensaje: "Auto-update: Process Jira issues"
- El workflow requiere que tengas permisos de escritura en el repositorio
