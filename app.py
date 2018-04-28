#!/usr/bin/python

from PIL import Image, ImageTk
import os
import traceback
import ConfigParser
import Tkinter as tk
import ttk
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

def exception_handler(message):

    run_command('screen-on')
    
    raise Exception(message.parts[0])

def print_handler(message):

    run_command('screen-on')

    for arg in message.parts:
        print(arg)

def exit_handler():

    run_command('screen-on')

    if root:
        root.attributes('-fullscreen', False)
        root.destroy()
 
    quit()

def restart_handler():
   
    run_command('screen-on')
    
    if root:
        root.attributes('-fullscreen', False)
        root.quit()

def update_handler():

    run_command('screen-on')
    run_command('update-repo')
    restart_handler()

def background_handler(message):
   
    message.save_attachments(map_file_to_directory)
   
    path = './pictures/' + message.parts[0]
    image = Image.open(path).resize((screen_width, screen_height), Image.ANTIALIAS)
    image_tk = ImageTk.PhotoImage(image)
    components['background'] = image_tk
    canvas.itemconfig(background_element, image=image_tk)     

    run_command('screen-on')

def map_file_to_directory(filename):

    if filename.endswith('png') or filename.endswith('jpg'):
        return './pictures/'
    
    return './unsorted_attachments/'        

def run_command(command):

    if not command in supported_bash_commands: return
    call_args = ['bash', './scripts/commands.sh', command]
    return_val = subprocess.call(call_args)

    if return_val != 0:
        raise Exception('Error using commands.sh')

def message(message):
 
    run_command('screen-on')
    set_overlay_opacity(180)
    canvas.itemconfig(overlay_text, text=message.parts[0])
    run_command('screen-on')

def clear_message():

    run_command('screen-on')
    set_overlay_opacity(0)
    canvas.itemconfig(overlay_text, text="")
    run_command('screen-on')

def send_message_callback(message):

    def wrapper():

        connection.send_email('harris.octavio@gmail.com', message.upper(), message)

    return wrapper

def set_overlay_opacity(value):

    # Add darkening to the screen
    overlay_img = Image.new('RGBA', (screen_width, screen_height), (0,0,0,value))
    overlay_img_tk = ImageTk.PhotoImage(overlay_img)
    components['overlay'] = overlay_img_tk
    canvas.itemconfig(overlay_element, image=overlay_img_tk)

def run(email_connection, email_listener, settings):

    global connection
    connection = email_connection

    # Register the handlers for the types of actions
    email_listener.register_handler('background', background_handler)
    email_listener.register_handler('message', message)
    email_listener.register_handler('clear_message', clear_message, noargs=True)
    email_listener.register_handler('update', update_handler, noargs=True)
    email_listener.register_handler('restart', restart_handler, noargs=True)
    email_listener.register_handler('exit', exit_handler, noargs=True)
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
    run_command('screen-on')

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

    # Add clear overlay and empty text 
    initial_text = "Sorry for being a crappy boyfriend"
    overlay_img = Image.new('RGBA', (screen_width, screen_height), (0,0,0,180))
    overlay_img_tk = ImageTk.PhotoImage(overlay_img)
    overlay_element = canvas.create_image(0, 0, image=overlay_img_tk, anchor=tk.NW)
    overlay_text = canvas.create_text((screen_width-150)/2, screen_height/2, anchor=tk.CENTER, text=initial_text, fill="yellow",font="Times 30 italic bold")

    # Add frame to canvas
    frame = tk.Frame(bg="black", height=screen_height,width=150)
    frame.grid_propagate(False)
    frame.columnconfigure(0, weight=1)
    canvas.create_window(screen_width, 0, window=frame, anchor=tk.NE)
    
    # Clear message on click
    canvas.bind("<Button-1>", lambda e: clear_message())
    
    # Add buttons to fram
    button_configs = [{   
        'text': "Oct is dumb",
        'callback': send_message_callback("Emily: you're dumb.")
    },{
        'text': "Why is Oct late",
        'callback': send_message_callback("Emily: why are you always late")
    },{
        'text': "No one is uglier...",
        'callback': send_message_callback("Emily: No one is uglier than you with your clothes off")
    },{
        'text': "I hate you",
        'callback': send_message_callback("Emily: I hate you")
    }]

    # Add buttons to frame
    for index, config in enumerate(button_configs):
    
        frame.rowconfigure(index, weight=1, uniform="right_buttons")

        button = ttk.Button(frame, text=config['text'], command=config['callback'])
        button.grid(row=index, column=0, padx=5, pady=5, sticky="nsew")
    
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

