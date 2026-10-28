import os
import smtplib

from supabase import create_client, Client
from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# 1. Initialize Supabase Client
# url: str = os.environ.get("SUPABASE_URL")
# key: str = os.environ.get("SUPABASE_KEY")

load_dotenv()
url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def fetch_unsent_campaigns():
    # Query Supabase for rows where emails haven't been sent yet
    response = supabase.table("email_campaigns").select("*").eq("is_sent", False).execute()
    return response.data # returns array/ list of OBJECTS from database

def render_and_prepare_emails():
    # 2. Set up Jinja2 Environment targeting the local templates directory
    # both statements below combine to make path templates/email_base.html
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("email_base.html")
    
    # Stores returned result from the Supabase query in function fetch_unsent_campaigns()
    # Each object in the list represents a single email campaign record from the database
    campaigns = fetch_unsent_campaigns()
    print(campaigns)
    
    if not campaigns:
        print("No pending/ unsent campaigns found in Database.")
        return

    for record in campaigns:
        # 3. Render dynamic content map directly into the template on variable "rendered_html"
        rendered_html = template.render(
            campaign_name=record["campaign_name"],
            first_name=record["first_name"],
            discount_code=record["discount_code"],
            product_title=record["product_title"],
            expires_at=record["expires_at"]

            # NOTE response from database was returned as a list of dictionaries (objects) where each dictionary represents a single campaign.
            # The key/ value pairs correspond to the columns in the database table and are access via BRACKET NOTATION [] as opposed to . notation
            # because the column names are strings that are MORE than one word long!
        )
        
        # Output or dispatch point
        print(f"--- Compiled HTML for {record['recipient_email']} ---")
        # print(rendered_html[:300] + "...\n")  # Preview snippet

        # Set up email details from environment variables
        sender_email = os.getenv("SENDER_EMAIL")
        password = os.getenv("EMAIL_PASSWORD")
        smtp_server = os.getenv("SMTP_SERVER")
        smtp_port = int(os.getenv("SMTP_PORT"))

        receiver_email = "receiver@example.com"

        subject = "Welcome to Company"
       
        #HTML content
        html_content = rendered_html
        print(html_content)

        # Create the email message
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = subject

        # Attach email body to message
        # message.attach(MIMEText(body, "plain"))
        message.attach(MIMEText(rendered_html, "html"))
        
        # Establish a connection to the SMTP server and send the email
        try:
            # Connect to the SMTP server
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()  # Secure the connection
                server.login(sender_email, password)  # Log in to the SMTP server
                server.sendmail(
                    sender_email, receiver_email, message.as_string()
                )  # Send the email
            print("Email sent successfully")
        except Exception as e:
            print(f"Error: {e}")


        # # HTML content
        # html_content = rendered_html
        
        # TODO: Hook your SMTP or email API sender here (e.g., SendGrid, Resend, Amazon SES)
        # send_email(record['recipient_email'], record['campaign_name'], rendered_html)
        
        # Mark as sent in Supabase to prevent duplicate sends
        # supabase.table("email_campaigns").update({"is_sent": True}).eq("id", record["id"]).execute()

if __name__ == "__main__":
    render_and_prepare_emails()