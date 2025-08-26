
import customtkinter
import os
import random
import subprocess
import configparser
from tkinter import filedialog

class FolderSelectWindow(customtkinter.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.master = master

        self.title("Select Folders")
        self.geometry("800x500")
        self.transient(master)
        self.grab_set()

        self.grid_columnconfigure(1, weight=1) # Path label column expands

        self.path_labels = []
        for i in range(10):
            row_frame = customtkinter.CTkFrame(self, width=600)
            row_frame.grid(row=i)

            # 1. Number Label
            num_label = customtkinter.CTkLabel(row_frame, width=25, text=f"{i+1}")
            num_label.grid(row=i, column=0, padx=(10,5), pady=5)

            # 2. Path Display Label
            path_label_frame = customtkinter.CTkFrame(row_frame, height=20)
            path_label_frame.grid(row=i, column=1, padx=5, pady=5, sticky="ew")
            path_label = customtkinter.CTkLabel(path_label_frame, width=500, text="", anchor="w")
            path_label.grid(sticky="nsew")
            self.path_labels.append(path_label)

            # 3. Browse Button
            browse_button = customtkinter.CTkButton(row_frame, text="Browse...", width=100, 
                                                  command=lambda i=i: self.browse_for_row(i))
            browse_button.grid(row=i, column=2, padx=5, pady=5)

            # 4. Delete Button
            delete_button = customtkinter.CTkButton(row_frame, text="Clear", width=70,
                                                  command=lambda i=i: self.clear_row(i))
            delete_button.grid(row=i, column=3, padx=(5,10), pady=5)

        # Populate initial data from master list
        for i, folder in enumerate(self.master.selected_folders):
            if i < 10:
                self.path_labels[i].configure(text=folder)

        # --- Bottom Buttons ---
        self.button_frame = customtkinter.CTkFrame(self)
        self.button_frame.grid(row=10, pady=20)

        self.confirm_button = customtkinter.CTkButton(self.button_frame, text="Confirm", command=self.confirm_selection)
        self.confirm_button.pack(side="left", padx=10)

        self.cancel_button = customtkinter.CTkButton(self.button_frame, text="Cancel", command=self.destroy)
        self.cancel_button.pack(side="left", padx=10)

    def browse_for_row(self, row_index):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.path_labels[row_index].configure(text=folder_path)

    def clear_row(self, row_index):
        self.path_labels[row_index].configure(text="")

    def confirm_selection(self):
        folder_paths = [label.cget("text") for label in self.path_labels]
        self.master.selected_folders = [path.strip() for path in folder_paths if path.strip()]
        self.master.update_folder_display()
        self.master.save_settings() # Also save folders on confirm
        self.destroy()

class OptionsWindow(customtkinter.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.master = master

        self.title("Filter Options")
        self.geometry("500x400")
        self.transient(master)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)

        self.blacklist_label = customtkinter.CTkLabel(self, text="Blacklist (comma-separated extensions):")
        self.blacklist_label.grid(row=0, column=0, padx=10, pady=(10,0), sticky="w")
        self.blacklist_textbox = customtkinter.CTkTextbox(self, height=120)
        self.blacklist_textbox.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.blacklist_textbox.insert("1.0", self.master.blacklist_str)

        self.whitelist_label = customtkinter.CTkLabel(self, text="Whitelist (comma-separated extensions):")
        self.whitelist_label.grid(row=2, column=0, padx=10, pady=(10,0), sticky="w")
        self.whitelist_textbox = customtkinter.CTkTextbox(self, height=120)
        self.whitelist_textbox.grid(row=3, column=0, padx=10, pady=10, sticky="nsew")
        self.whitelist_textbox.insert("1.0", self.master.whitelist_str)

        self.button_frame = customtkinter.CTkFrame(self)
        self.button_frame.grid(row=4, column=0, pady=10)

        self.save_button = customtkinter.CTkButton(self.button_frame, text="Save and Close", command=self.save_and_close)
        self.save_button.pack(side="left", padx=10)

        self.cancel_button = customtkinter.CTkButton(self.button_frame, text="Cancel", command=self.destroy)
        self.cancel_button.pack(side="left", padx=10)

    def save_and_close(self):
        blacklist_text = self.blacklist_textbox.get("1.0", "end-1c")
        whitelist_text = self.whitelist_textbox.get("1.0", "end-1c")
        self.master.blacklist_str = ','.join(filter(None, (ext.strip() for ext in blacklist_text.replace('\n', ',').split(','))))
        self.master.whitelist_str = ','.join(filter(None, (ext.strip() for ext in whitelist_text.replace('\n', ',').split(','))))
        self.master.save_settings()
        self.destroy()

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("Random File Selector")
        self.geometry("700x320")

        self.config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini')

        self.current_file_path = None
        self.selected_folders = []
        self.blacklist_str = ""
        self.whitelist_str = ""
        self.options_window = None
        self.folder_select_window = None

        self.TEXT_COLOR = ("#000000", "#FFFFFF")
        self.ERROR_COLOR = ("#D2042D", "#FF474C")
        self.WARNING_COLOR = ("#E49B0F", "#F9A602")
        self.BORDER_COLOR = ("#808080", "#505050")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        self.folder_frame = customtkinter.CTkFrame(self)
        self.folder_frame.grid(row=0, column=0, padx=10, pady=(10,5), sticky="ew")
        self.folder_frame.grid_columnconfigure(0, weight=1)

        self.selected_folders_label = customtkinter.CTkLabel(self.folder_frame, text="Selected Folders:", font=customtkinter.CTkFont(weight="bold"))
        self.selected_folders_label.grid(row=0, column=0, padx=10, pady=(5,0), sticky="w")
        self.folders_display_label = customtkinter.CTkLabel(self.folder_frame, text="No folders selected.", anchor="w", justify="left")
        self.folders_display_label.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        self.select_folders_button = customtkinter.CTkButton(self.folder_frame, text="Select Folder(s)...", command=self.open_folder_select_window)
        self.select_folders_button.grid(row=0, column=1, rowspan=2, padx=10, pady=10)

        self.main_button_frame = customtkinter.CTkFrame(self)
        self.main_button_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.main_button_frame.grid_columnconfigure(0, weight=1)

        self.find_button = customtkinter.CTkButton(self.main_button_frame, text="Find Random File", command=self.find_random_file)
        self.find_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        self.options_button = customtkinter.CTkButton(self.main_button_frame, text="Options", width=80, command=self.open_options_window)
        self.options_button.grid(row=0, column=1, padx=(5, 0))

        self.result_title_label = customtkinter.CTkLabel(self, text="Selected File", font=customtkinter.CTkFont(size=15))
        self.result_title_label.grid(row=2, column=0, padx=10, pady=(5,0), sticky="")

        self.result_frame = customtkinter.CTkFrame(self, border_width=2, border_color=self.BORDER_COLOR)
        self.result_frame.grid(row=3, column=0, padx=10, pady=(0,10), sticky="nsew")
        self.result_frame.grid_columnconfigure(0, weight=1)
        self.result_frame.grid_rowconfigure(0, weight=1)

        self.result_label = customtkinter.CTkLabel(self.result_frame, text="File path will appear here",
                                               wraplength=680, justify="left",
                                               text_color=self.TEXT_COLOR)
        self.result_label.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        self.action_frame = customtkinter.CTkFrame(self)
        self.action_frame.grid(row=4, column=0, padx=10, pady=10, sticky="ew")
        self.action_frame.grid_columnconfigure((0, 1), weight=1)

        self.open_button = customtkinter.CTkButton(self.action_frame, text="Open File", command=self.open_file, state="disabled")
        self.open_button.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        self.show_button = customtkinter.CTkButton(self.action_frame, text="Show in Explorer", command=self.show_in_explorer, state="disabled")
        self.show_button.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        self.load_settings() # Moved to after widget creation
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def load_settings(self):
        config = configparser.ConfigParser()
        if os.path.exists(self.config_file):
            config.read(self.config_file)
            self.blacklist_str = config.get('Filters', 'blacklist', fallback='')
            self.whitelist_str = config.get('Filters', 'whitelist', fallback='')
            self.selected_folders = [path.strip() for path in config.get('Folders', 'paths', fallback='').split('\n') if path.strip()]
        self.update_folder_display()

    def save_settings(self):
        config = configparser.ConfigParser()
        config['Filters'] = {
            'blacklist': self.blacklist_str,
            'whitelist': self.whitelist_str
        }
        config['Folders'] = {
            'paths': '\n'.join(self.selected_folders)
        }
        with open(self.config_file, 'w') as f:
            config.write(f)

    def on_closing(self):
        self.save_settings()
        self.destroy()

    def open_folder_select_window(self):
        if self.folder_select_window is None or not self.folder_select_window.winfo_exists():
            self.folder_select_window = FolderSelectWindow(self)
        else:
            self.folder_select_window.focus()

    def update_folder_display(self):
        if not self.selected_folders:
            self.folders_display_label.configure(text="No folders selected.")
        else:
            display_text = "\n".join(self.selected_folders[:3])
            if len(self.selected_folders) > 3:
                display_text += f"\n...and {len(self.selected_folders) - 3} more folder(s)."
            self.folders_display_label.configure(text=display_text)

    def open_options_window(self):
        if self.options_window is None or not self.options_window.winfo_exists():
            self.options_window = OptionsWindow(self)
        else:
            self.options_window.focus()

    def find_random_file(self):
        self.current_file_path = None

        if not self.selected_folders:
            self.result_label.configure(text="Error: No folders selected. Please select one or more folders.", text_color=self.ERROR_COLOR)
            self.update_action_buttons_state()
            return

        blacklist = {('.' + ext.strip().lower()) for ext in self.blacklist_str.split(',') if ext.strip()}
        whitelist = {('.' + ext.strip().lower()) for ext in self.whitelist_str.split(',') if ext.strip()}

        selected_file = None
        eligible_file_count = 0
        try:
            for folder_path in self.selected_folders:
                if not os.path.isdir(folder_path):
                    continue

                for root, _, files in os.walk(folder_path):
                    for file in files:
                        file_ext = os.path.splitext(file)[1].lower()

                        if file_ext in blacklist:
                            continue
                        if whitelist and file_ext not in whitelist:
                            continue
                        
                        eligible_file_count += 1
                        if random.randint(1, eligible_file_count) == 1:
                            selected_file = os.path.join(root, file)

        except Exception as e:
            self.result_label.configure(text=f"An error occurred: {e}", text_color=self.ERROR_COLOR)
            self.update_action_buttons_state()
            return

        if selected_file:
            self.current_file_path = selected_file
            self.result_label.configure(text=self.current_file_path, text_color=self.TEXT_COLOR)
        else:
            self.result_label.configure(text="No eligible files found in the selected folders with the current filters.", text_color=self.WARNING_COLOR)
        
        self.update_action_buttons_state()

    def update_action_buttons_state(self):
        state = "normal" if self.current_file_path else "disabled"
        self.open_button.configure(state=state)
        self.show_button.configure(state=state)

    def open_file(self):
        if self.current_file_path:
            os.startfile(self.current_file_path)

    def show_in_explorer(self):
        if self.current_file_path:
            path = os.path.abspath(self.current_file_path)
            path = path.replace('/', '\\')
            subprocess.Popen(r'explorer /select,"'+path+'"', shell=True)

if __name__ == "__main__":
    customtkinter.set_appearance_mode("System")
    customtkinter.set_default_color_theme("blue")
    
    app = App()
    app.mainloop()
