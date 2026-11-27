PYTHON ACADEMY - VERSION 0.3.0

NOVEDADES
- Boton "Buscar actualizaciones" en la barra lateral.
- Actualizador integrado que consulta GitHub Releases y descarga el ZIP de la nueva version.
- Las actualizaciones reemplazan archivos de la aplicacion sin modificar .venv ni update_config.json.
- Copias de seguridad de los archivos anteriores en .update_backups/.
- El progreso de las lecciones ahora se guarda en ~/.local/share/python-academy/progress.json.

REQUISITOS
- Linux (Debian, Ubuntu, Kali y derivados).
- Python 3.10 o superior.
- Flet 1.1.4 o compatible.

PRIMERA EJECUCION
1. Abre una terminal dentro de esta carpeta.
2. Crea el entorno virtual:
   python3 -m venv .venv
3. Activalo:
   source .venv/bin/activate
4. Instala Flet:
   pip install flet
5. Ejecuta:
   flet run main.py

CONFIGURAR ACTUALIZACIONES AUTOMATICAS (SOLO UNA VEZ)
El actualizador necesita un repositorio publico de GitHub donde se publiquen las versiones.
No se ha configurado un repositorio porque debe pertenecer al usuario.

1. Crea un repositorio publico en GitHub, por ejemplo: python-academy.
2. Sube el ZIP PythonAcademy_Linux_v0.3.0.zip como una Release con etiqueta v0.3.0.
   El ZIP debe conservar la carpeta superior "python_academy/" y contener main.py y version.json.
3. Abre el archivo update_config.json de esta carpeta.
4. Escribe el usuario y el nombre del repositorio:
   {
     "github_repo": "TU_USUARIO/python-academy"
   }
5. Guarda el archivo y reinicia la aplicacion.
6. En futuras versiones, publica un ZIP nuevo como Release de GitHub con una etiqueta mayor,
   por ejemplo v0.3.1. Incluye main.py, update_manager.py, version.json, README.txt y los
   demas archivos del programa dentro de python_academy/.
7. Pulsa "Buscar actualizaciones" dentro de Python Academy. La aplicacion descargara e
   instalara la nueva version. Luego cierrala y vuelve a abrirla.

IMPORTANTE SOBRE EL PROGRESO Y LOS DATOS
- El actualizador conserva .venv y update_config.json.
- El progreso esta fuera de la carpeta del programa: ~/.local/share/python-academy/.
- Las versiones anteriores de los archivos reemplazados se guardan en .update_backups/.
- No hace falta borrar la carpeta ni volver a instalar Flet para actualizar el codigo.
- Mientras no se configure GitHub Releases, el boton avisara que falta configurar el repositorio.
