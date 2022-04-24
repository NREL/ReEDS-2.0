
from ast import arguments
from ctypes import Union
from lib2to3.pytree import Base
from re import sub
import smtplib, ssl
from email.message import EmailMessage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from abc import ABC, abstractclassmethod, abstractmethod
from jinja2 import FileSystemLoader, Environment
import os
from numpy import source
import sendgrid
from sendgrid.helpers.mail import Email, To, Content, Mail
import boto3
from botocore.exceptions import ClientError

""" Interface for sending the email """
class BaseEmail(ABC):
    
    """ Abstract factory method to send the email"""
    @abstractmethod
    def send_email(sender: str, reciever: str, content: str, subject: str) -> bool:
        pass

""" Interface for sending the email """
class LoginBaseEmail(ABC):
    
    """ Abstract factory method to send the email"""
    @abstractmethod
    def send_email(sender: str, sender_password:str, reciever: str, content: str, subject: str) -> bool:
        pass


""" Interface for only smtp mail"""
class SMTPMail(ABC):

    def __init__(self, smtp_address:str, smtp_port:str):
        self.smtp_address = smtp_address
        self.smtp_port = smtp_port
        self.context = ssl.create_default_context()

""" Concerete implementation for SMTP email communication that requires no login for text message"""    
class NologinSMTPTextMail(SMTPMail, BaseEmail):

    def send_email(self, sender: str, reciever: str, content: str, subject: str) -> bool:
        stm = SimpleTextMessage()
        with smtplib.SMTP_SSL(self.smtp_address, self.smtp_port, context=self.context) as server:
            server.sendmail(sender, reciever, stm.prepare_message(subject, content))

""" Concerete implementation for SMTP email communication that requires no login for html message"""    
class NologinSMTPHTMLMail(SMTPMail, BaseEmail):

    def send_email(self, sender: str, reciever: str, content: str, subject: str) -> bool:
        htm = HTMLMessage()
        with smtplib.SMTP_SSL(self.smtp_address, self.smtp_port, context=self.context) as server:
            server.sendmail(sender, reciever, htm.prepare_message(subject, content))


""" Concerete implementation for SMTP email communication that requires login for text message""" 
class SMTPMailTextMail(SMTPMail, LoginBaseEmail):

    def send_email(self, sender: str, sender_password:str, reciever: str, content: str, subject: str) -> bool:
        stm = SimpleTextMessage()
        with smtplib.SMTP_SSL(self.smtp_address, self.smtp_port, context=self.context) as server:
            server.login(sender, sender_password)
            server.sendmail(sender, reciever, stm.prepare_message(subject, content))

""" Concerete implementation for SMTP email communication that requires login for html message""" 
class SMTPMailHTMLMail(SMTPMail, LoginBaseEmail):

    def send_email(self, sender: str, sender_password:str,  reciever: str, content: str, subject: str) -> bool:
        htm = HTMLMessage()
        with smtplib.SMTP_SSL(self.smtp_address, self.smtp_port, context=self.context) as server:
            server.login(sender, sender_password)
            server.sendmail(sender, reciever, htm.prepare_message(subject, content))


""" Interface for only sendgrid mail"""
class BaseSendGrid(ABC):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.sg = sendgrid.SendGridAPIClient(api_key=self.api_key)

""" Concrete implementation for Sendgrid API to send text email"""
class SendGridTextMail(BaseSendGrid,BaseEmail):
    def send_email(self, sender: str, reciever: str, content: str, subject: str) -> bool:
        sgtm = SendGridTextMessage(sender, reciever)
        response = self.sg.client.mail.send.post(request_body=sgtm.prepare_message(subject, content))

""" Concrete implementation for Sendgrid API to send html email"""
class SendGridHTMLMail(BaseSendGrid,BaseEmail):
    def send_email(self, sender: str, reciever: str, content: str, subject: str) -> bool:
        sghm = SendGridHTMLMessage(sender, reciever)
        response = self.sg.client.mail.send.post(request_body=sghm.prepare_message(subject, content))


""" Nase AWS Simple email service setup """
""" Set up Access keys for boto3 following documentation in https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html#installation"""
class BaseAWS_SES(ABC):

    def __init__(self, aws_region: str, access_key: str, secret_access: str):
        self.aws_region = aws_region
        self.client = boto3.client('ses', region=self.aws_region, aws_access_key_id=access_key,
        aws_secret_access_key=secret_access,)


""" Concrete implementation for AWS text email"""
class AWS_SES_TextMail(BaseAWS_SES, BaseEmail):
    
    def send_email(self, sender: str, reciever: str, content: str, subject: str) -> bool:
        aws_tm = AWSTextMessage(sender, reciever)
        try:
            self.client.send_email(**aws_tm.prepare_message(subject, content))
        except ClientError as e:
            print(e.response['Error']['Message'])

