import secrets
import string
import tkinter as tk
from tkinter import ttk, messagebox
import json
from pathlib import Path
from cryptography.fernet import Fernet 
import base64
import hashlib


def generate_password(length=12, use_lower=True, use_upper=True, use_digits=True, use_special=True):
    characters = ''
    if use_lower:
        characters += string.ascii_lowercase
    if use_upper:
        characters += string.ascii_uppercase
    if use_digits:
        characters += string.digits
    if use_special:
        characters += string.punctuation

    if not characters:
        characters = string.ascii_letters + string.digits + string.punctuation

    password = ''.join(secrets.choice(characters) for _ in range(length))
    return password

def create_gui():
    root = tk.Tk()
    root.title("Passwortgenerator")
    root.geometry("640x480")

    master_password = None
    
    def ask_master_password():
        dialog = tk.Toplevel(root)
        dialog.title("Master-Passwort")
        dialog.geometry("350x120")
        dialog.transient(root)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        frame = ttk.Frame(dialog, padding=15)
        frame.pack()
        
        ttk.Label(frame, text="Master-Passwort:").pack()
        pwd_var = tk.StringVar()
        pwd_entry = ttk.Entry(frame, textvariable=pwd_var, show="*", width=25)
        pwd_entry.pack(pady=5)
        pwd_entry.focus()
        
        result = [None]
        
        def ok_clicked():
            p = pwd_var.get()
            if len(p) < 4:
                messagebox.showerror("Fehler", "Passwort zu kurz (min. 4 Zeichen)")
                return
            result[0] = p
            dialog.destroy()
        
        def cancel_clicked():
            dialog.destroy()
            root.quit()
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="OK", command=ok_clicked).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="Abbrechen", command=cancel_clicked).pack(side=tk.LEFT, padx=3)
        
        pwd_entry.bind("<Return>", lambda e: ok_clicked())
        dialog.protocol("WM_DELETE_WINDOW", cancel_clicked)
        root.wait_window(dialog)
        
        return result[0]
    
    master_password = ask_master_password()
    if not master_password:
        root.destroy()
        return

    main = ttk.Frame(root, padding=12)
    main.grid()

    ttk.Label(main, text="Länge:").grid(column=0, row=0, sticky="w")
    length_var = tk.IntVar(value=12)
    length_spin = ttk.Spinbox(main, from_=4, to=128, textvariable=length_var, width=6)
    length_spin.grid(column=1, row=0, sticky="w")

    use_lower = tk.BooleanVar(value=True)
    use_upper = tk.BooleanVar(value=True)
    use_digits = tk.BooleanVar(value=True)
    use_special = tk.BooleanVar(value=True)

    ttk.Checkbutton(main, text="Kleinbuchstaben", variable=use_lower).grid(column=0, row=1, sticky="w")
    ttk.Checkbutton(main, text="Großbuchstaben", variable=use_upper).grid(column=1, row=1, sticky="w")
    ttk.Checkbutton(main, text="Ziffern", variable=use_digits).grid(column=0, row=2, sticky="w")
    ttk.Checkbutton(main, text="Sonderzeichen", variable=use_special).grid(column=1, row=2, sticky="w")

    ttk.Label(main, text="Generiertes Passwort:").grid(column=0, row=3, sticky="w", pady=(8, 0))
    password_var = tk.StringVar()
    password_entry = ttk.Entry(main, textvariable=password_var, width=40)
    password_entry.grid(column=0, row=4, columnspan=2, sticky="w")

    def on_generate():
        try:
            length = int(length_var.get())
        except Exception:
            messagebox.showerror("Ungültige Länge", "Bitte geben Sie eine gültige Zahl für die Länge ein.")
            return

        pwd = generate_password(length,
                                use_lower=use_lower.get(),
                                use_upper=use_upper.get(),
                                use_digits=use_digits.get(),
                                use_special=use_special.get())
        password_var.set(pwd)

    def copy_to_clipboard():
        pwd = password_var.get()
        if not pwd:
            return
        root.clipboard_clear()
        root.clipboard_append(pwd)
        root.update()
        messagebox.showinfo("Kopiert", "Passwort in die Zwischenablage kopiert.")

    gen_btn = ttk.Button(main, text="Generieren", command=on_generate)
    gen_btn.grid(column=0, row=5, pady=(8, 0), sticky="w")

    copy_btn = ttk.Button(main, text="Kopieren", command=copy_to_clipboard)
    copy_btn.grid(column=1, row=5, pady=(8, 0), sticky="e")

    
    bookmarks_file = Path.cwd() / "bookmarks.json"
    
    key_hash = hashlib.sha256(master_password.encode()).digest()
    encryption_key = base64.urlsafe_b64encode(key_hash)
    
    try:
        if bookmarks_file.exists():
            with bookmarks_file.open("rb") as f:
                encrypted_data = f.read()
            cipher = Fernet(encryption_key)
            decrypted_data = cipher.decrypt(encrypted_data)
            bookmarks = json.loads(decrypted_data.decode())
        else:
            bookmarks = []
    except Exception:
        bookmarks = []

    def persist_bookmarks():
        try:
            json_text = json.dumps(bookmarks, ensure_ascii=False, indent=2)
            cipher = Fernet(encryption_key)
            encrypted_data = cipher.encrypt(json_text.encode())
            with bookmarks_file.open("wb") as f:
                f.write(encrypted_data)
        except Exception:
            messagebox.showwarning("Speichern fehlgeschlagen", "Lesezeichen konnten nicht gespeichert werden.")

    ttk.Separator(main, orient="horizontal").grid(column=0, row=6, columnspan=2, sticky="ew", pady=(8, 8))
    ttk.Label(main, text="Lesezeichen:").grid(column=0, row=7, sticky="w")

    ttk.Label(main, text="Titel:").grid(column=0, row=8, sticky="w")
    title_var = tk.StringVar()
    title_entry = ttk.Entry(main, textvariable=title_var, width=24)
    title_entry.grid(column=1, row=8, sticky="w")

    def refresh_bookmarks_list():
        listbox.delete(0, tk.END)
        for bm in bookmarks:
            listbox.insert(tk.END, bm.get("title", "(untitled)"))

    def add_bookmark():
        title = title_var.get().strip()
        pwd = password_var.get()
        if not title:
            messagebox.showerror("Fehlender Titel", "Bitte geben Sie einen Titel für das Lesezeichen ein.")
            return
        if not pwd:
            messagebox.showerror("Kein Passwort", "Kein Passwort zum Speichern. Zuerst eins erzeugen.")
            return
        bookmarks.append({"title": title, "password": pwd})
        persist_bookmarks()
        refresh_bookmarks_list()
        title_var.set("")

    def delete_bookmark():
        sel = listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        del bookmarks[idx]
        persist_bookmarks()
        refresh_bookmarks_list()

    def copy_bookmark():
        sel = listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        bm = bookmarks[idx]
        root.clipboard_clear()
        root.clipboard_append(bm.get("password", ""))
        root.update()
        messagebox.showinfo("Kopiert", "Lesezeichen-Passwort in die Zwischenablage kopiert.")

    add_btn = ttk.Button(main, text="Lesezeichen speichern", command=add_bookmark)
    add_btn.grid(column=0, row=9, sticky="w", pady=(6, 0))

    listbox = tk.Listbox(main, height=6, width=40)
    listbox.grid(column=0, row=10, columnspan=2, sticky="w")

    btn_frame = ttk.Frame(main)
    btn_frame.grid(column=0, row=11, columnspan=2, sticky="w", pady=(6, 0))
    ttk.Button(btn_frame, text="Kopieren", command=copy_bookmark).grid(column=0, row=0, padx=(0, 6))
    ttk.Button(btn_frame, text="Löschen", command=delete_bookmark).grid(column=1, row=0)

    refresh_bookmarks_list()

    on_generate()

    root.mainloop()


if __name__ == "__main__":
    create_gui()
