import tkinter as tk
from tkinter import filedialog, messagebox
import os
from PIL import Image, ImageTk
import imagehash
import ctypes

# set taskbar icon for windows
myappid = 'deja.view.photo.deduper'
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

# function to center window on screen
def center_window(window):
    window.update_idletasks()
    w = window.winfo_width()
    h = window.winfo_height()
    x = (window.winfo_screenwidth() // 2) - (w // 2)
    y = (window.winfo_screenheight() // 2) - (h // 2)
    window.geometry(f"{w}x{h}+{x}+{y}")

# main app window
root = tk.Tk()
root.title("Déjà View - Photo Deduper")
root.iconbitmap("icon.ico")
root.geometry("500x250")
center_window(root)

# button hover effects
def on_enter(e): e.widget['background'] = '#d0d0d0'
def on_leave(e): e.widget['background'] = 'SystemButtonFace'

# holds selected folder path
selected_folder = tk.StringVar(value="No folder selected")

# function to open folder picker dialog
def select_folder():
    folder = filedialog.askdirectory()
    if folder:
        selected_folder.set(folder)
        find_btn.config(state="normal")

# list to hold duplicate pairs (dupe, original)
duplicates = []

# resize and pad images without distortion
def resize_and_pad(image, size=(500, 500), color=(240, 240, 240)):
    image.thumbnail(size, Image.Resampling.LANCZOS)
    new_img = Image.new("RGBA", size, color + (255,))
    left = (size[0] - image.width) // 2
    top = (size[1] - image.height) // 2
    new_img.paste(image, (left, top))
    return new_img

# function to find duplicates
def find_duplicates():
    folder = selected_folder.get()
    if not folder:
        return

    # update button text
    find_btn.config(text="Finding Duplicates...", state="disabled")
    root.update_idletasks()
    
    # supported image extensions
    supported_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.tif', '.webp', '.heic')

    # maps hash (key) to file path (value)
    seen_hashes = {}

    # reset any previos results
    duplicates.clear()

    for root_dir, _, files in os.walk(folder):
        for file in files:
            if file.lower().endswith(supported_extensions):
                path = os.path.join(root_dir, file)
                try:
                    img = Image.open(path)
                    img_hash = imagehash.average_hash(img)
                    img.close()

                    if img_hash in seen_hashes:
                        duplicates.append((path, seen_hashes[img_hash]))
                    else:
                        seen_hashes[img_hash] = path

                except Exception as e:
                    prinnt(f"Error processing {path}: {e}")

    # reset button text
    find_btn.config(text="Find Duplicates", state="normal")
            
    # show results        
    messagebox.showinfo("Done", f"Found {len(duplicates)} duplicate(s).")
    review_duplicates()

# function to review duplicates
def review_duplicates():
    if not duplicates:
        messagebox.showinfo("Done", "No duplicates found to review.")
        return

    # used list to track so we can update in inner functions
    current_index = [0]

    # create new window
    review_window = tk.Toplevel(root)
    review_window.title("Déjà View - Review Duplicates")
    review_window.iconbitmap("icon.ico")
    review_window.geometry("1200x725")
    center_window(review_window)

    # create grid layout
    review_window.columnconfigure(0, weight=1)
    review_window.columnconfigure(1, weight=1)

    # left side (duplicate)
    left_frame = tk.Frame(review_window)
    left_frame.grid(row=0, column=0,  padx=20, pady=20)

    left_path_label = tk.Label(left_frame, text="", wraplength=350, justify="center", font=("Helvetica", 12, "bold"))
    left_path_label.pack(pady=5)

    left_label = tk.Label(left_frame)
    left_label.pack()

    # right side (original)
    right_frame = tk.Frame(review_window)
    right_frame.grid(row=0, column=1, padx=20, pady=20)

    right_path_label = tk.Label(right_frame, text="", wraplength=350, justify="center", font=("Helvetica", 12, "bold"))
    right_path_label.pack(pady=5)

    right_label = tk.Label(right_frame)
    right_label.pack()

    # show current duplicate pair
    def show_current_pair():
        dupe_path, original_path = duplicates[current_index[0]]

        # load and resize images
        dupe_img = resize_and_pad(Image.open(dupe_path).convert("RGBA"))
        original_img = resize_and_pad(Image.open(original_path).convert("RGBA"))

        dupe_photo = ImageTk.PhotoImage(dupe_img)
        original_photo = ImageTk.PhotoImage(original_img)

        # update labels with file paths
        left_path_label.config(text="Duplicate: " + dupe_path)
        right_path_label.config(text="Original: " + original_path)

        # keep reference to avoid garbage collection
        left_label.image = dupe_photo
        right_label.image = original_photo

        left_label.config(image=dupe_photo)
        right_label.config(image=original_photo)

    # delete photo (either dupe or original)
    def delete_photo(photo_to_delete):
        dupe_path, original_path = duplicates[current_index[0]]
        path_to_delete = dupe_path if photo_to_delete == "duplicate" else original_path
        try:
            os.remove(path_to_delete)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete {path_to_delete}: {e}")
        go_next()

    # skip to next
    def go_next():
        current_index[0] += 1
        if current_index[0] >= len(duplicates):
            messagebox.showinfo("Done", "No more duplicates to review.")
            review_window.destroy()
        else:
            show_current_pair()

    # frame to hold action buttons
    button_frame = tk.Frame(review_window)
    button_frame.grid(row=1, column=0, columnspan=2, pady=10)

    # delete duplicate button
    delete_duplicate_btn = tk.Button(button_frame, text="Delete Duplicate", font=("Helvetica", 12, "bold"), command=lambda: delete_photo("duplicate"))
    delete_duplicate_btn.pack(side="left", padx=20)
    delete_duplicate_btn.bind("<Enter>", on_enter)
    delete_duplicate_btn.bind("<Leave>", on_leave)

    # delete original button
    delete_original_btn = tk.Button(button_frame, text="Delete Original", font=("Helvetica", 12, "bold"), command=lambda: delete_photo("original"))
    delete_original_btn.pack(side="left", padx=20)
    delete_original_btn.bind("<Enter>", on_enter)
    delete_original_btn.bind("<Leave>", on_leave)

    # skip button
    skip_btn = tk.Button(button_frame, text="Skip", font=("Helvetica", 12, "bold"), command=go_next)
    skip_btn.pack(side="left", padx=20)
    skip_btn.bind("<Enter>", on_enter)
    skip_btn.bind("<Leave>", on_leave)

    # show first pair
    show_current_pair()

# app title
title_label = tk.Label(root, text="Déjà View - Photo Deduper", font=("Helvetica", 16, "bold"))
title_label.pack(pady=(20, 10))

# select folder button
select_btn = tk.Button(root, text="Select Photos Folder", font=("Helvetica", 12, "bold"), padx=20, pady=10, width=15, command=select_folder)
select_btn.pack(pady=10)
select_btn.bind("<Enter>", on_enter)
select_btn.bind("<Leave>", on_leave)

# label to display selected folder
folder_label = tk.Label(root, textvariable=selected_folder, wraplength=400, justify="center", font=("Segoe UI", 10, "italic"), bg="#f0f0f0", relief="groove", bd=1, fg="gray")
folder_label.pack(pady=10)

# find duplicates button
find_btn = tk.Button(root, text="Find Duplicates", state="disabled", font=("Helvetica", 12, "bold"), padx=20, pady=10, width=15, command=find_duplicates)
find_btn.pack(pady=10)
find_btn.bind("<Enter>", on_enter)
find_btn.bind("<Leave>", on_leave)

# start gui loop
root.mainloop()