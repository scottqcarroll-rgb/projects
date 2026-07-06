#!/usr/bin/env python3
"""
One-time script to create Plastic Travel products and payment links in Stripe.
Run once: python setup_stripe.py
"""
import os, stripe
from dotenv import load_dotenv

load_dotenv()
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def create_payment_link(name, amount_cents, description):
    product = stripe.Product.create(name=name, description=description)
    price   = stripe.Price.create(
        product=product.id,
        unit_amount=amount_cents,
        currency='usd',
    )
    link = stripe.PaymentLink.create(
        line_items=[{'price': price.id, 'quantity': 1}],
        after_completion={'type': 'redirect', 'redirect': {'url': 'https://plastictravel.com'}},
    )
    return link.url

print("Creating Stripe products and payment links...")

test_url = create_payment_link(
    name="Plastic Travel — $1 Test Payment",
    amount_cents=100,
    description="Test payment for Plastic Travel workflow verification."
)

deep_dive_url = create_payment_link(
    name="Plastic Travel — Strategy Deep Dive",
    amount_cents=87500,
    description="75-minute credit card rewards strategy session. Full audit of your cards, spend categories, and travel goals. You walk away with a complete, custom points strategy."
)

print(f"\nSTRIPE_LINK_TEST={test_url}")
print(f"STRIPE_LINK_DEEP_DIVE={deep_dive_url}")
print("\nAdd these to your .env file.")
