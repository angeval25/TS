"""
Jira API Integration Script
Handles interactions with Jira API using the provided token.
Incluye funcionalidad para obtener changelog y detectar cambios de estado a "with RSOC".
"""
import os
from dotenv import load_dotenv
from jira import JIRA
import csv
from datetime import datetime
from typing import Optional, List, Dict
import requests
from requests.auth import HTTPBasicAuth

# Load environment variables
load_dotenv()

class JiraIntegration:
    def __init__(self):
        # Try to load from config.py first (tiene prioridad)
        self.api_token = None
        self.server = None
        self.email = None
        
        try:
            import config
            config_data = getattr(config, 'JIRA_CONFIG', {})
            self.api_token = config_data.get('api_token')
            self.server = config_data.get('server')
            self.email = config_data.get('email')
        except ImportError:
            pass
        
        # Si no está en config.py, intentar desde variables de entorno
        if not all([self.api_token, self.server, self.email]):
            self.api_token = self.api_token or os.getenv('JIRA_API_TOKEN')
            self.server = self.server or os.getenv('JIRA_SERVER')
            self.email = self.email or os.getenv('JIRA_EMAIL')
        
        if not all([self.api_token, self.server, self.email]):
            raise ValueError(
                "Missing required configuration. Please set JIRA_API_TOKEN, JIRA_SERVER, and JIRA_EMAIL "
                "in your .env file or create a config.py file from config.example.py"
            )
        
        # Asegurar que el servidor no tenga barra final
        self.server = self.server.rstrip('/')
        
        # Initialize Jira connection
        # Dejar que la biblioteca jira use la versión por defecto (compatible con v2 y v3)
        self.jira = JIRA(
            server=self.server,
            basic_auth=(self.email, self.api_token)
        )
    
    def create_issue(self, project_key, summary, description, issue_type='Task', **kwargs):
        """Create a Jira issue"""
        issue_dict = {
            'project': {'key': project_key},
            'summary': summary,
            'description': description,
            'issuetype': {'name': issue_type},
        }
        issue_dict.update(kwargs)
        
        issue = self.jira.create_issue(fields=issue_dict)
        print(f"Created issue: {issue.key} - {issue.fields.summary}")
        return issue
    
    def get_projects(self):
        """Get list of accessible Jira projects"""
        projects = self.jira.projects()
        return [{'key': p.key, 'name': p.name} for p in projects]
    
    def search_issues(self, jql_query, max_results=50):
        """
        Search for issues using JQL con paginación correcta usando API v3
        
        Args:
            jql_query: Consulta JQL
            max_results: Número máximo de resultados (None para obtener todos)
            
        Returns:
            Lista de objetos Issue de la biblioteca jira
        """
        # Usar requests directamente con el endpoint correcto de API v3
        # El endpoint /rest/api/3/search/jql requiere un formato específico
        url = f"{self.server}/rest/api/3/search/jql"
            
        auth = HTTPBasicAuth(self.email, self.api_token)
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        all_issues = []
        next_page_token = None
        page_num = 0
        
        # Si max_results es None, obtener todos los resultados disponibles
        while max_results is None or len(all_issues) < max_results:
            # Formato correcto para /rest/api/3/search/jql
            # El body debe ser un objeto JSON con el campo 'jql' y opcionalmente 'nextPageToken'
            payload = {
                'jql': jql_query,
                'maxResults': 50  # API v3 limita a 50 por página
            }
            
            # Si hay un límite y estamos cerca, ajustar maxResults
            if max_results is not None:
                remaining = max_results - len(all_issues)
                if remaining < 50:
                    payload['maxResults'] = remaining
            
            # Si hay un token de siguiente página, usarlo
            if next_page_token:
                payload['nextPageToken'] = next_page_token
            
            try:
                response = requests.post(url, json=payload, auth=auth, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                issues_data = data.get('issues', [])
                
                if not issues_data:
                    break
                
                # Obtener información de paginación
                is_last = data.get('isLast', False)
                next_page_token = data.get('nextPageToken')
                page_num += 1
                
                # Obtener cada issue usando la biblioteca jira
                for issue_data in issues_data:
                    # Si tenemos un límite y ya lo alcanzamos, salir
                    if max_results is not None and len(all_issues) >= max_results:
                        break
                    
                    # En API v3, la estructura puede ser diferente
                    # Intentar diferentes formas de acceder a la key
                    issue_key = None
                    if isinstance(issue_data, dict):
                        issue_key = issue_data.get('key') or issue_data.get('id')
                    elif hasattr(issue_data, 'key'):
                        issue_key = issue_data.key
                    elif hasattr(issue_data, 'id'):
                        issue_key = issue_data.id
                    
                    if not issue_key:
                        # Si no se puede obtener la key, saltar este issue
                        continue
                    
                    try:
                        issue = self.jira.issue(issue_key)
                        all_issues.append(issue)
                    except Exception as e:
                        # Si falla, crear un objeto simple
                        class SimpleIssue:
                            def __init__(self, key):
                                self.key = key
                        all_issues.append(SimpleIssue(issue_key))
                
                # Mostrar progreso
                print(f"    Progreso: {len(all_issues)} issues obtenidos (página {page_num})...", end='\r')
                
                # Si es la última página, alcanzamos el límite, o no hay más páginas, salir
                if is_last or (max_results is not None and len(all_issues) >= max_results) or not next_page_token:
                    break
                    
            except requests.exceptions.RequestException as e:
                print(f"Error en búsqueda JQL: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    print(f"Response: {e.response.text}")
                break
        
        # Si hay un límite, retornar solo hasta ese límite
        if max_results is not None:
            return all_issues[:max_results]
        return all_issues
    
    def get_changelog(self, issue_key: str) -> List[Dict]:
        """
        Obtiene el historial completo (changelog) de un issue.
        Usa la biblioteca jira que maneja automáticamente la versión de API correcta.
        Si falla, intenta usar requests directamente con API v2.
        
        Args:
            issue_key: La clave del issue (ej: TPGSOC-1329200)
            
        Returns:
            Lista de diccionarios con los cambios realizados
        """
        changelog = []
        
        # Método 1: Intentar con la biblioteca jira (más simple)
        try:
            issue = self.jira.issue(issue_key, expand='changelog')
            
            # Verificar que el changelog existe
            if hasattr(issue, 'changelog') and issue.changelog:
                for history in issue.changelog.histories:
                    created = history.created
                    author = history.author
                    author_name = author.displayName if hasattr(author, 'displayName') else str(author)
                    
                    for item in history.items:
                        changelog.append({
                            'issue_key': issue_key,
                            'date': created,
                            'author': author_name,
                            'field': item.field,
                            'from': item.fromString if hasattr(item, 'fromString') else '',
                            'to': item.toString if hasattr(item, 'toString') else '',
                            'from_id': getattr(item, 'from', None),
                            'to_id': getattr(item, 'to', None)
                        })
            
            if changelog:
                return changelog
        except Exception as e:
            # Si falla, intentar método alternativo
            pass
        
        # Método 2: Si el método 1 no funcionó, usar requests directamente con API v2
        try:
            url = f"{self.server}/rest/api/2/issue/{issue_key}?expand=changelog"
            auth = HTTPBasicAuth(self.email, self.api_token)
            headers = {'Accept': 'application/json'}
            
            response = requests.get(url, auth=auth, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'changelog' in data and 'histories' in data['changelog']:
                for history in data['changelog']['histories']:
                    created = history.get('created', '')
                    author = history.get('author', {})
                    author_name = author.get('displayName', '') if author else ''
                    
                    for item in history.get('items', []):
                        changelog.append({
                            'issue_key': issue_key,
                            'date': created,
                            'author': author_name,
                            'field': item.get('field', ''),
                            'from': item.get('fromString', ''),
                            'to': item.get('toString', ''),
                            'from_id': item.get('from', None),
                            'to_id': item.get('to', None)
                        })
        except Exception as e:
            print(f"Error obteniendo changelog para {issue_key}: {e}")
        
        return changelog
    
    def get_status_change_date(self, issue_key: str, target_status: str = "with RSOC") -> Optional[Dict]:
        """
        Obtiene la fecha exacta en que un caso cambió a un estado específico.
        Si el estado aparece varias veces, retorna la PRIMERA ocurrencia (más antigua).
        
        Args:
            issue_key: La clave del issue (ej: TPGSOC-1329200)
            target_status: El estado objetivo a buscar (default: "with RSOC")
            
        Returns:
            Diccionario con información del cambio o None si no se encontró
        """
        changelog = self.get_changelog(issue_key)
        
        if not changelog:
            # Debug: verificar si el changelog está vacío
            return None
        
        # Ordenar changelog por fecha (del más antiguo al más nuevo) para asegurar que tomamos el PRIMER cambio
        # Convertir fechas a objetos datetime para comparar correctamente
        changelog_sorted = sorted(changelog, key=lambda x: x['date'] if x['date'] else datetime.min)
        
        # Debug: contar cambios de status
        status_changes = [c for c in changelog_sorted if c['field'].lower() == 'status']
        
        for change in changelog_sorted:
            if change['field'].lower() == 'status' and change['to'] and target_status.lower() in change['to'].lower():
                return {
                    'issue_key': issue_key,
                    'status': change['to'],
                    'date': change['date'],
                    'author': change['author'],
                    'from_status': change['from']
                }
        
        return None
    
    def get_assignee_change_date(self, issue_key: str, target_assignees: List[str]) -> Optional[Dict]:
        """
        Obtiene la fecha exacta en que un caso fue asignado a alguna de las personas de la lista.
        Si hay múltiples asignaciones, retorna la PRIMERA ocurrencia (más antigua).
        
        Args:
            issue_key: La clave del issue (ej: TPGSOC-1329200)
            target_assignees: Lista de nombres de personas a buscar
            
        Returns:
            Diccionario con información del cambio o None si no se encontró
        """
        changelog = self.get_changelog(issue_key)
        
        # Ordenar changelog por fecha (del más antiguo al más nuevo) para asegurar que tomamos el PRIMER cambio
        # Convertir fechas a objetos datetime para comparar correctamente
        changelog_sorted = sorted(changelog, key=lambda x: x['date'] if x['date'] else datetime.min)
        
        # Normalizar nombres para comparación (remover acentos, mayúsculas)
        target_assignees_lower = [name.lower().strip() for name in target_assignees]
        
        for change in changelog_sorted:
            if change['field'].lower() == 'assignee' and change['to']:
                assignee_name = change['to'].lower().strip()
                # Verificar si el nombre asignado coincide con alguno de la lista
                for target in target_assignees_lower:
                    if target in assignee_name or assignee_name in target:
                        return {
                            'issue_key': issue_key,
                            'assignee': change['to'],
                            'date': change['date'],
                            'author': change['author'],
                            'from_assignee': change['from']
                        }
        
        return None
    
    def get_rsoc_date_batch(self, issue_keys: List[str]) -> List[Dict]:
        """
        Obtiene la fecha de cambio a "with RSOC" para múltiples issues.
        
        Args:
            issue_keys: Lista de claves de issues (ej: ['TPGSOC-1329200', 'TPGSOC-1329201'])
            
        Returns:
            Lista de diccionarios con los resultados
        """
        results = []
        for issue_key in issue_keys:
            result = self.get_status_change_date(issue_key, "with RSOC")
            if result:
                results.append(result)
            else:
                results.append({
                    'issue_key': issue_key,
                    'status': None,
                    'date': None,
                    'author': None,
                    'from_status': None,
                    'note': 'No se encontró cambio a "with RSOC"'
                })
        return results
    
    def export_rsoc_dates_to_csv(self, issue_keys: List[str], output_file: str = 'rsoc_dates.csv'):
        """
        Exporta las fechas de cambio a "with RSOC" a un archivo CSV.
        
        Args:
            issue_keys: Lista de claves de issues
            output_file: Nombre del archivo de salida
        """
        results = self.get_rsoc_date_batch(issue_keys)
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['issue_key', 'status', 'date', 'author', 'from_status', 'note']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for result in results:
                writer.writerow(result)
        
        print(f"Resultados exportados a {output_file}")
        return results


def main():
    """Example usage"""
    try:
        jira = JiraIntegration()
        
        # List available projects
        print("Available projects:")
        projects = jira.get_projects()
        for project in projects:
            print(f"  - {project['key']}: {project['name']}")
        
        # Ejemplo: Obtener fecha de cambio a "with RSOC" para un issue
        # issue_key = 'TPGSOC-1329200'
        # result = jira.get_status_change_date(issue_key, "with RSOC")
        # if result:
        #     print(f"\nIssue {result['issue_key']} cambió a '{result['status']}' el {result['date']}")
        #     print(f"Cambiado por: {result['author']}")
        #     print(f"Estado anterior: {result['from_status']}")
        # else:
        #     print(f"No se encontró cambio a 'with RSOC' para {issue_key}")
        
        # Ejemplo: Procesar múltiples issues
        # issue_keys = ['TPGSOC-1329200', 'TPGSOC-1329201', 'TPGSOC-1329202']
        # results = jira.get_rsoc_date_batch(issue_keys)
        # for result in results:
        #     print(result)
        
        # Ejemplo: Exportar a CSV
        # jira.export_rsoc_dates_to_csv(issue_keys, 'rsoc_dates.csv')
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()

