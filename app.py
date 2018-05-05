#!/usr/bin/python

from PIL import Image, ImageTk
import os
import traceback
import tkinter as tk
import tkinter.ttk as ttk
import subprocess

root = None
exception = None
email_listener = None
components = {}


supported_bash_commands = [
    'screen-on',
    'screen-off',
    'update-repo'
]

### HANDLERS ###

def exception_handler(message):

    raise Exception(message.parts[0])

def print_handler(message):

    for arg in message.parts:
        print(arg)

def exit_handler(message):
    
    if root:
        root.attributes('-fullscreen', False)
        root.destroy()
 
    quit()

def restart_handler(message):
   
    if root:
        root.attributes('-fullscreen', False)
        root.quit()

def update_handler(message):

    run_command('update-repo')
    restart_handler(message)

def set_background(message):
   
    message.save_attachments(map_file_to_directory)
   
    path = './pictures/' + message.parts[0]
    image = Image.open(path).resize((screen_width, screen_height), Image.ANTIALIAS)
    image_tk = ImageTk.PhotoImage(image)
    components['background'] = image_tk
    canvas.itemconfig(background_element, image=image_tk)     

def message(message):
 
    canvas.bind("<Button-1>", clear_message)
    set_overlay_opacity(180)
    canvas.itemconfig(overlay_text, text=message.parts[0])

def clear_message(message):

    canvas.unbind("<Button-1>")
    set_overlay_opacity(0)
    canvas.itemconfig(overlay_text, text="")

### HELPER FUNCTIONS ###

def handler_wrapper(handler):
    
    def wrapper(message):
        run_command('screen-on')
        handler(message)
    
    return wrapper

def set_overlay_opacity(value):

    overlay_img = Image.new('RGBA', (screen_width, screen_height), (0,0,0,value))
    overlay_img_tk = ImageTk.PhotoImage(overlay_img)
    components['overlay'] = overlay_img_tk
    canvas.itemconfig(overlay_element, image=overlay_img_tk)

def run_command(command):

    if not command in supported_bash_commands: return
    call_args = ['bash', './scripts/commands.sh', command]
    return_val = subprocess.call(call_args)

    if return_val != 0:
        raise Exception('Error using commands.sh')

def send_message_callback(message):

    def wrapper():
        connection.send_email('harris.octavio@gmail.com', message.upper(), message)

    return wrapper

def map_file_to_directory(filename):

    if filename.endswith('png') or filename.endswith('jpg'):
        return './pictures/'
    
    return './unsorted_attachments/'        

### MAIN APP ###

def run(email_connection, email_listener, settings):

    global connection
    connection = email_connection

    email_listener.set_handler_wrapper(handler_wrapper)

    # Register the handlers for the types of actions
    email_listener.register_handler('background', set_background)
    email_listener.register_handler('message', message)
    email_listener.register_handler('clear_message', clear_message)
    email_listener.register_handler('update', update_handler)
    email_listener.register_handler('restart', restart_handler)
    email_listener.register_handler('exit', exit_handler)
    email_listener.register_handler('print', print_handler)
    email_listener.register_handler('exception', exception_handler)
   
    # Initialize and open the Tkinter window
    global root
    root = tk.Tk()
    root.attributes('-fullscreen', True) 
    style = ttk.Style()

    # Collect screen dimensions
    global screen_width
    global screen_height
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # Function to poll email using Tkinter's after function
    def poll_email():
        
        if not email_listener.running: return

        root.after(int(email_listener.poll_interval * 1000), poll_email)
        
        try:
            print('.')
            email_listener.process_latest_email()
        except Exception as e:
            global exception
            exception = e
            email_listener.stop()
            root.quit()

    # Set the email_listener to running and wake screen
    email_listener.running = True

    # Create components
    global canvas
    global background_element
    global overlay_element
    global overlay_text

    canvas = tk.Canvas(root)#, width=screen_width, height=screen_height)
    canvas.place(relwidth=1.0, relheight=1.0)

    # Default background
    default_path = "./pictures/background.jpg" 
    
    if os.path.exists(default_path):
        image = Image.open(default_path).resize((screen_width, screen_height), Image.ANTIALIAS)
    else:
        image = Image.new('RGB', (screen_width, screen_height), 'black')

    image_tk = ImageTk.PhotoImage(image)
    background_element = canvas.create_image(0, 0, image=image_tk, anchor=tk.NW)

    # Add frame to canvas
    frame = tk.Frame(bg="black", height=screen_height,width=150)
    frame.grid_propagate(False)
    frame.columnconfigure(0, weight=1)
    canvas.create_window(screen_width, 0, window=frame, anchor=tk.NE)
    
    # Add clear overlay and empty text 
    initial_text = ""
    overlay_img = Image.new('RGBA', (screen_width, screen_height), (0,0,0,0))
    overlay_img_tk = ImageTk.PhotoImage(overlay_img)
    overlay_element = canvas.create_image(0, 0, image=overlay_img_tk, anchor=tk.NW)
    overlay_text = canvas.create_text((screen_width-150)/2, screen_height/2, anchor=tk.CENTER, text=initial_text, fill="yellow",font="Times 30 italic bold")

    # Add buttons to frame
    buttons_settings = settings['BUTTONS']
   
    for index, button_settings  in enumerate(buttons_settings):
    
        frame.rowconfigure(index, weight=1, uniform="right_buttons")

        button_text = button_settings['text']
        button_action = send_message_callback(button_settings['message'])

        button = ttk.Button(frame, text=button_text, command=button_action)
        button.grid(row=index, column=0, padx=5, pady=5, sticky="nsew")

    # Force screen on before tkinter main loop begins
    run_command('screen-on')

    # Start polling email and enter main event loop
    root.after(0, poll_email)
    root.mainloop()
    root.destroy()

    # If the main loop was exited by an exception, then raise that exception
    if exception:
        raise exception

def main():
    
    connection = init_email_connection()
    run(connection)

if __name__ == '__main__':
    try:
        main()  
    except Exception:
        crash_details = traceback.format_exc()
        event_logger.log_event('CRASH', crash_details) 

