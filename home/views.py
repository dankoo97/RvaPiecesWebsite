import stripe
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import TemplateView
from djstripe.settings import djstripe_settings


# Create your views here.
def index(request):
    return render(request, "home/home.html", {})


def faq(request):
    return render(request, "home/faq.html", {})


stripe.api_key = djstripe_settings.STRIPE_SECRET_KEY


class DonateView(TemplateView):
    template_name = "home/donate.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["STRIPE_PUBLIC_KEY"] = djstripe_settings.STRIPE_PUBLIC_KEY

        success_url = self.request.build_absolute_uri(reverse("index"))

        cancel_url = self.request.build_absolute_uri(reverse("index"))

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            # payment_method_types=["bacs_debit"],  # for bacs_debit
            payment_intent_data={
                "setup_future_usage": "off_session",
                # so that the metadata gets copied to the associated Payment Intent and Charge Objects
            },
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        # "currency": "gbp",  # for bacs_debit
                        "unit_amount": 2000,
                        "product_data": {
                            "name": "Sample Product Name",
                            "images": ["https://i.imgur.com/EHyR2nP.png"],
                            "description": "Sample Description",
                        },
                    },
                    "quantity": 1,
                },
            ],
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
        )

        context["CHECKOUT_SESSION_ID"] = session.id

        return context
