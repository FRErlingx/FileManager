import os
import hashlib
import csv
import shutil
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

def hash_file(file_path):
    """Calculer l'empreinte de hachage SHA256 d'un fichier."""
    try:
        with open(file_path, 'rb') as f:
            sha256 = hashlib.sha256()
            while True:
                data = f.read(65536)  # 64KB à la fois
                if not data:
                    break
                sha256.update(data)
        return sha256.hexdigest()
    except FileNotFoundError:
        print("Le fichier", file_path, "n'a pas été trouvé.")
        return None

def scan_files(directory, progress_var, text_box):
    """Parcourir tous les fichiers d'un répertoire et ses sous-répertoires."""
    file_hashes = {}
    total_files = sum(len(files) for _, _, files in os.walk(directory))
    files_scanned = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            file_hash = hash_file(file_path)
            if file_hash in file_hashes:
                file_hashes[file_hash].append(file_path)
            else:
                file_hashes[file_hash] = [file_path]
            files_scanned += 1
            progress = int(files_scanned / total_files * 100)
            progress_var.set(progress)
            text_box.insert(tk.END, file_path + '\n')
            text_box.see(tk.END)
            text_box.update()
    return file_hashes

def get_creation_date(file_path):
    """Obtenir la date de création d'un fichier."""
    return datetime.fromtimestamp(os.path.getctime(file_path))

def remove_duplicates_to_trash(file_hashes):
    """Supprimer les fichiers doublons."""
    for file_paths in file_hashes.values():
        if len(file_paths) > 1:
            # Créez un dictionnaire pour stocker les chemins des fichiers par date de création
            creation_dates = {}
            for file_path in file_paths:
                creation_date = get_creation_date(file_path)
                creation_dates[file_path] = creation_date

            # Triez les chemins des fichiers par date de création
            sorted_files = sorted(creation_dates.items(), key=lambda x: x[1])  # Tri par date croissante

            # Récupérez le chemin du premier fichier (le plus vieux)
            oldest_file_path = sorted_files[0][0]

            # Supprimez tous les fichiers sauf le premier (le plus vieux)
            for file_path in file_paths:
                if file_path != oldest_file_path:
                    try:
                        os.remove(file_path)  # Supprime le fichier
                    except Exception as e:
                        print(f"Erreur lors de la suppression de {file_path} : {e}")

    messagebox.showinfo("Terminé", "Opération de suppression terminée.")


def move_duplicates_to_folder(file_hashes, duplicates_folder):
    """Déplacer tous les fichiers doublons sauf le plus ancien dans un dossier et enregistrer la liste dans un fichier CSV."""
    if not os.path.exists(duplicates_folder):
        os.makedirs(duplicates_folder)

    # Créer une liste pour stocker les fichiers à déplacer dans le fichier CSV
    duplicates_list = []

    for file_paths in file_hashes.values():
        if len(file_paths) > 1:
            # Créer un dictionnaire pour stocker les chemins des fichiers par date de création
            creation_dates = {}
            for file_path in file_paths:
                creation_date = get_creation_date(file_path)
                creation_dates[file_path] = creation_date

            # Trier les chemins des fichiers par date de création
            sorted_files = sorted(creation_dates.items(), key=lambda x: x[1], reverse=True)  # Tri par date décroissante

            # Récupérer le chemin du premier fichier (le plus ancien)
            oldest_file_path = sorted_files[-1][0]

            # Parcourir chaque fichier et les déplacer vers le dossier des doublons en conservant leur arborescence
            for file_path in file_paths:
                if file_path != oldest_file_path:
                    # Obtenir le chemin relatif par rapport au répertoire de départ
                    relative_path = os.path.relpath(file_path, os.path.dirname(oldest_file_path))

                    # Créer le chemin complet du nouveau fichier dans le dossier des doublons
                    new_file_path = os.path.join(duplicates_folder, relative_path)

                    # Créer le dossier s'il n'existe pas déjà
                    os.makedirs(os.path.dirname(new_file_path), exist_ok=True)

                    # Déplacer le fichier vers le nouveau chemin
                    try:
                        shutil.move(file_path, new_file_path)
                        duplicates_list.append((file_path, new_file_path))
                    except Exception as e:
                        print(f"Erreur lors du déplacement de {file_path} : {e}")

    # Écrire la liste des fichiers déplacés dans un fichier CSV
    with open(os.path.join(duplicates_folder, 'files.csv'), 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['Original File', 'Duplicate File'])
        csv_writer.writerows(duplicates_list)

