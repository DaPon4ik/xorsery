import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import cv2
import numpy as np
from PIL import Image, ImageTk
import io
from algorithm import encode, decode


class Steganography:
    MAX_PREVIEW_SIZE = 400

    def __init__(self, root):
        self.root = root
        self.root.title("Пример интерфейса")
        self.root.geometry("800x650")

        self.public_path = tk.StringVar()
        self.secret_path = tk.StringVar()
        self.quality = tk.IntVar(value=50)
        self.encode_password = tk.StringVar()
        self.encoded_key = tk.StringVar()
        self.decode_key = tk.StringVar()
        self.decode_password = tk.StringVar()
        self.decoded_image = None
        self._preview_photo = None

        self._setup_ui()

    def _setup_ui(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)

        encode_frame = ttk.Frame(notebook)
        decode_frame = ttk.Frame(notebook)

        notebook.add(encode_frame, text="Кодирование")
        notebook.add(decode_frame, text="Декодирование")

        self._setup_encode_tab(encode_frame)
        self._setup_decode_tab(decode_frame)

    def _setup_encode_tab(self, parent):
        self._create_file_selector(parent, 0, "Публичное изображение:", self.public_path)
        self._create_file_selector(parent, 1, "Секретное изображение:", self.secret_path)

        ttk.Label(parent, text="Пароль (опционально):").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(parent, textvariable=self.encode_password, width=30).grid(row=2, column=1, sticky='w', padx=5, pady=5)

        ttk.Label(parent, text="Качество (1-100):").grid(row=3, column=0, sticky='w', padx=5, pady=5)

        quality_frame = ttk.Frame(parent)
        quality_frame.grid(row=3, column=1, columnspan=2, sticky='ew', padx=5, pady=5)

        def update_quality(value):
            self.quality.set(int(float(value)))

        scale = ttk.Scale(quality_frame, from_=1, to=100, variable=self.quality, orient='horizontal',
                          command=update_quality)
        scale.pack(side='left', fill='x', expand=True)

        ttk.Label(quality_frame, textvariable=self.quality, width=4).pack(side='right', padx=5)

        ttk.Button(parent, text="Закодировать", command=self._encode_image).grid(row=4, column=0, columnspan=3, pady=20)

        ttk.Label(parent, text="Ключ:").grid(row=5, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(parent, textvariable=self.encoded_key, width=60).grid(row=5, column=1, padx=5, pady=5)
        ttk.Button(parent, text="Копировать", command=self._copy_key).grid(row=5, column=2, padx=5, pady=5)

        parent.columnconfigure(1, weight=1)

    def _setup_decode_tab(self, parent):
        self._create_file_selector(parent, 0, "Публичное изображение:", self.public_path)

        ttk.Label(parent, text="Ключ:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(parent, textvariable=self.decode_key, width=60).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(parent, text="Вставить", command=self._paste_key).grid(row=1, column=2, padx=5, pady=5)

        ttk.Label(parent, text="Пароль:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(parent, textvariable=self.decode_password, width=30).grid(row=2, column=1, sticky='w', padx=5, pady=5)

        ttk.Button(parent, text="Декодировать", command=self._decode_image).grid(row=3, column=0, columnspan=3, pady=20)

        preview_frame = ttk.LabelFrame(parent, text="Предпросмотр")
        preview_frame.grid(row=4, column=0, columnspan=3, sticky='nsew', padx=5, pady=5)

        self.preview_label = ttk.Label(preview_frame, text="Нажмите 'Декодировать' для предпросмотра")
        self.preview_label.pack(pady=20)

        self.save_button = ttk.Button(parent, text="Сохранить", command=self._save_image, state='disabled')
        self.save_button.grid(row=5, column=0, columnspan=3, pady=10)

        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(4, weight=1)

    @staticmethod
    def _create_file_selector(parent, row, label_text, variable):
        ttk.Label(parent, text=label_text).grid(row=row, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(parent, textvariable=variable, width=60).grid(row=row, column=1, padx=5, pady=5)
        ttk.Button(parent, text="Обзор", command=lambda: Steganography._browse_file(variable)).grid(row=row, column=2, padx=5, pady=5)

    @staticmethod
    def _browse_file(variable):
        file_path = filedialog.askopenfilename(title="Выберите изображение", filetypes=[("Изображения", "*.jpg *.jpeg *.png *.bmp *.tiff"), ("Все файлы", "*.*")])
        if file_path:
            variable.set(file_path)

    def _paste_key(self):
        try:
            self.decode_key.set(self.root.clipboard_get())
        except tk.TclError:
            messagebox.showerror("Ошибка", "Не удалось вставить из буфера обмена")

    def _copy_key(self):
        key = self.encoded_key.get()
        if key:
            self.root.clipboard_clear()
            self.root.clipboard_append(key)
            messagebox.showinfo("Успех", "Ключ скопирован в буфер обмена")
        else:
            messagebox.showwarning("Предупреждение", "Нет ключа для копирования")

    def _encode_image(self):
        if not self.public_path.get() or not self.secret_path.get():
            messagebox.showerror("Ошибка", "Выберите оба изображения")
            return

        try:
            key = encode(self.public_path.get(), self.secret_path.get(),
                        quality=self.quality.get(), password=self.encode_password.get())
            self.encoded_key.set(key)
            messagebox.showinfo("Успех", "Изображение закодировано")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _decode_image(self):
        if not self.public_path.get() or not self.decode_key.get():
            messagebox.showerror("Ошибка", "Выберите публичное изображение и введите ключ")
            return

        if not os.path.exists(self.public_path.get()):
            messagebox.showerror("Ошибка", f"Файл не найден: {self.public_path.get()}")
            return

        thread = threading.Thread(target=self._decode_worker, daemon=True)
        thread.start()

    def _decode_worker(self):
        try:
            self.decoded_image = decode(
                self.public_path.get(),
                self.decode_key.get(),
                password=self.decode_password.get()
            )
            self.root.after(0, self._show_preview)

        except Exception as e:
            self._show_error(f"Декодирование не удалось:\n{e}")

    def _show_error(self, message):
        self.root.after(0, lambda: messagebox.showerror("Ошибка", message))

    def _show_preview(self):
        if self.decoded_image is None:
            return

        img_rgb = cv2.cvtColor(self.decoded_image, cv2.COLOR_BGR2RGB)
        img_resized = self._resize_for_preview(img_rgb)
        img_bytes = cv2.imencode('.png', cv2.cvtColor(img_resized, cv2.COLOR_RGB2BGR))[1].tobytes()

        img = Image.open(io.BytesIO(img_bytes))
        self._preview_photo = ImageTk.PhotoImage(img)

        self.preview_label.config(image=self._preview_photo, text="")
        self.save_button.config(state='normal')

    def _resize_for_preview(self, img):
        h, w = img.shape[:2]
        if h <= self.MAX_PREVIEW_SIZE and w <= self.MAX_PREVIEW_SIZE:
            return img

        scale = self.MAX_PREVIEW_SIZE / max(h, w)
        new_w = int(w * scale)
        new_h = int(h * scale)
        return cv2.resize(img, (new_w, new_h))

    def _save_image(self):
        if self.decoded_image is None:
            return

        file_path = filedialog.asksaveasfilename(title="Сохранить изображение", defaultextension=".png", filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("Все файлы", "*.*")])
        if file_path:
            cv2.imwrite(file_path, self.decoded_image)
            messagebox.showinfo("Успех", f"Изображение сохранено: {file_path}")

def main():
    root = tk.Tk()
    Steganography(root)
    root.mainloop()

main()