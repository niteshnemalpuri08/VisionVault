import yagmail
from datetime import date
from twilio.rest import Client

# =========================================================
# ⚙️ CONFIGURATION
# =========================================================

# 📧 EMAIL SETTINGS (Updated with your App Password)
SENDER_EMAIL = "niteshnemalpuri17@gmail.com"
SENDER_PASSWORD = "shwx suzm wgro vwll"  

# 📱 SMS SETTINGS (Twilio - Optional/Placeholder)
TWILIO_SID = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TWILIO_AUTH = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TWILIO_PHONE = "+1555000000"

# =========================================================
# 🚀 INITIALIZATION
# =========================================================

try:
    # Initialize Email Client Globally
    yag = yagmail.SMTP(SENDER_EMAIL, SENDER_PASSWORD)
    print(f"✅ Email System Ready ({SENDER_EMAIL})")
except Exception as e:
    yag = None
    print(f"⚠️ Email Config Invalid: {e}")

try:
    # Initialize SMS Client
    sms_client = Client(TWILIO_SID, TWILIO_AUTH)
except:
    sms_client = None

# =========================================================
# 📧 FUNCTIONS
# =========================================================

def send_absent_email(student_name, parent_email, date_absent):
    if not yag: 
        print("❌ Email not sent: System not configured.")
        return
    
    try:
        subject = f"Alert: {student_name} Absent Today"
        body = f"""
        Dear Parent,
        
        This is to inform you that your ward {student_name} was marked ABSENT today ({date_absent}).
        
        Please contact the HOD if this is a mistake.
        
        Regards,
        GIET University
        """
        yag.send(to=parent_email, subject=subject, contents=body)
        print(f"📧 Absent Email sent to {parent_email}")
    except Exception as e:
        print(f"❌ Email Failed: {e}")

def send_absent_sms(student_name, parent_phone):
    if not sms_client: return
    try:
        msg = f"GIETU ALERT: {student_name} is ABSENT today ({date.today()})."
        sms_client.messages.create(body=msg, from_=TWILIO_PHONE, to=parent_phone)
        print(f"📱 SMS sent to {parent_phone}")
    except Exception as e:
        print(f"❌ SMS Failed: {e}")

def send_payment_receipt(student_name, parent_email, filename, pdf_buffer):
    """
    Sends the fee payment receipt with PDF attachment.
    """
    if not yag:
        print("❌ Receipt not sent: yagmail not configured.")
        return False

    try:
        subject = f"✅ Fee Receipt: {student_name}"
        body = f"""
        Dear Parent,
        
        We have received the payment for {student_name}.
        
        Please find the official receipt attached below.
        
        Transaction Status: VERIFIED
        
        Regards,
        GIET University Accounts Dept.
        """
        
        # Ensure the buffer is at the start
        pdf_buffer.seek(0)
        
        # Send Email with Attachment
        yag.send(
            to=parent_email,
            subject=subject,
            contents=body,
            attachments=pdf_buffer # The PDF file from memory
        )
        print(f"📧 Receipt sent successfully to {parent_email}")
        return True

    except Exception as e:
        print(f"❌ Email Failed: {e}")
        return False