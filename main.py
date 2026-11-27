import asyncio
import json
from pathlib import Path

import flet as ft
from update_manager import UpdateError, check_for_update, current_version, install_update


COURSES = [
    {
        "title": "Carrera 1 · Fundamentos de Python",
        "description": "Aprende desde cero: sintaxis, variables, tipos, decisiones, ciclos y funciones.",
        "lessons": [
            (
                "1. Tu primer programa",
                "Usa print() para mostrar mensajes en pantalla. print() recibe un valor y lo muestra en la terminal o en la salida del programa.",
                'print("Hola mundo")',
                "Hola mundo",
                "Cambia el mensaje para que Python muestre tu nombre.",
            ),
            (
                "2. Variables",
                "Las variables guardan datos para poder utilizarlos más adelante. El signo = asigna un valor a una variable.",
                'nombre = "Jose"\nedad = 29\nprint(f"Hola {nombre}, tienes {edad} años")',
                "Hola Jose, tienes 29 años",
                "Crea una variable llamada objetivo y muestra tu objetivo profesional usando una f-string.",
            ),
            (
                "3. Tipos de datos",
                "Python tiene distintos tipos de datos. str representa texto, int números enteros, float números decimales y bool valores verdaderos o falsos. type() permite consultar el tipo.",
                'nombre = "Jose"\nedad = 29\npeso = 75.5\nestudia = True\n\nprint(type(nombre))\nprint(type(edad))\nprint(type(peso))\nprint(type(estudia))',
                "<class 'str'>\n<class 'int'>\n<class 'float'>\n<class 'bool'>",
                "Crea una variable ciudad con tu ciudad y otra horas_estudio con un número decimal. Muestra sus tipos.",
            ),
            (
                "4. Entrada de datos",
                "input() permite pedir información a la persona que utiliza el programa. El valor recibido por input() es texto (str), incluso si escribe números.",
                'nombre = input("¿Cómo te llamas? ")\nprint(f"Bienvenido, {nombre}")',
                "El programa preguntará tu nombre y después mostrará un saludo.",
                "Pregunta el país donde te gustaría trabajar y muestra una frase usando la respuesta.",
            ),
            (
                "5. Operadores",
                "Los operadores permiten realizar cálculos. Algunos son + (suma), - (resta), * (multiplicación), / (división), // (división entera), % (resto) y ** (potencia).",
                "a = 10\nb = 3\n\nprint(a + b)\nprint(a // b)\nprint(a % b)",
                "13\n3\n1",
                "Crea dos variables numéricas y muestra su suma, resta, multiplicación y división.",
            ),
            (
                "6. Condicionales",
                "if, elif y else permiten que el programa tome decisiones según una condición. La sangría (indentación) define qué instrucciones pertenecen a cada bloque.",
                'edad = 18\n\nif edad >= 18:\n    print("Mayor de edad")\nelse:\n    print("Menor de edad")',
                "Mayor de edad",
                "Cambia la edad y agrega una condición para mostrar si la persona tiene exactamente 18 años.",
            ),
            (
                "7. Ciclos",
                "Los ciclos repiten instrucciones. for se utiliza habitualmente para recorrer elementos o rangos; while repite mientras una condición sea verdadera.",
                "for numero in range(1, 4):\n    print(numero)",
                "1\n2\n3",
                "Haz un ciclo que muestre los números del 1 al 10.",
            ),
            (
                "8. Funciones",
                "Las funciones agrupan instrucciones reutilizables. Se definen con def, pueden recibir parámetros y pueden devolver un resultado con return.",
                'def saludar(nombre):\n    return f"Hola, {nombre}"\n\nprint(saludar("Jose"))',
                "Hola, Jose",
                "Crea una función llamada sumar que reciba dos números y devuelva el resultado.",
            ),
        ],
    },
    {
        "title": "Carrera 2 · Python Intermedio",
        "description": "Domina estructuras, archivos, excepciones, módulos y programación orientada a objetos.",
        "lessons": [],
    },
    {
        "title": "Carrera 3 · SQL y Bases de Datos",
        "description": "Aprende SQL, PostgreSQL, consultas, relaciones y modelado de datos.",
        "lessons": [],
    },
    {
        "title": "Carrera 4 · Backend Developer",
        "description": "Construye APIs con FastAPI, autenticación, validación y pruebas.",
        "lessons": [],
    },
    {
        "title": "Carrera 5 · Profesional",
        "description": "Git, Docker, despliegue, portafolio, entrevistas y preparación para PCAP.",
        "lessons": [],
    },
]


