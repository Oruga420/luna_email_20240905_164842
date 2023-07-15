import getpass
import time
import sys
import email
import imaplib
import smtplib
import openai
from functools import reduce
from openai import ChatCompletion
from email.utils import parseaddr
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# account credentials
username = "ur email here"
password = getpass.getpass()

# create an IMAP4 class with SSL 
conn = imaplib.IMAP4_SSL("outlook.office365.com")
conn.login(username, password)

# Set openai secret key
openai.api_key = 'OpenAI API Key Here'

# Define the sender filter
sender_filter = "Email to scan for here"

def get_body(email_message):
    if email_message.is_multipart():
        return ''.join(
            part.get_payload(decode=True).decode('utf-8') 
            for part in email_message.walk() 
            if part.get_content_type() == 'text/plain' 
        )
    else:
        return email_message.get_payload(decode=True).decode('utf-8')

def send_email(to_addr, subject, message):
    from_addr = username
    password = getpass.getpass()

    msg = MIMEMultipart()
    msg['From'] = from_addr
    msg['To'] = to_addr
    msg['Subject'] = subject

    msg.attach(MIMEText(message, 'plain'))

    server = smtplib.SMTP('smtp-mail.outlook.com', 587)
    server.starttls()
    server.login(from_addr, password)
    server.sendmail(from_addr, to_addr, msg.as_string())
    server.quit()

def check_email():
    mailbox = "INBOX"
    conn.select(mailbox)

    _, data = conn.uid('search', None, "(UNSEEN)")
    email_ids = data[0].split()

    if not email_ids:
        print("No New Emails.")
        return None, None, None

    for email_id in email_ids:
        _, data = conn.uid('fetch', email_id, '(BODY.PEEK[])')
        raw_email = data[0][1]
        email_message = email.message_from_bytes(raw_email)

        sender = parseaddr(email_message["From"])[1] 
        subject = email_message["Subject"]
        body = get_body(email_message)
      
        if sender == sender_filter:
            if any(word in subject or word in body for word in ['Meeting', 'Report', 'meeting', 'report']):
                continue 

            # This will mark the email as Read
            conn.uid('store', email_id, '+FLAGS', '\Seen')

            return sender, subject, body

    return None, None, None

def generate_response(chat_model, chat_messages):
    response = ChatCompletion.create(model=chat_model, messages=chat_messages)
    return response['choices'][0]['message']['content']

def prompt_input(message):
    return input(message).strip().lower() == 'y'

while True:
    sender, subject, body = check_email()

    if sender is not None:
        chat_model = "gpt-4"
        chat_messages = [{
    "role": "system", 
    "content": "You are a AI stoner Assistant that responds to email"
}, {
    "role": "user", 
    "content": f"Hey dude, You are reading my email please follow my instructions and do not invent anything its super important luna if its short its short just do not invent things dude, I got a new mail with the subject '{subject}', generate a stonery summary and a pun please friend? and start the pun with a yo dude or a hey boss or oruga dude something cool like that. Please just Generate what I asked nothing else dude. Keep it 100% only about the subject do not invent anything dude if its too short just tell me dude to short to make a pun but there a new email about this <subject here>.  just say the pun keep it natural "
}
    
]
        
        email_response = generate_response(chat_model, chat_messages)
        
        print("New Email Alert: ", email_response)
        
        if prompt_input("Do you want to respond? (y/n): "):
            additional_thoughts = input("Any additional thoughts?: ")
            chat_messages.append({
                "role": "user",
                "content": f"Hey dude You are reading my email please follow my instructions and do not invent anything its super important luna if its short its short just do not invent things dude, here this email '{body}', and here are my additional thoughts on it '{additional_thoughts}'. Generate a stonery response to it please dude? Please just Generate what I asked nothing else dude and keep it 100% only about the email. If it's too short just say thanks for you email but I need more info to work with it  and mock the fact that is way to short for a longer answer at the end sign up as Luna Orugas AI Stoner Assistant"
            })
            email_response = generate_response(chat_model, chat_messages)
            
            print("Email response generated: ", email_response)

            while True:
                if prompt_input("Send response? (y/n): "):
                    send_email(sender, "Re: " + subject, email_response)
                    print("Email sent.")
                    break
                elif prompt_input("Want to generate a different response? (y/n): "):
                    additional_thoughts = input("Any additional thoughts?: ")
                    chat_messages.append({
                        "role": "user",
                        "content": additional_thoughts
                    })
                    email_response = generate_response(chat_model, chat_messages)
                    print("New email response generated: ", email_response)
                else:
                    break

    for remaining in range(30, 0, -1):
        sys.stdout.write("\r")
        sys.stdout.write("{:2d} seconds remaining.".format(remaining))
        sys.stdout.flush()
        time.sleep(1)