"""
Script para obtener issues desde Jira usando JQL y actualizar Libro1.csv
Ejecuta una consulta JQL y llena la columna Clave en Libro1.csv
"""
from jira_integration import JiraIntegration
import csv
import os

def obtener_issues_y_actualizar_csv(archivo_csv='Libro1.csv', max_results=1000):
    """
    Obtiene issues desde Jira usando JQL y actualiza Libro1.csv con las claves
    
    Args:
        archivo_csv: Nombre del archivo CSV a actualizar
        max_results: Número máximo de resultados a obtener
    """
    
    # Consulta JQL
    jql_query = 'created >= -30d AND project = TPGSOC AND assignee IN membersOf("RSOC ILATAM L1") ORDER BY created DESC'
    
    print("=" * 80)
    print("Obteniendo issues desde Jira")
    print("=" * 80)
    print(f"\n[*] Consulta JQL:")
    print(f"    {jql_query}\n")
    
    # Inicializar conexión a Jira
    try:
        print("[*] Conectando a Jira...")
        jira = JiraIntegration()
        print("[OK] Conexion establecida\n")
    except Exception as e:
        print(f"[ERROR] Error al conectar con Jira: {e}")
        return
    
    # Buscar issues - usar un límite alto para obtener todos
    try:
        print(f"[*] Buscando issues (máximo {max_results})...")
        # Usar un límite alto para asegurar que obtenemos todos los resultados
        issues = jira.search_issues(jql_query, max_results=max(max_results, 500))
        print(f"\n[OK] Se encontraron {len(issues)} issues\n")
    except Exception as e:
        print(f"[ERROR] Error al buscar issues: {e}")
        return
    
    if not issues:
        print("[!] No se encontraron issues con los criterios especificados")
        return
    
    # Extraer claves
    claves = []
    for issue in issues:
        claves.append(issue.key)
    
    print(f"[*] Claves obtenidas: {len(claves)}")
    print(f"\n[*] Primeras 10 claves:")
    for i, clave in enumerate(claves[:10], 1):
        print(f"    {i}. {clave}")
    if len(claves) > 10:
        print(f"    ... y {len(claves) - 10} más")
    
    # Leer CSV existente si existe para preservar otras columnas
    issues_existentes = {}
    columnas_existentes = ['Clave']
    
    if os.path.exists(archivo_csv):
        print(f"\n[*] Leyendo archivo existente: {archivo_csv}")
        try:
            with open(archivo_csv, 'r', encoding='utf-8-sig', newline='') as f:
                reader = csv.DictReader(f)
                # Obtener todas las columnas del archivo existente
                if reader.fieldnames:
                    columnas_existentes = list(reader.fieldnames)
                    # Asegurar que 'Clave' esté primero
                    if 'Clave' in columnas_existentes:
                        columnas_existentes.remove('Clave')
                    columnas_existentes = ['Clave'] + columnas_existentes
                
                # Leer datos existentes
                for row in reader:
                    clave = row.get('Clave', '').strip()
                    if clave:
                        issues_existentes[clave] = row
            print(f"[OK] Se leyeron {len(issues_existentes)} issues existentes")
        except Exception as e:
            print(f"[!] Error al leer archivo existente: {e}")
            print(f"    Se creará un archivo nuevo")
    
    # Crear estructura de datos con las nuevas claves
    # Si el issue ya existe, preservar sus datos; si no, crear nuevo registro
    nuevos_issues = []
    for clave in claves:
        if clave in issues_existentes:
            # Preservar datos existentes
            nuevos_issues.append(issues_existentes[clave])
        else:
            # Crear nuevo registro vacío
            nuevo_issue = {'Clave': clave}
            # Agregar otras columnas vacías si existen
            for col in columnas_existentes:
                if col != 'Clave' and col not in nuevo_issue:
                    nuevo_issue[col] = ''
            nuevos_issues.append(nuevo_issue)
    
    # Si no hay columnas definidas, usar las estándar
    if len(columnas_existentes) == 1:  # Solo 'Clave'
        columnas_existentes = ['Clave', 'with RSOC', 'with Local Security', 'Closed', 'First response']
        # Agregar columnas faltantes a los issues existentes
        for issue in nuevos_issues:
            for col in columnas_existentes:
                if col not in issue:
                    issue[col] = ''
    
    # Guardar CSV actualizado
    print(f"\n[*] Guardando {len(nuevos_issues)} issues en: {archivo_csv}")
    try:
        with open(archivo_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=columnas_existentes)
            writer.writeheader()
            for issue in nuevos_issues:
                writer.writerow(issue)
        
        print(f"[OK] Archivo guardado exitosamente")
        print(f"\n[*] Resumen:")
        print(f"    Total issues en CSV: {len(nuevos_issues)}")
        print(f"    Issues nuevos agregados: {len(nuevos_issues) - len(issues_existentes)}")
        print(f"    Issues existentes preservados: {len(issues_existentes)}")
        
    except Exception as e:
        print(f"[ERROR] Error al guardar el CSV: {e}")

if __name__ == "__main__":
    import sys
    
    # Permitir especificar el archivo CSV como argumento
    archivo = sys.argv[1] if len(sys.argv) > 1 else "Libro1.csv"
    
    # Permitir especificar max_results como segundo argumento
    max_results = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    
    obtener_issues_y_actualizar_csv(archivo, max_results)
    
    print("\n" + "=" * 80)
    print("[OK] Proceso completado")
    print("=" * 80)
    print("\n[*] Siguiente paso: Ejecutar 'python procesar_csv.py' para obtener las fechas")
