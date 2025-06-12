import os
import subprocess
import time
import ctypes 
from tkinter import *
from threading import *
import sys
import pystray #type:ignore
from pystray import MenuItem as item #type:ignore
from threading import Thread
from PIL import Image, ImageTk #type:ignore
import psutil #type:ignore

# Timer Class handles start end and duration of timer on the seperate thread
class Timer:

    # Variables
    def __init__(self):
        self.processRunning = False
        self.remainingTime = 0
        self.timerRunning = False
        self.timerPaused = False
        self.timerStarted = False
        self.sessionLength = 25  # default session length in minutes
        self.processName = ""
        self.shouldSnooze = True
        self.snoozeLength = 2 # default snooze length in minutes
    
    # Creates a pop-up window with "title" "text" "style" -
    #  style: 0= ok,1= ok cancel ,2= abort retry ignore, 3= yes no cancel ,4= yes no ,5= retry cancel ,6= cancel try_again continue
    def Mbox(self,title, text, style):
        return ctypes.windll.user32.MessageBoxW(0, text, title, style)
    
    # Returns a list of every process currently running
    def get_process_names(self):
        try:
            return [proc.name() for proc in psutil.process_iter(['name'])]
        except Exception as e:
            print(e)
            return []

    # Timer Snooze sleeps for snooze length then recheck and alert if needed if not then stop the timer thread
    def snooze(self):
        time.sleep(self.snoozeLength * 60)  # Wait for 2 minutes before checking again
        if self.get_processes() != None and self.shouldSnooze:
            self.Mbox("Timer", "Still Running! Please Close It!", 0)
            self.snooze()
        else:
            self.timer_ended()
    
    # Stops and reset the timer and closes the thread
    def timer_ended(self):
        self.processRunning = False
        self.timerRunning = False
        self.timerStarted = False
        pause_button.config(text="Start")

    # Returns the currect process via its name if exists else None if multi process return all
    def get_processes(self):
        process = []
        for proc in psutil.process_iter(['name']):
            try:
                if self.processName.lower() in proc.info['name'].lower():
                    process.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if process:
            return process

        return None
    
    # Start Timer handling
    def start_timer(self, minutes=None):

        if self.timerRunning:
            return  # Already running so dont run again

        # minutes verify and set default if not set
        if minutes is None:
            minutes = self.sessionLength
        if minutes < 0:
            return
        if minutes == 0:
            minutes = 0.1

        # set time in seconds and set start vars
        self.remainingTime = int(minutes * 60)
        self.timerRunning = True
        self.timerPaused = False
        self.timerStarted = True

        # alert user of timer start
        units = "Minutes" if minutes >= 1 else "Seconds"
        amount = minutes if minutes >= 1 else int(minutes * 60)
        self.Mbox("Timer", f"Have Fun! You Got {amount} {units}!", 0)
        
        # timer loop
        while self.remainingTime > 0 and self.timerRunning:
            if not self.timerPaused:
                time.sleep(1)
                self.remainingTime -= 1
                clock_label.config(text=f"{self.remainingTime // 60:02}:{self.remainingTime % 60:02}") # update time left label in ui
            else:
                time.sleep(0.2)  # Avoid CPU overuse when paused

        # timer ended
        if self.remainingTime <= 0:
            self.end_timer()

    # End Timer handling
    def end_timer(self):
        # set vars
        self.timerRunning = False
        self.timerStarted = False

        # Check and handle the process closure logic
        # get the process
        process = None
        process = self.get_processes()

        # if process found
        if process:

            # if hard stop is enabled kill the process and alert user
            if hardStop_var.get():
                try:
                    try:
                        for proc in process: proc.kill()
                    except psutil.AccessDenied:
                        self.Mbox("Permission Denied", "Run as administrator to kill this process.", 0)

                    self.Mbox("Timer", f"{process[0].name()} was forcefully closed by Timer.", 0)
                except Exception as e:
                    self.Mbox("Error", f"Error: {e} | Could not close {process[0].name()}.", 0)

            # if snooze is enabled alert user to close and start snooze
            elif snooze_var.get():
                self.Mbox("Timer", "Time's Up! Please Close It!", 0)
                pause_button.config(text="Stop")
                self.snooze()
        
        # set vars and labels
        self.timer_ended()

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