def main():
    root = tk.Tk()
    root.title("Gestion des fichiers doublons")

    # Création d'un Notebook (onglets)
    notebook = ttk.Notebook(root)
    notebook.pack(expand=True, fill='both')

    # Premier onglet pour le déplacement des fichiers doublons
    frame_move = ttk.Frame(notebook)
    notebook.add(frame_move, text='Déplacement')

    # Widgets pour le premier onglet
    label_directory_move = tk.Label(frame_move, text="Répertoire à scanner:")
    label_directory_move.grid(row=0, column=0, sticky="w")

    entry_directory_move = tk.Entry(frame_move, width=40)
    entry_directory_move.grid(row=0, column=1, padx=5, pady=5)

    button_browse_move = tk.Button(frame_move, text="Parcourir", command=lambda: entry_directory_move.insert(tk.END, filedialog.askdirectory()))
    button_browse_move.grid(row=0, column=2, padx=5, pady=5)

    label_duplicates_move = tk.Label(frame_move, text="Dossier pour les doublons:")
    label_duplicates_move.grid(row=1, column=0, sticky="w")

    entry_duplicates_move = tk.Entry(frame_move, width=40)
    entry_duplicates_move.grid(row=1, column=1, padx=5, pady=5)

    button_browse_duplicates_move = tk.Button(frame_move, text="Parcourir", command=lambda: entry_duplicates_move.insert(tk.END, filedialog.askdirectory()))
    button_browse_duplicates_move.grid(row=1, column=2, padx=5, pady=5)

    progress_var = tk.DoubleVar()
    progress_bar = ttk.Progressbar(frame_move, variable=progress_var, maximum=100)
    progress_bar.grid(row=2, columnspan=3, sticky="ew", padx=5, pady=5)

    text_box = tk.Text(frame_move, wrap=tk.WORD, height=20, width=60)
    text_box.grid(row=3, columnspan=3, padx= 5, pady=5)

    button_process_move = tk.Button(frame_move, text="Déplacer les doublons", command=lambda: process_move(entry_directory_move.get(), entry_duplicates_move.get(), progress_var, text_box))
    button_process_move.grid(row=4, columnspan=3, padx=5, pady=5)

    # Deuxième onglet pour la suppression des fichiers doublons
    frame_remove = ttk.Frame(notebook)
    notebook.add(frame_remove, text='Suppression')

    # Widgets pour le deuxième onglet
    label_directory_remove = tk.Label(frame_remove, text="Répertoire à scanner:")
    label_directory_remove.grid(row=0, column=0, sticky="w")

    entry_directory_remove = tk.Entry(frame_remove, width=40)
    entry_directory_remove.grid(row=0, column=1, padx=5, pady=5)

    button_browse_remove = tk.Button(frame_remove, text="Parcourir", command=lambda: entry_directory_remove.insert(tk.END, filedialog.askdirectory()))
    button_browse_remove.grid(row=0, column=2, padx=5, pady=5)

    button_process_remove = tk.Button(frame_remove, text="Supprimer les doublons", command=lambda: process_remove(entry_directory_remove.get()))
    button_process_remove.grid(row=1, column=1, padx=5, pady=5)

    def process_move(directory, duplicates_folder, progress_var, text_box):
        if not duplicates_folder or not os.path.exists(duplicates_folder):
            messagebox.showerror("Erreur", "Dossier pour les doublons invalide.")
            return

        file_hashes = scan_files(directory, progress_var, text_box)
        move_duplicates_to_folder(file_hashes, duplicates_folder)
        messagebox.showinfo("Terminé", "Opération de déplacement terminée. Consultez le dossier des doublons.")

    def process_remove(directory):
        """Scanner les fichiers et supprimer les doublons."""
        if not directory or not os.path.exists(directory):
            messagebox.showerror("Erreur", "Répertoire invalide.")
            return

        file_hashes = scan_files(directory, None, None)
        remove_duplicates_to_trash(file_hashes)
        messagebox.showinfo("Terminé", "Opération de suppression terminée.")

    root.mainloop()

if __name__ == "__main__":
    main()