def main(page: ft.Page):
    page.title = "Python Academy"
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.BLUE)
    page.window_width = 1120
    page.window_height = 800
    page.padding = 0

    # El progreso se guarda fuera de la carpeta de la aplicación para que sobreviva
    # a las actualizaciones y a la sustitución de archivos del programa.
    data_dir = Path.home() / ".local" / "share" / "python-academy"
    progress_file = data_dir / "progress.json"

    def load_completed():
        try:
            saved = json.loads(progress_file.read_text(encoding="utf-8"))
            return {(int(item[0]), int(item[1])) for item in saved.get("completed", [])}
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return set()

    def save_completed():
        data_dir.mkdir(parents=True, exist_ok=True)
        payload = {"completed": [list(item) for item in sorted(completed)]}
        progress_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    completed = load_completed()
    content = ft.Column(expand=True, spacing=16, scroll=ft.ScrollMode.AUTO)
    progress_text = ft.Text("0 de 8 lecciones completadas", size=13)
    progress_bar = ft.ProgressBar(value=0, width=320)

    def set_view(controls):
        content.controls.clear()
        content.controls.extend(controls)
        page.update()

    def make_code_panel(code):
        return ft.Container(
            content=ft.Text(
                code,
                selectable=True,
                font_family="monospace",
                size=14,
            ),
            bgcolor=ft.Colors.BLACK,
            padding=16,
            border_radius=10,
            width=None,
        )

    def show_dashboard(e=None):
        cards = []
        for i, course in enumerate(COURSES):
            lesson_count = len(course["lessons"])
            detail = f"{lesson_count} lecciones disponibles" if lesson_count else "Contenido en preparación"
            cards.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(course["title"], size=17, weight=ft.FontWeight.BOLD),
                                ft.Text(course["description"], size=13),
                                ft.Text(detail, size=12, color=ft.Colors.BLUE_200),
                                ft.Button("Abrir carrera", on_click=lambda ev, idx=i: show_course(idx)),
                            ],
                            spacing=9,
                        ),
                        padding=16,
                    )
                )
            )

        done_count = sum(1 for course_idx, _ in completed if course_idx == 0)
        progress_text.value = f"{done_count} de 8 lecciones completadas"
        progress_bar.value = done_count / 8
        set_view(
            [
                ft.Text("Bienvenido a tu academia", size=29, weight=ft.FontWeight.BOLD),
                ft.Text("Una ruta guiada desde cero hasta desarrollar software y APIs."),
                ft.Card(
                    content=ft.Container(
                        content=ft.Column(
                            [
                                ft.Text("Tu progreso", size=18, weight=ft.FontWeight.BOLD),
                                progress_text,
                                progress_bar,
                            ],
                            spacing=10,
                        ),
                        padding=18,
                    )
                ),
                ft.Text("Carreras de aprendizaje", size=22, weight=ft.FontWeight.BOLD),
                *cards,
            ]
        )

    def mark_done(course_idx, lesson_idx):
        completed.add((course_idx, lesson_idx))
        save_completed()
        done_count = sum(1 for c, _ in completed if c == 0)
        progress_text.value = f"{done_count} de 8 lecciones completadas"
        progress_bar.value = done_count / 8
        page.snack_bar = ft.SnackBar(ft.Text("¡Lección marcada como completada!"))
        page.snack_bar.open = True
        page.update()

    def show_lesson(course_idx, lesson_idx):
        course = COURSES[course_idx]
        title, explanation, code, expected, challenge = course["lessons"][lesson_idx]
        is_done = (course_idx, lesson_idx) in completed
        set_view(
            [
                ft.Button("← Volver a la carrera", on_click=lambda e: show_course(course_idx)),
                ft.Text(title, size=27, weight=ft.FontWeight.BOLD),
                ft.Text(explanation, size=15),
                ft.Text("Ejemplo de código", size=18, weight=ft.FontWeight.BOLD),
                make_code_panel(code),
                ft.Text("Salida / comportamiento esperado", size=18, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.Text(expected, selectable=True, font_family="monospace", size=14),
                    bgcolor=ft.Colors.BLACK,
                    padding=16,
                    border_radius=10,
                ),
                ft.Text("Tu desafío", size=18, weight=ft.FontWeight.BOLD),
                ft.Text(challenge, size=14),
                ft.Text(
                    "Consejo: prueba el código en tu terminal. En una próxima versión incorporaremos un editor y ejecución dentro de la academia.",
                    size=12,
                    color=ft.Colors.BLUE_200,
                ),
                ft.Button(
                    "✓ Lección completada" if is_done else "Marcar lección como completada",
                    icon=ft.Icons.CHECK,
                    on_click=lambda e: mark_done(course_idx, lesson_idx),
                    disabled=is_done,
                ),
            ]
        )

    def show_course(course_idx):
        course = COURSES[course_idx]
        if not course["lessons"]:
            set_view(
                [
                    ft.Button("← Volver al inicio", on_click=show_dashboard),
                    ft.Text(course["title"], size=27, weight=ft.FontWeight.BOLD),
                    ft.Text(course["description"], size=15),
                    ft.Text("Contenido en preparación. Primero completa la carrera de Fundamentos de Python.", size=14),
                ]
            )
            return

        lesson_tiles = []
        for idx, lesson in enumerate(course["lessons"]):
            done = (course_idx, idx) in completed
            lesson_tiles.append(
                ft.Card(
                    content=ft.ListTile(
                        leading=ft.Icon(ft.Icons.CHECK_CIRCLE if done else ft.Icons.MENU_BOOK),
                        title=ft.Text(lesson[0]),
                        subtitle=ft.Text(lesson[1], max_lines=2),
                        trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT),
                        on_click=lambda e, lesson_idx=idx: show_lesson(course_idx, lesson_idx),
                    )
                )
            )

        set_view(
            [
                ft.Button("← Volver al inicio", on_click=show_dashboard),
                ft.Text(course["title"], size=27, weight=ft.FontWeight.BOLD),
                ft.Text(course["description"], size=15),
                ft.Text(f"Contenido: {len(course['lessons'])} lecciones", size=13, color=ft.Colors.BLUE_200),
                *lesson_tiles,
            ]
        )

    def notify(message):
        page.snack_bar = ft.SnackBar(ft.Text(message))
        page.snack_bar.open = True
        page.update()

    async def check_updates(e):
        update_button.disabled = True
        update_button.text = "Buscando actualizaciones..."
        page.update()
        try:
            release = await asyncio.to_thread(check_for_update)
            if release is None:
                notify(f"Ya tienes la última versión ({current_version()}).")
                return
            await asyncio.to_thread(install_update, release)
            notify(
                f"Actualización {release.version} instalada. "
                "Cierra y vuelve a abrir Python Academy para usarla."
            )
        except UpdateError as exc:
            notify(str(exc))
        except Exception as exc:
            notify(f"No se pudo actualizar: {exc}")
        finally:
            update_button.disabled = False
            update_button.text = "Buscar actualizaciones"
            page.update()

    update_button = ft.Button("Buscar actualizaciones", on_click=check_updates)

    sidebar_items = [
        ft.Text("🐍 PYTHON ACADEMY", size=18, weight=ft.FontWeight.BOLD),
        ft.Divider(),
        ft.ListTile(
            leading=ft.Icon(ft.Icons.HOME),
            title=ft.Text("Inicio"),
            on_click=show_dashboard,
        ),
        ft.Text("CARRERAS", size=12, weight=ft.FontWeight.BOLD),
    ]
    for idx, course in enumerate(COURSES):
        sidebar_items.append(
            ft.ListTile(
                leading=ft.Icon(ft.Icons.SCHOOL),
                title=ft.Text(course["title"], size=12),
                on_click=lambda e, course_idx=idx: show_course(course_idx),
            )
        )
    sidebar_items.extend(
        [
            ft.Divider(),
            update_button,
            ft.Text(f"Versión {current_version()}", size=10, color=ft.Colors.GREY_500),
            ft.Text("Tu objetivo: Python Backend Developer", size=11, italic=True),
        ]
    )

    sidebar = ft.Container(
        width=245,
        padding=12,
        content=ft.Column(sidebar_items, spacing=4, scroll=ft.ScrollMode.AUTO),
    )
    main_panel = ft.Container(content=content, expand=True, padding=22)
    page.add(
        ft.Row(
            [sidebar, ft.VerticalDivider(width=1), main_panel],
            expand=True,
            spacing=0,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )
    )
    show_dashboard()


ft.run(main)