#Function to pause or resume the timer
def pause_resume():
    # first time? apply data incase wasnt applied
    if pause_button['text'] == "Start":
        apply()
    # snooze stop timer
    if pause_button['text'] == "Stop":
        t.shouldSnooze = False
        t.timer_ended()
    # start pause resume handling
    elif good:
        if not t.timerStarted:
            # Timer hasn't started, so start it now
            pause_button.config(text="Pause")
            t.timerStarted = True
            t.timerPaused = False
            Thread(target=t.start_timer, args=(t.sessionLength,), daemon=True).start()

        elif t.timerRunning and not t.timerPaused:
            # Pause the timer
            t.timerPaused = True
            pause_button.config(text="Resume")

        elif t.timerRunning and t.timerPaused:
            # Resume the timer
            t.timerPaused = False
            pause_button.config(text="Pause")
    else:
        t.Mbox("Timer","Invalid Inputs!",0)
        print("Invalid Inputs. Please enter valid inputs.")


def apply():
    global process_name,good
    # reset
    good = False

    # Get and validate process name
    processInput = setProcess_entry.get().strip()
    if not processInput or len(processInput)<3:
        processInput = ""  # No process name entered

    # Get and validate time
    try:
        minutes = int(setTime_entry.get().strip())
        if minutes < 0:
            minutes = -1  # Time must be positive
    except ValueError:
        minutes=-1  # Invalid number

    # Get and validate snooze length
    try:
        snoozeLength = int(setSnoozeTime_entry.get().strip())
        if snoozeLength <= 0:
            snoozeLength = -1  # Time must be positive
    except ValueError:
        snoozeLength=-1  # Invalid number

    # Check if process is running if so set good and get its name
    fullProcessName=""
    for proc in psutil.process_iter(['name']):
        try:
            if processInput.lower() in proc.info['name'].lower():
                fullProcessName = proc.info['name']
                good = True
                break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # Update UI 
    labelText = "Currently Selected: "
    if processInput:
        labelText += processInput if fullProcessName == "" else fullProcessName.split('.')[0] # use entered name if didnt found such process
    if minutes >= 0:
        timeStr = f"({minutes} min)" if minutes > 0 else "(6 sec)" # use minutes enterd or 6 sec if 0 entered (0=0.1*60)
        labelText += f" {timeStr}"
    currentlySelected_label.config(text=labelText) # apply string to label

    # Validate data after proccessing
    if snooze_var.get() and snoozeLength < 1:
        good = False
    if processInput == "" or minutes < 0 :
        good = False
    if fullProcessName == "":
        good = False
    if not good:
        return
    
    # Here on data is valid

    # Save data to timer
    t.processName = fullProcessName # will always be found if good (safe to use)
    t.sessionLength = minutes
    t.snoozeLength = snoozeLength

# Closing function
def on_closing():
    timerRoot.destroy()  # Destroy the Tkinter window
    sys.exit()     # Forcefully kill everything, including background threads

# Debug  function for testing different data or functions using a button
def debug_func():
    processes = subprocess.run(['tasklist'], capture_output=True, text=True, check=True).stdout.strip().splitlines()
    for process in processes:
        print(process.split()[0])

# Hard Stop ticked in UI -> disable snooze
def on_hard_tick():
    if hardStop_var.get():
        snooze_var.set(False)

# Snooze ticked in UI -> disable hard stop
def on_snooze_tick():
    if snooze_var.get():
        hardStop_var.set(False)

# Toggle state of checked when "Enter" is pressed
def toggle_check(var, callback):
    var.set(not var.get())
    callback()  # ensure exclusivity logic runs

# shows the program in the system tray
def show_tray_icon():
    # creates default blue square as app icon for the tray (fallback)
    icon_img = Image.new(mode="RGB",color=(11, 176, 217),size=(64,64))

    # If icon image exist tries to set it
    try:
        icon_img = Image.open(resource_path("icon.png"))   
    except FileNotFoundError:
        print("Tray icon image (icon.png) not found. using fallback color")

    # adds menu options when right clicked
    menu = (
        item("Restore", on_tray_restore),
        item("Exit", on_tray_exit)
    )
    icon = pystray.Icon("Timer", icon_img, "Timer", menu)
    Thread(target=icon.run, daemon=True).start()

# when restoring app from system tray
def on_tray_restore(icon=None, item=None):
    if icon:
        icon.stop()
    timerRoot.after(0, timerRoot.deiconify)

