#!/usr/bin/python
import re
import time
import traceback
import subprocess
import ConfigParser
import pynput.keyboard as keyboard
from email_utils import EmailConnection

# Constants used
SEPARATOR_REGEX = '\r\n####'
SETTINGS_FILE_PATH = './settings.ini'
STATUS_REPORT_ADDRESS = 'harris.octavio@gmail.com'

# Global variables
terminate = False
def restart_script():

    print('Restarting script...')
    subprocess.call(['python', 'receive.py'])
    exit(0)

def exception_handler(text_segments, attachments):
    raise Exception(text_segments[0])

def print_handler(text_segments, attachments):

    for text in text_segments:
        print(text)

def reflash_handler(content_parts, attachments):

    # Verify number of attachments
    if len(attachments) != 1:
        print('Updating file requires 1 attachment.')
        return

    # Extract necessary information
    attachment_filename = attachments[0]['filename']
    attachment_contents = attachments[0]['binary']

    # Write file contents to a tmp file
    print('Updating file...')
    with open(attachment_filename,"wb") as file:
        file.write(attachment_contents)

    # Restart script with updated file
    restart_script()

def on_press(key):
    
    if key == keyboard.Key.esc:
        print('Terminate signal received.')
        global terminate
        terminate = True
        return False

def process_message(body, attachments):

    # Verify passed string is not empty
    if body == None:
        print('Cannot process empty email body.')
        return

    # Extract message type and text segments
    parts = re.split(SEPARATOR_REGEX, body)
    parts = map(str.strip, parts)
    message_type = parts[0].strip()
    text_segments = parts[1::]

    # Verify there is a configured handler for the specified message type
    if message_type not in handlers:
        print('Unhandled message type: ' + message_type)
        return

    # Call the appropriate handler
    handlers[message_type](text_segments, attachments)
   
def run(connection, event_logger):
  
    # Read from settings.ini file
    config = ConfigParser.ConfigParser()
    config.optionxform=str 
    config.read(SETTINGS_FILE_PATH) 

    # Extract program settings 
    READ_INTERVAL = float(config.get('PROGRAM', 'READ_INTERVAL'))
    LAST_PROCESSED_ID_FILE = config.get('PROGRAM', 'LAST_PROCESSED_ID_FILE')
 
    # Listen for esc to be pressed to exit
    with keyboard.Listener(on_press=on_press) as listener:
   
        # Set up times for repeating reads
        next_read_time = time.time() + READ_INTERVAL

        while not terminate:

            last_id = connection.fetch_email_ids()[-1]
            
            # Check the last processed message
            with open(LAST_PROCESSED_ID_FILE, 'a+') as file:
                last_processed_id = file.readline()

            
            if not last_processed_id or last_id != last_processed_id.strip():
                
                # Save the id of the last processed email
                with open(LAST_PROCESSED_ID_FILE, 'w') as file:
                    file.write(last_id)

                # Process the contents of the email
                body, attachments = connection.fetch_email(last_id)
                process_message(body, attachments)

            # Sleep from now until next specified read time
            time.sleep(next_read_time - time.time())
            next_read_time += READ_INTERVAL

def main():
    
    connection = init_email_connection()
    run(connection)

handlers = {
    'print': print_handler,
    'reflash' : reflash_handler,
    'exception' : exception_handler
}

if __name__ == '__main__':
    try:
        main()
    except Exception:
        crash_details = traceback.format_exc()
        event_logger.log_event('CRASH', crash_details) 