""" Concrete implementation for AWS html email"""
class AWS_SES_HTMLMail(BaseAWS_SES, BaseEmail):
    
    def send_email(self, sender: str, reciever: str, content: str, subject: str) -> bool:
        aws_hm = AWSHTMLMessage(sender, reciever)
        try:
            self.client.send_email(**aws_hm.prepare_message(subject, content))
        except ClientError as e:
            print(e.response['Error']['Message'])

""" Interface for testing email service"""
class TestMail(BaseEmail):

    def send_email(self, message: EmailMessage) -> bool:
        print(message.get_data())


""" Interface for preparing simple email message with body and subject """
class EmailMessage(ABC):

    def prepare_message(subject: str, body: str):
        pass


""" Concrete implementation for simple text message """
class SimpleTextMessage(EmailMessage):

    def prepare_message(self, subject, body) -> str:

        msg = EmailMessage()
        msg['Subject'] = subject
        msg.set_content(body)
        return msg.as_string()

""" Concrete implementation for html message """
class HTMLMessage(EmailMessage):

    def prepare_message(self, subject, body) -> str:
        
        msg = MIMEMultipart("alternative")
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        return msg.as_string()


""" Concrete implementation for send grid text message """
class SendGridTextMessage(EmailMessage):
    
    def __init__(self, sender, reciever):
        self.from_email = Email(sender)
        self.to_email = To(reciever)

    def prepare_message(self, subject: str, body: str):

        content = Content("text/plain", body)
        mail = Mail(self.from_email, self.to_email, subject, content)
        print(mail.get())
        return mail.get()


""" Concrete implementation for send grid html message """
class SendGridHTMLMessage(SendGridTextMessage):

    def prepare_message(self, subject: str, body: str):
        content = Content("text/html", body)
        mail = Mail(self.from_email, self.to_email, subject, content)
        return mail.get()

""" Concrete implementation for AWS SES text message """
class AWSTextMessage(EmailMessage):

    def __init__(self, sender, reciever, config_set = None, charset='UTF-8'):
        self.config_set = config_set
        self.charset = charset
        self.destination = {
            'ToAddresses': [
                reciever,
            ],
        }
        self.source = sender


    def prepare_message(self, subject: str, body: str) -> dict:
        message = {
            'Body': {
                'Text': {
                    'Charset': self.charset,
                    'Data': body,
                },
            },
            'Subject': {
                'Charset': self.charset,
                'Data': subject,
            },
        }

        arguments_dict = {
                'Destination': self.destination,
                'Message': message,
                'Source': self.source,
        }
        if self.config_set:
            arguments_dict.update({"ConfigurationSetName": self.config_set})

        return arguments_dict

""" Concrete implementation for AWS SES html message """
class AWSHTMLMessage(AWSTextMessage):

    def prepare_message(self, subject: str, body: str) -> dict:
        message = {
            'Body': {
                'Html': {
                    'Charset': self.charset,
                    'Data': body,
                },
            },
            'Subject': {
                'Charset': self.charset,
                'Data': subject,
            },
        }

        arguments_dict = {
                'Destination': self.destination,
                'Message': message,
                'Source': self.source,
        }
        if self.config_set:
            arguments_dict.update({"ConfigurationSetName": self.config_set})

        return arguments_dict


class DynamicHTMLContent(ABC):

    def return_rendered_html(self, content_dict:dict):

        file_loader = FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates'))
        env = Environment(loader=file_loader)
        template = env.get_template(self.html_file)
        output = template.render(data=content_dict)

        return output

class UserWelcomeHTMLMessage(DynamicHTMLContent):

    def __init__(self):
        self.html_file = 'user_welcome_message.html'

class UserPasswordResetHTMLMessage(DynamicHTMLContent):

    def __init__(self):
        self.html_file = 'user_password_reset_message.html'

class UserSignUpInstructionsHTMLMessage(DynamicHTMLContent):

    def __init__(self):
        self.html_file = 'user_signup_instructions_message.html'

class UserSignUpRejectionHTMLMessage(DynamicHTMLContent):

    def __init__(self):
        self.html_file = 'user_signup_rejection_message.html'

class UserSignUpRequestNotificationHTMLMessage(DynamicHTMLContent):

    def __init__(self):
        self.html_file = 'user_signup_request_notification_message.html'

class UserSimRunInitiationHTMLMessage(DynamicHTMLContent):

    def __init__(self):
        self.html_file = 'user_simrun_initiation_message.html'

class UserSimRunCompleteHTMLMessage(DynamicHTMLContent):

    def __init__(self):
        self.html_file = 'user_simrun_complete_message.html'


if __name__ == '__main__':

    # Let's try sending simple email usingSMTP

    message = "Hey you got it!"
    message = UserWelcomeHTMLMessage().return_rendered_html({})
    subject = "Test Email"

    api_key = ''
    #sg = SendGridTextMail(api_key)
    sg = SendGridHTMLMail(api_key)
    #sg.send_email('kapil.duwadi@nrel.gov', 'kapil.duwadi@nrel.gov', message, subject)

  