#!/usr/bin/python

from PIL import Image, ImageTk
import traceback
import ConfigParser
import Tkinter as tk
import subprocess

root = None
email_listener = None

supported_bash_commands = [
    'screen-on',
    'screen-off',
    'update-repo'
]

def exception_handler(message):

    run_command('screen-on')
    
    raise Exception(message.args[0])

def print_handler(message):

    run_command('screen-on')

    for arg in message.args:
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

    background_name = './pictures/' + message.parts[0]
    background_photo = Image.open(background_name)
    background_image = ImageTk.PhotoImage(background_photo)
    background_label.configure(image=background_image)
    background_label.image = background_image
    background_label.pack(fill=tk.BOTH, expand=tk.YES)

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

def run(email_listener, settings):

    # Register the handlers for the types of actions
    email_listener.register_handler('background', background_handler)
    email_listener.register_handler('update', update_handler, noargs=True)
    email_listener.register_handler('restart', restart_handler, noargs=True)
    email_listener.register_handler('exit', exit_handler, noargs=True)
    email_listener.register_handler('print', print_handler)
    email_listener.register_handler('exception', exception_handler)
   
    # Initialize and open the Tkinter window
    global root
    root = tk.Tk()
    root.attributes('-fullscreen', True) 

    # Function to poll email using Tkinter's after function
    def poll_email():
        
        if not email_listener.running: return

        root.after(int(email_listener.poll_interval * 1000), poll_email)
        email_listener.process_latest_email()

    # Set the email_listener to running and wake screen
    email_listener.running = True
    run_command('screen-on')

    # Start polling email and enter main event loop
    root.after(0, poll_email)


    global background_label
    background_photo = Image.open('./pictures/ali_birthday.png')
    background_image = ImageTk.PhotoImage(background_photo)
    background_label = tk.Label(root, image=background_image)
    background_label.image = background_image
    background_label.pack(fill=tk.BOTH, expand=tk.YES)

    root.mainloop()
    root.destroy()

def main():
    
    connection = init_email_connection()
    run(connection)

if __name__ == '__main__':
    try:
        main()
    except Exception:
        crash_details = traceback.format_exc()
        event_logger.log_event('CRASH', crash_details) 