# when exiting the app from system tray
def on_tray_exit(icon=None, item=None):
    icon.stop()
    timerRoot.after(0, on_closing)

# minimize to system tray handling
def handle_minimize(event):
    if timerRoot.state() == 'iconic':
        timerRoot.withdraw()
        show_tray_icon()


debug = False
good = False

process_name = ""
t = Timer()

bg_color = "#afcbd9"


# UI creation
timerRoot = Tk()
timerRoot.title("Timer")
timerRoot.geometry("400x250")
timerRoot.config(bg=bg_color) # fallback bg color
timerRoot.resizable(width=False,height=False) # fixed size

# try to set background image to the app
try:
    image = Image.open(resource_path("Bg.png"))
    resized_image = image.resize((400, 250))  # Resize to fit window
    bg = ImageTk.PhotoImage(resized_image)
    label1 = Label(timerRoot, image = bg)
    label1.place(relx = 0, rely = 0.1,relheight=1,relwidth=1)
except:
    pass

# Checkbox vars
hardStop_var=BooleanVar()
hardStop_var.set(False)
snooze_var=BooleanVar()
snooze_var.set(True)

# create labels
currentlySelected_label = Label(timerRoot,text="",bg=bg_color)
setProcess_label = Label(timerRoot,text="Process Name:",bg=bg_color)
setTime_label = Label(timerRoot,text="Session Length:(minutes)",bg=bg_color)
timeLeft_label = Label(timerRoot,text="Time Left:",bg=bg_color)
clock_label = Label(timerRoot,text="00:00",bg=bg_color)

# create user text entries
setProcess_entry = Entry(timerRoot,width=15)
setTime_entry = Entry(timerRoot,width=6)
# set default values
setProcess_entry.insert(0,"Stardew Valley")
setTime_entry.insert(0,"25")

# crate checkboxs
hardStop_checkbox = Checkbutton(timerRoot,text="Hard Stop?",variable=hardStop_var,command=on_hard_tick,bg=bg_color)
snooze_checkbox = Checkbutton(timerRoot,text="snooze?",variable=snooze_var,command=on_snooze_tick,bg=bg_color)

# snooze
setSnoozeTime_entry = Entry(timerRoot,width=3)
setSnoozeTime_entry.insert(0,"2")

# create buttons
apply_button = Button(timerRoot,text="Apply",command=apply)
pause_button = Button(timerRoot,text="Start",command=pause_resume)

# UI placement using relative X and Y 
currentlySelected_label.place(relx=0.5,rely=0.15,anchor="center")
setTime_label.place(relx=0.6,rely=0.42,anchor="e")
setProcess_label.place(relx=0.465,rely=0.3,anchor="e")
timeLeft_label.place(relx=0.85,rely=0.3,anchor="center")
clock_label.place(relx=0.85,rely=0.38,anchor="center")
setProcess_entry.place(relx=0.465,rely=0.3,anchor="w")
setTime_entry.place(relx=0.6,rely=0.42,anchor="w")
hardStop_checkbox.place(relx=0.5,rely=0.56,anchor="center")
snooze_checkbox.place(relx=0.48,rely=0.66,anchor="center")
setSnoozeTime_entry.place(relx=0.57,rely=0.66,anchor="w")
apply_button.place(relx=0.51,rely=0.8,anchor="w")
pause_button.place(relx=0.49,rely=0.8,anchor="e")

# Binding of UI elements
setTime_entry.bind("<Return>", lambda event: apply())
setProcess_entry.bind("<Return>", lambda event: apply())
hardStop_checkbox.bind("<Return>", lambda event: toggle_check(hardStop_var, on_hard_tick))
snooze_checkbox.bind("<Return>", lambda event: toggle_check(snooze_var, on_snooze_tick))
apply_button.bind("<Return>",lambda event: apply())
pause_button.bind("<Return>",lambda event: pause_resume())
timerRoot.bind("<Unmap>", handle_minimize)

if(debug):
    debug_button = Button(timerRoot,text="debug",command=debug_func)
    debug_button.place(relx=0.9,rely=0.9,anchor="se")

# latch onto closing
timerRoot.protocol("WM_DELETE_WINDOW", on_closing)


myappid = 'python.liron.timer'
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

# set app icon
try:
    timerRoot.iconbitmap(default=resource_path("icon.ico"))
except Exception as e:
    print("Icon not loaded:", e)

apply()

timerRoot.mainloop()