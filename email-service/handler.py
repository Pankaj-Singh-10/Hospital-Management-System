import json
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def send_email(event, context):
    """
    Python serverless function to send emails
    Triggered by HTTP POST request
    """
    try:
        # Log the incoming event
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        # Extract required fields
        action = body.get('action')
        recipient_email = body.get('email')
        
        if not action or not recipient_email:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Missing required fields: action and email'})
            }
        
        # Get SMTP settings from environment variables
        smtp_host = os.environ.get('SMTP_HOST')
        smtp_port = int(os.environ.get('SMTP_PORT', 587))
        smtp_user = os.environ.get('SMTP_USER')
        smtp_password = os.environ.get('SMTP_PASSWORD')
        
        # Prepare email content based on action
        if action == 'SIGNUP_WELCOME':
            subject = "Welcome to Hospital Management System"
            name = body.get('name', 'User')
            user_type = body.get('user_type', 'user')
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #2c3e50; color: white; padding: 10px; text-align: center; }}
                    .content {{ padding: 20px; }}
                    .footer {{ background-color: #f4f4f4; padding: 10px; text-align: center; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>Welcome to HMS!</h2>
                    </div>
                    <div class="content">
                        <p>Dear <strong>{name}</strong>,</p>
                        <p>Thank you for signing up as a <strong>{user_type}</strong> on our Hospital Management System.</p>
                        <p>You can now log in and start using our services:</p>
                        <ul>
                            <li>View available doctors</li>
                            <li>Book appointments</li>
                            <li>Manage your schedule</li>
                        </ul>
                        <p>If you have any questions, please don't hesitate to contact us.</p>
                    </div>
                    <div class="footer">
                        <p>&copy; 2024 Hospital Management System. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
            Welcome to HMS!
            
            Dear {name},
            
            Thank you for signing up as a {user_type} on our Hospital Management System.
            
            You can now log in and start using our services.
            
            Best regards,
            HMS Team
            """
        
        elif action == 'BOOKING_CONFIRMATION':
            subject = "Appointment Confirmation - Hospital Management System"
            patient_name = body.get('patient_name', 'Patient')
            doctor_name = body.get('doctor_name', 'Doctor')
            date = body.get('date', '')
            start_time = body.get('start_time', '')
            end_time = body.get('end_time', '')
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #27ae60; color: white; padding: 10px; text-align: center; }}
                    .content {{ padding: 20px; }}
                    .appointment-details {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                    .footer {{ background-color: #f4f4f4; padding: 10px; text-align: center; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>Appointment Confirmed!</h2>
                    </div>
                    <div class="content">
                        <p>Dear <strong>{patient_name}</strong>,</p>
                        <p>Your appointment has been successfully confirmed. Here are the details:</p>
                        
                        <div class="appointment-details">
                            <h3>Appointment Details:</h3>
                            <p><strong>Doctor:</strong> Dr. {doctor_name}</p>
                            <p><strong>Date:</strong> {date}</p>
                            <p><strong>Time:</strong> {start_time} - {end_time}</p>
                        </div>
                        
                        <p>Please arrive 10 minutes before your scheduled time.</p>
                        <p>If you need to cancel or reschedule, please log in to your account.</p>
                    </div>
                    <div class="footer">
                        <p>&copy; 2024 Hospital Management System. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
            Appointment Confirmed!
            
            Dear {patient_name},
            
            Your appointment with Dr. {doctor_name} has been confirmed.
            
            Date: {date}
            Time: {start_time} - {end_time}
            
            Thank you for choosing HMS!
            """
        
        else:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': f'Invalid action: {action}'})
            }
        
        # Send email
        result = send_smtp_email(
            smtp_host, smtp_port, smtp_user, smtp_password,
            recipient_email, subject, html_content, text_content
        )
        
        if result:
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'message': 'Email sent successfully',
                    'action': action,
                    'recipient': recipient_email
                })
            }
        else:
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Failed to send email'})
            }
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }

def send_smtp_email(host, port, user, password, to_email, subject, html_content, text_content):
    """Send email using SMTP"""
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = user
        msg['To'] = to_email
        
        # Attach both plain text and HTML versions
        part1 = MIMEText(text_content, 'plain')
        part2 = MIMEText(html_content, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        # Connect to SMTP server
        logger.info(f"Connecting to SMTP server {host}:{port}")
        server = smtplib.SMTP(host, port)
        server.starttls()
        server.login(user, password)
        
        # Send email
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"SMTP error: {str(e)}")
        raise

    