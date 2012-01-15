from google.appengine.api.mail import EmailMessage

def sendMail(emailId,subject,body):
    emailMessage = EmailMessage()
    emailMessage.sender = "Support <support@grafiteapp.appspotmail.com>"
    emailMessage.to = emailId
    emailMessage.subject = subject
    emailMessage.html = body
    return emailMessage.send()