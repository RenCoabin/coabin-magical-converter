import tkinter as tk
from tkinter import messagebox, filedialog, TclError
from yt_dlp import YoutubeDL
import threading
import sys, os
from PIL import Image, ImageTk  # pillow needed for Alex Mode

# ---------- RECURSOS ----------
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ---------- FFmpeg PATH ----------
def get_ffmpeg_path():
    """Use bundled ffmpeg.exe instead of system one"""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(__file__)
    return os.path.join(base_path, "ffmpeg.exe")

# ---------- MAIN WINDOW ----------
root = tk.Tk()
root.title("Coabin magical converter")
root.geometry("840x420")
root.resizable(False, False)

# ---------- GLOBAL STATE ----------
current_bg_image = None
bg_label = None

# ---------- DEFINIENDO TEMAS ----------
def apply_light_mode(root):
    root.configure(bg="white")
    for widget in root.winfo_children():
        try:
            widget.configure(bg="white", fg="black")
        except TclError:
            pass

def apply_dark_mode(root):
    root.configure(bg="#1e1e1e")
    for widget in root.winfo_children():
        try:
            widget.configure(bg="#1e1e1e", fg="white")
        except TclError:
            pass

def apply_naughty_mode():
    global current_bg_image, bg_label
    bg_path = resource_path("bgtravieso.jpg")
#por si se pierde el fichero
    if not os.path.exists(bg_path):
        messagebox.showerror("Error", "No se encontró fondo 'bgtravieso.jpg'.")
        return

    if bg_label is not None:
        bg_label.destroy()

    img = Image.open(bg_path)
    img = img.resize((root.winfo_width(), root.winfo_height()))
    current_bg_image = ImageTk.PhotoImage(img)

    bg_label = tk.Label(root, image=current_bg_image)
    bg_label.place(x=0, y=0, relwidth=1, relheight=1)
    bg_label.lower()

    for widget in root.winfo_children():
        if isinstance(widget, (tk.Label, tk.Button, tk.Entry, tk.OptionMenu)):
            widget.configure(bg="#00000080", fg="white")

    footer_label.configure(bg="#000000", fg="white")
    footer_label.lift()

# ---------- MENU ----------
menu_bar = tk.Menu(root)
theme_menu = tk.Menu(menu_bar, tearoff=0)
theme_menu.add_command(label="Light Mode", command=lambda: apply_light_mode(root))
theme_menu.add_command(label="Dark Mode", command=lambda: apply_dark_mode(root))
theme_menu.add_command(label="Naughty Mode", command=apply_naughty_mode)
menu_bar.add_cascade(label="Tema", menu=theme_menu)
root.config(menu=menu_bar)

# ---------- PATH FIX ----------
if getattr(sys, 'frozen', False):
    os.environ['PATH'] += os.pathsep + sys._MEIPASS

# ---------- LOGICA ----------
def download_media(url: str, output_folder: str, mode: str):

    
    ffmpeg_path = get_ffmpeg_path()  # <--- use bundled ffmpeg

    common_ydl_opts = {
    'quiet': True,
    'noplaylist': True,
    'ffmpeg_location': ffmpeg_path,

    # ---- 403 FIXES ----
    'force_ipv4': True,
    'extractor_args': {
        'youtube': {
            'player_client': ['android', 'web'],
            'skip': ['dash', 'hls']
        }
    },
    'http_headers': {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/124.0.0.0 Safari/537.36'
        )
    },

    # Uncomment ONLY if needed
    # 'cookiefile': resource_path('cookies.txt'),
}


    if mode == "mp3":
        ydl_opts = {
            **common_ydl_opts,
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(output_folder, '%(title)s.%(ext)s'),
            'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
}

    else:  # mp4
        selected_quality = quality_var.get()
        quality_formats = {
            "1080p": "bestvideo[height<=1080][vcodec*=avc1]+bestaudio[ext=m4a]/best[ext=mp4]",
            "720p": "bestvideo[height<=720][vcodec*=avc1]+bestaudio[ext=m4a]/best[ext=mp4]",
            "480p": "bestvideo[height<=480][vcodec*=avc1]+bestaudio[ext=m4a]/best[ext=mp4]",
            "360p": "bestvideo[height<=360][vcodec*=avc1]+bestaudio[ext=m4a]/best[ext=mp4]"
        }

        ydl_opts = {
            **common_ydl_opts,
            'format': quality_formats.get(
                selected_quality,
                'bestvideo[vcodec*=avc1]+bestaudio/best'
            ),
            'merge_output_format': 'mp4',
            'postprocessors': [
                {'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'}
            ],
            'outtmpl': os.path.join(output_folder, '%(title)s.%(ext)s'),
        }


    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return info.get('title', 'Unknown title')
    except Exception as e:
        return f"ERROR: {e}"

def start_download(mode: str):
    url = url_entry.get().strip()
    if not url:
        messagebox.showwarning("URL no seleccionada.", "Introduce una URL de YouTube.")
        return

    output_folder = folder_path.get()
    if not output_folder:
        messagebox.showwarning("Carpeta no seleccionada.", "Elige la carpeta de destino.")
        return

    status_label.config(text=f"Descargando como {mode.upper()}...", fg="blue")
    mp3_button.config(state=tk.DISABLED)
    mp4_button.config(state=tk.DISABLED)

    def run():
        result = download_media(url, output_folder, mode)
        if result.startswith("ERROR:"):
            status_label.config(text=result, fg="red")
        else:
            status_label.config(text=f"Descargado: {result}.{mode}", fg="green")
        mp3_button.config(state=tk.NORMAL)
        mp4_button.config(state=tk.NORMAL)

    threading.Thread(target=run, daemon=True).start()

def choose_folder():
    folder = filedialog.askdirectory()
    if folder:
        folder_path.set(folder)

# ---------- ICON ----------
icon_path = resource_path("app.ico")
if os.path.exists(icon_path):
    root.iconbitmap(icon_path)

# ---------- UI ----------
folder_path = tk.StringVar()

tk.Label(root, text="URL de YouTube:").pack(pady=5)
url_entry = tk.Entry(root, width=60)
url_entry.pack(pady=5)

tk.Button(root, text="Carpeta de destino", command=choose_folder).pack(pady=5)
tk.Label(root, textvariable=folder_path, fg="gray").pack(pady=2)

tk.Label(root, text="Calidad de video:").pack(pady=5)
quality_var = tk.StringVar(value="720p")
quality_dropdown = tk.OptionMenu(root, quality_var, "1080p", "720p", "480p", "360p")
quality_dropdown.pack(pady=5)

frame = tk.Frame(root)
frame.pack(pady=10)

mp3_button = tk.Button(frame, text="Descargar MP3 (Audio)", width=20, command=lambda: start_download("mp3"))
mp3_button.grid(row=0, column=0, padx=10)

mp4_button = tk.Button(frame, text="Descargar MP4 (Video)", width=17, command=lambda: start_download("mp4"))
mp4_button.grid(row=0, column=1, padx=10)

status_label = tk.Label(root, text="", fg="black")
status_label.pack(pady=10)

footer_label = tk.Label(root, text="Coabin (May '26)", fg="purple", bg="white")
footer_label.pack(side="bottom", pady=5)
footer_label.lift()

# ---------- EMPEZAR EN MODO CLARO ----------
apply_light_mode(root)

root.mainloop()
