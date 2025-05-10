import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

CONFIG_FILE = "config.json"

def load_config():
    """Carga la configuración desde el archivo JSON."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config
        except Exception as e:
            print("Error al cargar la configuración:", e)
    return {}

def save_config(config):
    """Guarda la configuración en el archivo JSON."""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print("Error al guardar la configuración:", e)

def select_folder():
    """Abre un diálogo para seleccionar una carpeta y actualiza el entry correspondiente."""
    folder_path = filedialog.askdirectory()
    if folder_path:
        folder_entry.delete(0, tk.END)
        folder_entry.insert(0, folder_path)
        # Guardar la carpeta seleccionada en la configuración
        config = load_config()
        config["last_folder"] = folder_path
        save_config(config)
def update_progress(progress_var, current, total):
    """Actualiza la barra de progreso."""
    if total > 0:
        progress = (current / total) * 100
        progress_var.set(progress)
        root.update_idletasks()

def load_search_history():
    """Carga el historial de búsquedas desde la configuración."""
    config = load_config()
    return config.get("search_history", [])

def save_search_history(search_term):
    """Guarda un término de búsqueda en el historial."""
    config = load_config()
    history = config.get("search_history", [])
    if search_term in history:
        history.remove(search_term)
    history.insert(0, search_term)
    history = history[:10]  # Mantener solo los últimos 10 términos
    config["search_history"] = history
    save_config(config)
    update_history_menu()

def update_history_menu():
    """Actualiza el menú desplegable del historial."""
    history = load_search_history()
    menu = history_menu.menu
    menu.delete(0, 'end')
    for term in history:
        menu.add_command(
            label=term,
            command=lambda t=term: search_entry.set(t)
        )

def preview_changes():
    """Muestra una vista previa de los cambios sin realizarlos."""
    folder = folder_entry.get()
    search_term = search_entry.get()
    replace_term = replace_entry.get()
    
    if not folder or not search_term:
        messagebox.showwarning("Advertencia", "Por favor, complete los campos requeridos.")
        return

    report_text.delete(1.0, tk.END)
    report = "VISTA PREVIA DE CAMBIOS:\n\n"
    
    total_files = sum(len(files) for _, _, files in os.walk(folder))
    progress_var.set(0)
    files_processed = 0
    
    for root_dir, _, files in os.walk(folder):
        for filename in files:
            file_path = os.path.join(root_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    if search_term in content:
                        report += f"Archivo: {file_path}\n"
                        lines = content.split('\n')
                        for i, line in enumerate(lines, 1):
                            if search_term in line:
                                report += f"Línea {i}:\n"
                                report += f"  Original: {line}\n"
                                report += f"  Cambio:   {line.replace(search_term, replace_term)}\n\n"
            except:
                continue
            
            files_processed += 1
            update_progress(progress_var, files_processed, total_files)
    
    report_text.insert(tk.END, report)

def search_only():
    """Busca la cadena en todos los archivos de la carpeta (y subcarpetas) sin reemplazarla."""
    folder = folder_entry.get()
    search_term = search_entry.get()
    
    if not folder:
        messagebox.showwarning("Advertencia", "Por favor, seleccione una carpeta.")
        return
    if not search_term:
        messagebox.showwarning("Advertencia", "Por favor, ingrese la cadena a buscar.")
        return

    save_search_history(search_term)
    report_text.delete(1.0, tk.END)
    
    total_files = sum(len(files) for _, _, files in os.walk(folder))
    progress_var.set(0)
    files_processed = 0
    total_occurrences = 0
    report = ""

    for root_dir, _, files in os.walk(folder):
        for filename in files:
            file_path = os.path.join(root_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    lines = file.readlines()
            except UnicodeDecodeError:
                continue
            except Exception as e:
                report += f"Error al leer {file_path}: {str(e)}\n"
                continue

            file_occurrences = []
            for line_num, line in enumerate(lines, start=1):
                start_index = 0
                while True:
                    index = line.find(search_term, start_index)
                    if index == -1:
                        break
                    file_occurrences.append((line_num, index + 1, line.strip()))
                    total_occurrences += 1
                    start_index = index + len(search_term)
            
            if file_occurrences:
                report += f"\nArchivo: {file_path}\n"
                for occ in file_occurrences:
                    line_num, col, line = occ
                    report += f"  Línea {line_num}, Columna {col}:\n"
                    report += f"  {line[:col-1]}>>>{search_term}<<<{line[col-1+len(search_term):]}\n"
            
            files_processed += 1
            update_progress(progress_var, files_processed, total_files)

    report += f"\nTotal de archivos analizados: {total_files}\n"
    report += f"Total de ocurrencias encontradas: {total_occurrences}\n"
    report_text.insert(tk.END, report)

def search_and_replace():
    """Busca y reemplaza la cadena en todos los archivos de la carpeta (y subcarpetas)."""
    folder = folder_entry.get()
    search_term = search_entry.get()
    replace_term = replace_entry.get()
    
    if not folder or not search_term:
        messagebox.showwarning("Advertencia", "Por favor, complete los campos requeridos.")
        return

    if not messagebox.askyesno("Confirmar", 
                              "¿Está seguro de que desea realizar el reemplazo?\n"
                              "Este cambio no se puede deshacer."):
        return

    save_search_history(search_term)
    report_text.delete(1.0, tk.END)
    
    total_files = sum(len(files) for _, _, files in os.walk(folder))
    progress_var.set(0)
    files_processed = 0
    total_occurrences = 0
    modified_files = 0
    report = ""

    for root_dir, _, files in os.walk(folder):
        for filename in files:
            file_path = os.path.join(root_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                count = content.count(search_term)
                if count > 0:
                    total_occurrences += count
                    new_content = content.replace(search_term, replace_term)
                    with open(file_path, 'w', encoding='utf-8') as file:
                        file.write(new_content)
                    modified_files += 1
                    report += f"{file_path}: {count} ocurrencia(s) reemplazada(s)\n"
            except UnicodeDecodeError:
                continue
            except Exception as e:
                report += f"Error al procesar {file_path}: {str(e)}\n"
                continue
            
            files_processed += 1
            update_progress(progress_var, files_processed, total_files)

    report += f"\nTotal de archivos analizados: {total_files}\n"
    report += f"Total de ocurrencias encontradas y reemplazadas: {total_occurrences}\n"
    report += f"Total de archivos modificados: {modified_files}\n"
    report_text.insert(tk.END, report)

# Configuración de la ventana principal
root = ttk.Window(themename="flatly")
root.title("Buscador y Reemplazador de Texto")

frame = ttk.Frame(root, padding=10)
frame.pack(fill="both", expand=True)

# Selección de carpeta
folder_label = ttk.Label(frame, text="Carpeta:")
folder_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
folder_entry = ttk.Entry(frame, width=50)
folder_entry.grid(row=0, column=1, padx=5, pady=5)
folder_button = ttk.Button(frame, text="Seleccionar carpeta", command=select_folder)
folder_button.grid(row=0, column=2, padx=5, pady=5)

# Entrada para la cadena a buscar y historial
search_label = ttk.Label(frame, text="Cadena a buscar:")
search_label.grid(row=1, column=0, sticky="w", padx=5, pady=5)
search_entry = ttk.StringVar()
search_entry_widget = ttk.Entry(frame, width=50, textvariable=search_entry)
search_entry_widget.grid(row=1, column=1, padx=5, pady=5)

# Crear el menú de historial correctamente
history_menu = ttk.Menubutton(frame, text="Historial")
history_menu.grid(row=1, column=2, padx=5, pady=5)
history_menu.menu = tk.Menu(history_menu, tearoff=0)
history_menu['menu'] = history_menu.menu 

# Entrada para la cadena de reemplazo
replace_label = ttk.Label(frame, text="Cadena de reemplazo:")
replace_label.grid(row=2, column=0, sticky="w", padx=5, pady=5)
replace_entry = ttk.Entry(frame, width=50)
replace_entry.grid(row=2, column=1, padx=5, pady=5)

# Botones
search_button = ttk.Button(frame, text="Solo Buscar", command=search_only)
search_button.grid(row=3, column=0, padx=5, pady=10)
replace_button = ttk.Button(frame, text="Buscar y Reemplazar", command=search_and_replace)
replace_button.grid(row=3, column=1, padx=5, pady=10)
preview_button = ttk.Button(frame, text="Vista Previa", command=preview_changes)
preview_button.grid(row=3, column=2, padx=5, pady=10)

# Barra de progreso
progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(frame, variable=progress_var, maximum=100)
progress_bar.grid(row=5, column=0, columnspan=3, sticky="ew", padx=5, pady=5)

# Área de reporte
report_text = scrolledtext.ScrolledText(frame, wrap="word", width=80, height=20)
report_text.grid(row=4, column=0, columnspan=3, padx=5, pady=5)

# Cargar configuración inicial
config = load_config()
if "last_folder" in config:
    folder_entry.insert(0, config["last_folder"])
update_history_menu()

root.mainloop()