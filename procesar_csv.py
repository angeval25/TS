"""
Script para procesar CSV y llenar fechas de cambio de estado
Lee Libro1.csv y busca fechas de cambio a "with RSOC" y "with Local Security"
"""
from jira_integration import JiraIntegration
import csv
import os
from datetime import datetime

def procesar_csv(archivo_entrada='Libro1.csv', archivo_salida=None):
    """
    Procesa el CSV y llena las columnas con fechas de cambio de estado
    
    Args:
        archivo_entrada: Nombre del archivo CSV de entrada
        archivo_salida: Nombre del archivo CSV de salida (si None, sobrescribe el original)
    """
    
    if archivo_salida is None:
        archivo_salida = archivo_entrada
    
    # Inicializar conexión a Jira
    try:
        print("[*] Conectando a Jira...")
        jira = JiraIntegration()
        print("[OK] Conexion establecida\n")
    except Exception as e:
        print(f"[ERROR] Error al conectar con Jira: {e}")
        return
    
    # Leer el CSV
    print(f"[*] Leyendo archivo: {archivo_entrada}")
    issues = []
    
    # Intentar diferentes codificaciones
    encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']
    
    for encoding in encodings:
        try:
            with open(archivo_entrada, 'r', encoding=encoding) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    issue_key = row.get('Clave', '').strip()
                    if issue_key:
                        issues.append({
                            'Clave': issue_key,
                            'with RSOC': row.get('with RSOC', '').strip(),
                            'with Local Security': row.get('with Local Security', '').strip(),
                            'Closed': row.get('Closed', '').strip(),
                            'First response': row.get('First response', '').strip()
                        })
            print(f"[OK] Se encontraron {len(issues)} issues en el CSV (encoding: {encoding})\n")
            break
        except Exception as e:
            if encoding == encodings[-1]:  # Último intento
                print(f"[ERROR] Error al leer el CSV: {e}")
                return
            continue
    
    if not issues:
        print("[ERROR] No se encontraron issues en el CSV")
        return
    
    # Procesar cada issue
    print("[*] Procesando issues...")
    print("-" * 80)
    
    encontrados_rsoc = 0
    encontrados_local = 0
    encontrados_closed = 0
    encontrados_first_response = 0
    errores = 0
    
    # Lista de personas para First response
    target_assignees = [
        'Angela Garnica Centanaro',
        'Daniel Lara',
        'Juan Sarmiento Montoya',
        'Julian Sarmiento Florez',
        'Oscar Riveros Rodriguez',
        'Sebastian Ahumada Segrera'
    ]
    
    for i, issue_data in enumerate(issues, 1):
        issue_key = issue_data['Clave']
        print(f"[{i}/{len(issues)}] {issue_key}...", end=' ')
        
        # Si ya tiene todas las fechas, saltar
        if (issue_data['with RSOC'] and issue_data['with Local Security'] and 
            issue_data['Closed'] and issue_data['First response']):
            print("(ya tiene datos)")
            continue
        
        try:
            # Buscar fecha de cambio a "with RSOC"
            if not issue_data['with RSOC']:
                rsoc_result = jira.get_status_change_date(issue_key, "with RSOC")
                if rsoc_result:
                    issue_data['with RSOC'] = rsoc_result['date']
                    encontrados_rsoc += 1
                    print("RSOC: OK", end=' ')
                else:
                    print("RSOC: no encontrado", end=' ')
            else:
                print("RSOC: ya existe", end=' ')
            
            # Buscar fecha de cambio a "with Local Security"
            if not issue_data['with Local Security']:
                local_result = jira.get_status_change_date(issue_key, "with Local Security")
                if local_result:
                    issue_data['with Local Security'] = local_result['date']
                    encontrados_local += 1
                    print("Local: OK", end=' ')
                else:
                    print("Local: no encontrado", end=' ')
            else:
                print("Local: ya existe", end=' ')
            
            # Buscar fecha de cambio a "Closed"
            if not issue_data['Closed']:
                closed_result = jira.get_status_change_date(issue_key, "Closed")
                if closed_result:
                    issue_data['Closed'] = closed_result['date']
                    encontrados_closed += 1
                    print("Closed: OK", end=' ')
                else:
                    print("Closed: no encontrado", end=' ')
            else:
                print("Closed: ya existe", end=' ')
            
            # Buscar fecha de asignación a personas específicas (First response)
            if not issue_data['First response']:
                first_response_result = jira.get_assignee_change_date(issue_key, target_assignees)
                if first_response_result:
                    issue_data['First response'] = first_response_result['date']
                    encontrados_first_response += 1
                    print("First response: OK", end=' ')
                else:
                    print("First response: no encontrado", end=' ')
            else:
                print("First response: ya existe", end=' ')
            
            print()  # Nueva línea
            
        except Exception as e:
            errores += 1
            print(f"[ERROR] {e}")
            # Continuar con el siguiente issue
        
        # Mostrar progreso cada 10 issues
        if i % 10 == 0:
            print(f"\n[*] Progreso: {i}/{len(issues)} procesados")
            print(f"    RSOC encontrados: {encontrados_rsoc}")
            print(f"    Local Security encontrados: {encontrados_local}")
            print(f"    Closed encontrados: {encontrados_closed}")
            print(f"    First response encontrados: {encontrados_first_response}")
            print(f"    Errores: {errores}\n")
    
    print("-" * 80)
    print(f"\n[OK] Procesamiento completado")
    print(f"    Total issues: {len(issues)}")
    print(f"    RSOC encontrados: {encontrados_rsoc}")
    print(f"    Local Security encontrados: {encontrados_local}")
    print(f"    Closed encontrados: {encontrados_closed}")
    print(f"    First response encontrados: {encontrados_first_response}")
    print(f"    Errores: {errores}")
    
    # Escribir el CSV actualizado
    print(f"\n[*] Guardando resultados en: {archivo_salida}")
    try:
        with open(archivo_salida, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['Clave', 'with RSOC', 'with Local Security', 'Closed', 'First response']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            writer.writeheader()
            for issue_data in issues:
                writer.writerow(issue_data)
        
        print(f"[OK] Archivo guardado exitosamente: {archivo_salida}")
        
        # Estadísticas finales
        con_rsoc = sum(1 for i in issues if i['with RSOC'])
        con_local = sum(1 for i in issues if i['with Local Security'])
        con_closed = sum(1 for i in issues if i['Closed'])
        con_first_response = sum(1 for i in issues if i['First response'])
        completos = sum(1 for i in issues if i['with RSOC'] and i['with Local Security'])
        
        print(f"\n[*] Estadisticas finales:")
        print(f"    Issues con fecha 'with RSOC': {con_rsoc}")
        print(f"    Issues con fecha 'with Local Security': {con_local}")
        print(f"    Issues con fecha 'Closed': {con_closed}")
        print(f"    Issues con fecha 'First response': {con_first_response}")
        print(f"    Issues completos (ambas fechas): {completos}")
        
    except Exception as e:
        print(f"[ERROR] Error al guardar el CSV: {e}")


if __name__ == "__main__":
    # Procesar el CSV
    # Por defecto sobrescribe el archivo original, pero puedes crear una copia primero
    import sys
    
    archivo_entrada = sys.argv[1] if len(sys.argv) > 1 else "Libro1.csv"
    
    if not os.path.exists(archivo_entrada):
        print(f"[ERROR] El archivo {archivo_entrada} no existe")
        sys.exit(1)
    
    # Verificar que el archivo tenga contenido
    with open(archivo_entrada, 'r', encoding='utf-8-sig') as f:
        lines = f.readlines()
        if len(lines) <= 1:
            print(f"[ERROR] El archivo {archivo_entrada} solo tiene la cabecera o está vacío")
            print(f"       Total de lineas: {len(lines)}")
            print(f"       Asegurate de que el CSV tenga los issues en la columna 'Clave'")
            sys.exit(1)
    
    # Crear copia de respaldo
    if os.path.exists(archivo_entrada):
        import shutil
        backup = f"{archivo_entrada}.backup"
        shutil.copy2(archivo_entrada, backup)
        print(f"[*] Copia de respaldo creada: {backup}\n")
    
    procesar_csv(archivo_entrada)

