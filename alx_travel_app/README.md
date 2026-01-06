# ALX Travel App — Milestone 2 & 3

This project implements database models, serializers, API views, and third-party
integration for a travel booking platform. It supports listings, bookings, and
secure payment processing using the **Chapa API**, with email notifications
handled asynchronously.

---

## Features

### Core Features
- Django models for:
  - Listing
  - Booking
  - Review
  - Payment
- Django REST Framework (DRF) serializers for:
  - Listing
  - Booking
- REST API endpoints for:
  - Listings
  - Bookings
  - Payment initiation
  - Payment verification
- Secure payment processing using **Chapa**
- Email confirmation on successful payment (via Celery)
- Custom management command:
  - `seed` — populates the database with sample listings

---

## Project Duplication

- Project duplicated from:
  - `alx_travel_app_0x01` → `alx_travel_app_0x02`
- Payment integration and background tasks added in this milestone

---

## Payment Integration (Chapa API)

The application integrates the **Chapa payment gateway** to allow users to
securely pay for travel bookings.

### Payment Workflow

1. User creates a booking
2. Payment is initiated via Chapa
3. User is redirected to Chapa checkout page
4. Chapa processes the payment
5. Payment status is verified via API
6. Payment status is updated in the database
7. Confirmation email is sent on success

---

## Payment Model

A `Payment` model was added to store transaction details.

### Stored Fields
- Email
- Booking reference
- Amount
- Transaction ID (`tx_ref`)
- Payment status (`PENDING`, `COMPLETED`, `FAILED`)
- Timestamps

---

## Environment Variables

Chapa credentials are stored securely using environment variables.
