#!/usr/bin/python

import traceback
import ConfigParser
import Tkinter
import subprocess
#import threading

root = None

def exception_handler(text_segments, attachments):

    raise Exception(text_segments[0])

def print_handler(text_segments, attachments):

    for text in text_segments:
        print(text)

def program_exit(text_segments, attachments):

    if root:
        root.destroy()
 
    quit()

def restart(text_segments, attachments):
   
    if root:
        root.quit()

    # Return false to stop the listener
    return False

def run(email_listener, settings):

    # Register the handlers for the types of actions
    email_listener.register_handler('restart', restart)
    email_listener.register_handler('exit', program_exit)
    email_listener.register_handler('print', print_handler)
    email_listener.register_handler('exception', exception_handler)
   
    # Initialize and open the Tkinter window
    global root
    root = Tkinter.Tk()
    root.attributes('-fullscreen', True) 

    # Function to poll email using Tkinter's after function
    def poll_email():
        
        if not email_listener.running: return

        root.after(int(email_listener.poll_interval * 1000), poll_email)
        email_listener.process_latest_email()

    # Set the email_listener to running
    email_listener.running = True
    
    # Start polling email and enter main event loop
    root.after(0, poll_email)
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

