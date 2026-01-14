# Jira CSV Processor

Script para procesar archivos CSV y obtener fechas de cambio de estado desde Jira, actualizado automáticamente con GitHub Actions.

## Características

- ✅ Obtiene issues desde Jira usando consultas JQL
- ✅ Busca fechas de cambio de estado: "with RSOC", "with Local Security", "Closed"
- ✅ Busca fechas de "First response" (asignación a personas específicas)
- ✅ Ejecución automática cada 9 horas (6 AM, 3 PM, 12 AM UTC) mediante GitHub Actions
- ✅ Actualización automática del repositorio con los resultados

## Instalación

1. Clonar el repositorio:
```bash
git clone <tu-repositorio>
cd LA
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Configurar credenciales de Jira:

**Opción A: Usar config.py (recomendado para desarrollo local)**
```bash
cp config.example.py config.py
# Editar config.py con tus credenciales
```

**Opción B: Usar variables de entorno (.env)**
```bash
# Crear archivo .env con:
JIRA_SERVER=https://tu-dominio.atlassian.net
JIRA_EMAIL=tu-email@ejemplo.com
JIRA_API_TOKEN=tu-token
```

## Configuración de GitHub Actions

Para que el workflow funcione automáticamente, necesitas configurar los siguientes secrets en GitHub:

1. Ve a tu repositorio en GitHub
2. Settings → Secrets and variables → Actions
3. Agrega los siguientes secrets:
   - `JIRA_SERVER`: URL de tu instancia de Jira (ej: `https://tu-dominio.atlassian.net`)
   - `JIRA_EMAIL`: Tu email de Jira
   - `JIRA_API_TOKEN`: Tu token de API de Jira

### Horarios de ejecución

El workflow se ejecuta automáticamente cada 9 horas:
- **6:00 AM UTC** (medianoche en algunas zonas)
- **3:00 PM UTC** (15:00)
- **12:00 AM UTC** (medianoche)

Para cambiar los horarios, edita el archivo `.github/workflows/process-jira.yml` y modifica los valores de `cron`.

## Uso Local

### 1. Obtener issues desde Jira

```bash
python obtener_issues_jql.py Libro1.csv 200
```

Este script ejecuta la consulta JQL:
```
created >= -30d AND project = TPGSOC AND assignee IN membersOf("RSOC ILATAM L1") ORDER BY created DESC
```

### 2. Procesar CSV y obtener fechas

```bash
python procesar_csv.py
```

El script buscará automáticamente:
- Fechas de cambio a "with RSOC"
- Fechas de cambio a "with Local Security"
- Fechas de cambio a "Closed"
- Fechas de "First response" (cuando se asignó a personas específicas)

## Archivos

- `Libro1.csv`: Archivo de entrada/salida con las claves de issues
- `obtener_issues_jql.py`: Script que obtiene issues desde Jira usando JQL
- `procesar_csv.py`: Script principal que procesa el CSV y busca fechas
- `jira_integration.py`: Clase para interactuar con la API de Jira
- `config.example.py`: Plantilla de configuración
- `.github/workflows/process-jira.yml`: Workflow de GitHub Actions

## Estructura del CSV

El archivo `Libro1.csv` tiene las siguientes columnas:

- `Clave`: Clave del issue (ej: TPGSOC-1329200)
- `with RSOC`: Fecha de cambio a estado "with RSOC"
- `with Local Security`: Fecha de cambio a estado "with Local Security"
- `Closed`: Fecha de cambio a estado "Closed"
- `First response`: Fecha cuando se asignó a alguna persona específica

## Personas para First Response

El script busca asignaciones a las siguientes personas:
- Angela Garnica Centanaro
- Daniel Lara
- Juan Sarmiento Montoya
- Julian Sarmiento Florez
- Oscar Riveros Rodriguez
- Sebastian Ahumada Segrera

## Notas

- El archivo `config.py` está en `.gitignore` y no se sube al repositorio
- Los archivos de backup (`.backup`, `.backup_*`) también están excluidos
- El workflow de GitHub Actions actualiza automáticamente `Libro1.csv` en el repositorio
