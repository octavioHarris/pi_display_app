#!/usr/bin/python

import traceback
import ConfigParser
import Tkinter

def exception_handler(text_segments, attachments):

    raise Exception(text_segments[0])

def print_handler(text_segments, attachments):

    for text in text_segments:
        print(text)

def win_open():

    root = Tkinter.Tk()
    root.attributes('-fullscren', True)
    root.mainloop()

def win_close():

    quit()

def run(email_listener, settings):

    email_listener.stop()
    email_listener.register_handler('open', win_open)
    email_listener.register_handler('close', win_close)
    email_listener.register_handler('print', print_handler)
    email_listener.register_handler('exception', exception_handler)
    email_listener.start()

def main():
    
    connection = init_email_connection()
    run(connection)

if __name__ == '__main__':
    try:
        main()
    except Exception:
        crash_details = traceback.format_exc()
        event_logger.log_event('CRASH', crash_details) 

