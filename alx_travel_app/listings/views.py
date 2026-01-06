from django.shortcuts import render
from django.conf import settings

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

import requests
import uuid

from .models import Listing, Booking, Payment
from .serializers import ListingSerializer, BookingSerializer
from .tasks import send_payment_confirmation


class ListingViewSet(viewsets.ModelViewSet):
    '''
    ViewSet for managing property listings.
    offers full CRUD operations: list, retrieve, create, update, delete
    '''
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer
    authentication_class = [TokenAuthentication, SessionAuthentication]
    permission_class = [IsAuthenticated]


class BookingViewSet(viewsets.ModelViewSet):
    '''
    ViewSet for managing bookings.
    offers full CRUD operations: list, retrieve, create, update, delete
    '''
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    authentication_class = [TokenAuthentication, SessionAuthentication]
    permission_class = [IsAuthenticated]


@api_view(['POST'])
def initiate_payment(request):
    amount = request.data.get('amount')
    booking_reference = request.data.get('booking_reference')
    email = request.data.get('email')

    if not all([amount, booking_reference, email]):
        return Response(
            {"error": "amount, booking_reference and email are required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    tx_ref = str(uuid.uuid4())

    payment = Payment.objects.create(
        email=email,
        booking_reference=booking_reference,
        amount=amount,
        status='PENDING',
        transaction_id=tx_ref
    )

    payload = {
        'amount': str(amount),
        'currency': 'ETB',
        'email': email,
        'tx_ref': tx_ref,
        'callback_url': 'http://localhost:8000/api/verify-payment/',
        'return_url': 'http://localhost:8000/payment-success/',
        'customization': {
            'title': 'Travel Booking Payment',
            'description': 'Payment for booking'
        }
    }

    headers = {
        'Authorization': f'Bearer {settings.CHAPA_SECRET_KEY}'
    }

    response = requests.post(
        'https://api.chapa.co/v1/transaction/initialize',
        json=payload,
        headers=headers
    )

    if response.status_code == 200:
        data = response.json().get('data', {})
        checkout_url = data.get('checkout_url')

        if not checkout_url:
            payment.status = 'FAILED'
            payment.save()
            return Response(
                {'error': 'Invalid response from payment gateway'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(
            {'checkout_url': checkout_url},
            status=status.HTTP_200_OK
        )
    
    payment.status = 'FAILED'
    payment.save()
    
    return Response(
        {'error': 'Payment initiation failed'},
        status=status.HTTP_400_BAD_REQUEST
    )


@api_view(['GET'])
def verify_payment(request):
    tx_ref = request.GET.get('tx_ref')
    if not tx_ref:
        return Response({"error": "tx_ref is required"}, status=400)

    payment = Payment.objects.filter(transaction_id=tx_ref).first()
    if not payment:
        return Response({'error': 'Payment not found'}, status=404)

    headers = {
        'Authorization': f'Bearer {settings.CHAPA_SECRET_KEY}'
    }

    response = requests.get(
        f'https://api.chapa.co/v1/transaction/verify/{tx_ref}',
        headers=headers
    )

    data = response.json()

    if data.get('status') == 'success':
        payment.status = 'COMPLETED'
        payment.save()

        # Trigger Celery email task here
        send_payment_confirmation.delay(payment.email)

        return Response({'message': 'Payment verified successfully'})

    payment.status = 'FAILED'
    payment.save()

    return Response({'message': 'Payment failed'}, status=400)
