import csv, struct, traceback
from tkinter import (
    filedialog, 
    messagebox,
    Tk,
    Button,
    IntVar,
    Label,
    Checkbutton
)
from pathlib import Path
from .chant import Chant
from utils import *

class App(Tk):
    app_name = "PES4/WE8i Chants Tool"
    w = 400 # width for the Tk root
    h = 200 # height for the Tk root

    def __init__(self):
        super().__init__()
        self.title(self.app_name)
        # get screen width and height
        ws = self.winfo_screenwidth() # width of the screen
        hs = self.winfo_screenheight() # height of the screen
        # calculate x and y coordinates for the Tk root window
        x = (ws/2) - (self.w/2)
        y = (hs/2) - (self.h/2)
        # set the dimensions of the screen 
        # and where it is placed
        self.iconbitmap(default=resource_path("resources/pes_indie.ico"))
        self.geometry('%dx%d+%d+%d' % (self.w, self.h, x, y))
        self.filename = ""
        self.my_btn_0 = Button(self, text = "Select your Executable", command = self.__search_exe)
        self.my_btn_1 = Button(self, text = "Create chants map", command = self.create_map)
        self.my_btn_2 = Button(self, text = "Import chants map", command = self.import_map)
        self.backup_check = IntVar()
        self.checkbox_backup = Checkbutton(self, text = "Make backup of PES4/WE8i.exe", variable = self.backup_check)
        self.my_label = Label(self)
    
    def run(self):
        self.my_btn_0.place(relx = 0.5, rely = 0.5, anchor = "center")
        self.my_btn_1.place(x = 220, y = 150)
        self.my_btn_2.place(x = 70, y = 150)
        self.checkbox_backup.place(x = 60, y = 120)
        self.my_label.place(x = 0, y = 180)

        self.resizable(False, False)
        self.mainloop()
        
    def __search_exe(self):
        filename = filedialog.askopenfilename(
            initialdir = ".",
            title = "Select your Executable", 
            filetypes = [
                (
                    "PES4/WE8i Executable", 
                    "*.exe"
                )
            ]
        )
        if not filename: return
        self.filename = filename
        self.my_label.configure(text = self.filename)
        self.__set_game_variables()

    def __set_game_variables(self):
        size = Path(self.filename).stat().st_size
        with open(self.filename, "rb") as f:
            f.seek(60)
            idx = struct.unpack("<I", f.read(4))[0]

        if size == 8503296:
            # PES4 1.00 PC
            self.chants_address = 6098048
            self.total_teams = 206
            self.teams_names_address = 6114048
            self.base_address = 0x400000
        elif size == 8511488 and idx == 2320:
            # PES4 1.10 PC
            self.chants_address = 6102192
            self.total_teams = 206
            self.teams_names_address = 6118200
            self.base_address = 0x400000
        elif size == 8511488 and idx == 140:
            # WE8 PC
            self.chants_address = 6106288
            self.total_teams = 206
            self.teams_names_address = 6121584
            self.base_address = 0x400000
        else:
            raise Exception("Unsupported game")

    def make_backup(self):
        try:
            with open(self.filename, "rb") as f:
                file_contents = f.read()
            backup_file_path = "%s.bak" % (Path(self.filename).stem)
            with open(backup_file_path, "wb") as f:
                f.write(file_contents)
            return True
        except Exception as e:
            print("ERROR while creating backup %r" % (e))
            return False

    def get_name_from_id(self, team_id:int):

        name_offset = struct.unpack("<I", read_data(self.filename, self.teams_names_address + 4 + (team_id * 20), 4))[0] - self.base_address
        name = b''

        grabed_data = read_data(self.filename, name_offset, 1)
        while grabed_data != b'\x00':
            name_offset += 1
            name += grabed_data
            grabed_data = read_data(self.filename, name_offset, 1)

        return name.decode('utf-8')

    def create_map(self):
        if not self.filename:
            self.warning_message("Please first select a PES4/WE8i executable")
            return
        try:
            chants_list = []
            for team_id in range (self.total_teams):
                team_chants_bytes = read_data(self.filename, self.chants_address + (team_id * 4), 4)
                file_id, afs_id = struct.unpack("<2H", team_chants_bytes)
                chant = Chant(team_id, file_id, afs_id)
                chants_list.append(chant)

            csv_file_path = "%s_chants_map.csv" % (Path(self.filename).stem)
            csv_data = [
                [
                    chant.team_id,
                    chant.file_id,
                    chant.afs_name,
                    self.get_name_from_id(chant.team_id),
                ]
                for chant in chants_list
            ]
            with open(csv_file_path, "w", newline = "", encoding = "utf-8") as f:
                csv_writer = csv.writer(f)
                csv_writer.writerow(CSV_HEADERS)
                csv_writer.writerows(csv_data)
            self.info_message("Map created successfully")
        except Exception as e:
            self.error_message("Error while creatinng the map\n%r" % (e))

    def import_map(self):
        if not self.filename:
            self.warning_message("Please first select a PES4/WE8i executable")
            return
        csv_file_selected=filedialog.askopenfilename(
            initialdir = ".",
            title = "Select a CSV file", 
            filetypes = [
                (
                    "CSV file", 
                    "*.csv"
                )
            ]
        )
        if not csv_file_selected: return
        chants_list = []
        try:
            if self.backup_check.get() and not self.make_backup():
                self.error_message("An error has ocurred while creating backup file the map was not imported")
                return
            with open(csv_file_selected, "r", newline = "") as csvfile:
                csv_rows = csv.reader(csvfile)
                for i, row in enumerate(csv_rows):
                    try:
                        if not i: continue
                        team_id, file_number, afs_name, *_ = row
                        team_id = int(team_id)
                        file_number = int(file_number)
                        afs_id = AFS_FILENAMES.index(afs_name)
                        chant = Chant(team_id, file_number, afs_id)
                        chants_list.append(chant)
                    except Exception as e:
                        raise Exception("Error on line number %d content:\n%r\nError:%r" % (i, row, e))
        except Exception as e:
            self.error_message("Error while reading map\n%r" % (e))
            return
        try:
            with open(self.filename, "r+b") as f:
                for chant in chants_list:
                    chant_offset = self.chants_address + (chant.team_id * 4)
                    f.seek(chant_offset, 0)
                    f.write(struct.pack("<2H", chant.file_id, chant.afs_id))
            self.info_message("Map imported successfully!")
        except Exception as e:
            self.error_message("Error while importing map:\n%r" % (e))

    def info_message(self, message):
        messagebox.showinfo(
            title = self.app_name, 
            message = message
        )
    
    def error_message(self, message):
        messagebox.showerror(
            title = self.app_name,
            message = message
        )
        
    def warning_message(self, message):
        messagebox.showwarning(
            title = self.app_name, 
            message = message
        )

    def report_callback_exception(self, *args):
        err = traceback.format_exception(*args)
        self.error_message(" ".join(err))
