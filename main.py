
import customtkinter
import os
import random
import subprocess
import configparser
from tkinter import filedialog

class OptionsWindow(customtkinter.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.master = master

        self.title("Filter Options")
        self.geometry("500x400") # Adjusted window height
        self.transient(master)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)

        # Blacklist
        self.blacklist_label = customtkinter.CTkLabel(self, text="Blacklist (comma-separated extensions):")
        self.blacklist_label.grid(row=0, column=0, padx=10, pady=(10,0), sticky="w")
        self.blacklist_textbox = customtkinter.CTkTextbox(self, height=120) # Set fixed height
        self.blacklist_textbox.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.blacklist_textbox.insert("1.0", self.master.blacklist_str)

        # Whitelist
        self.whitelist_label = customtkinter.CTkLabel(self, text="Whitelist (comma-separated extensions):")
        self.whitelist_label.grid(row=2, column=0, padx=10, pady=(10,0), sticky="w")
        self.whitelist_textbox = customtkinter.CTkTextbox(self, height=120) # Set fixed height
        self.whitelist_textbox.grid(row=3, column=0, padx=10, pady=10, sticky="nsew")
        self.whitelist_textbox.insert("1.0", self.master.whitelist_str)

        # Action Buttons
        self.button_frame = customtkinter.CTkFrame(self)
        self.button_frame.grid(row=4, column=0, pady=10)

        self.save_button = customtkinter.CTkButton(self.button_frame, text="Save and Close", command=self.save_and_close)
        self.save_button.pack(side="left", padx=10)

        self.cancel_button = customtkinter.CTkButton(self.button_frame, text="Cancel", command=self.destroy)
        self.cancel_button.pack(side="left", padx=10)

    def save_and_close(self):
        # Get text directly, newlines are no longer processed
        blacklist_text = self.blacklist_textbox.get("1.0", "end-1c")
        whitelist_text = self.whitelist_textbox.get("1.0", "end-1c")

        # Clean up text by removing newlines and ensuring single comma separation
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
        self.blacklist_str = ""
        self.whitelist_str = ""
        self.options_window = None
        self.load_settings()

        self.TEXT_COLOR = ("#000000", "#FFFFFF")
        self.ERROR_COLOR = ("#D2042D", "#FF474C")
        self.WARNING_COLOR = ("#E49B0F", "#F9A602")
        self.BORDER_COLOR = ("#808080", "#505050")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        self.input_frame = customtkinter.CTkFrame(self)
        self.input_frame.grid(row=0, column=0, padx=10, pady=(10,5), sticky="ew")
        self.input_frame.grid_columnconfigure(1, weight=1)

        self.folder_label = customtkinter.CTkLabel(self.input_frame, text="Folder:")
        self.folder_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.folder_entry = customtkinter.CTkEntry(self.input_frame, placeholder_text="Select a folder to search")
        self.folder_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.browse_button = customtkinter.CTkButton(self.input_frame, text="Browse...", command=self.browse_folder)
        self.browse_button.grid(row=0, column=2, padx=10, pady=10)

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
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def load_settings(self):
        config = configparser.ConfigParser()
        if os.path.exists(self.config_file):
            config.read(self.config_file)
            self.blacklist_str = config.get('Filters', 'blacklist', fallback='')
            self.whitelist_str = config.get('Filters', 'whitelist', fallback='')

    def save_settings(self):
        config = configparser.ConfigParser()
        config['Filters'] = {
            'blacklist': self.blacklist_str,
            'whitelist': self.whitelist_str
        }
        with open(self.config_file, 'w') as f:
            config.write(f)

    def on_closing(self):
        self.save_settings()
        self.destroy()

    def open_options_window(self):
        if self.options_window is None or not self.options_window.winfo_exists():
            self.options_window = OptionsWindow(self)
        else:
            self.options_window.focus()

    def browse_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.folder_entry.delete(0, "end")
            self.folder_entry.insert(0, folder_path)

    def find_random_file(self):
        folder_path = self.folder_entry.get()
        self.current_file_path = None

        if not os.path.isdir(folder_path):
            self.result_label.configure(text="Error: Invalid folder path.", text_color=self.ERROR_COLOR)
            self.update_action_buttons_state()
            return

        blacklist = {('.' + ext.strip().lower()) for ext in self.blacklist_str.split(',') if ext.strip()}
        whitelist = {('.' + ext.strip().lower()) for ext in self.whitelist_str.split(',') if ext.strip()}

        selected_file = None
        eligible_file_count = 0
        try:
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
            self.result_label.configure(text="No eligible files found with the current filters.", text_color=self.WARNING_COLOR)
        
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
