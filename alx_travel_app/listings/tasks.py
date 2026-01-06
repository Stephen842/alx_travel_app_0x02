from celery import shared_task
from django.core.mail import send_mail

@shared_task
def send_payment_confirmation(email):
    send_mail(
        'Payment Successful',
        'Your booking payment was successful.',
        'noreply@travelapp.com',
        [email],
        fail_silently=True,
    )
