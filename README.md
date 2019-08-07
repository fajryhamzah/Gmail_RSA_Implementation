# Gmail_RSA_Implementation
Sending Email via GMAIL with encrypted content message

#Requirements
- Redis
- Virtual Environtment
- Python
- Gmail Account with Allow less secure apps option set to ON

# How to use
- Activate Redis Server
- Activate the virtualenv
- run server.py


# Simple Scenario
- Log In to in the apps with gmail account
- Generate RSA key in generate key page
- Send the Public key via anything to another person
- Another person login and paste the public key in the "public key tujuan" page
- Send email via apps home page and set the encryption menu with the key that just copied before
- Email will be appears in destination inbox with encrypted message
- To decrypt the message, the destination log in via the apps and write the sender email in the "baca email" page
- Open the email
- Decrypt the message with the saved private key
