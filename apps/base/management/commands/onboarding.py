import datetime
import json
import logging

from django.core.mail import EmailMultiAlternatives
from django.core.management import BaseCommand
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from apps.base.models import Profile, OnboardEvents
from apps.common.constants import EMAIL_FROM
from mastermind.utils import user_time_now

logger = logging.getLogger('onboarding')

class OnboardSender:
    """
        sales schedule:
        sale-1, 14 days after register
        sale-2, 16 days after register
        research
        trial warning 1: 5 days before trial ends
        trial warning 2: 2 days before trial ends
        On last day
    """

    """
    Onboard schedule:
    1. Project
    2. Plan
    3. Work
    4. Journal
    5. Habits
    """


    ONBOARD_DATA = {
        "project": {
            "subject": "Tip 1 of 5 | The #1 reason they pick LifeHQ over everything else",
            "template": "project.html"
        },
        "plan": {
            "subject": "Tip 2 of 5 | Never waste another productive morning, separate prioritization from execution.",
            "template": "plan.html"
        },
        "work": {
            "subject": "Tip 3 of 5 | Getting focused work done in a world of distractions.",
            "template": "work.html"
        },
        "journal": {
            "subject": "Tip 4 of 5 | Keep your vision front and center with a productivity journal.",
            "template": "journal.html"
        },
        "habits": {
            "subject": "Tip 5 of 5 | Staying consistent with the foundations for energy, creativity and success.",
            "template": "habits.html"
        },
        "discount_1": {
            "subject": "[30% OFF] Win every day by managing your life like a pro",
            "template": "sale-1.html"
        },
        "discount_2": {
            "subject": "[FINAL NOTICE] 30% OFF supercharged productivity and organization ends in few hours",
            "template": "sale-2.html"
        },
        "discount_beta": {
            "subject": "[REMINDER] 50% OFF supercharged productivity and organization ends soon",
            "template": "sale-beta.html"
        },
        "trial_expires_1": {
            "subject": "[Trial ending] Your free trial at LifeHQ expires in 5 days",
            "template": "trial-expires-1.html"
        },
        "trial_expires_2": {
            "subject": "[Trial ending] Your free trial at LifeHQ expires tomorrow",
            "template": "trial-expires-2.html"
        },
        "beta_trial_expires_1": {
            "subject": "[Trial ending] Your free trial at LifeHQ expires in 5 days",
            "template": "beta-trial-expires-1.html"
        },
        "beta_trial_expires_2": {
            "subject": "[Trial ending] Your free trial at LifeHQ expires tomorrow",
            "template": "beta-trial-expires-2.html"
        },
    }


    @classmethod
    def onboard_user(cls, profile, onboarding, user_now):
        what_to_send = onboarding.next_to_send(user_now)
        email = profile.account.user.email
        if what_to_send:
            email_results = cls.send_email(email, what_to_send, onboarding)
            logger.info("Sending {} to {}".format(what_to_send, email))
            onboarding.record_sending(what_to_send, user_now)
        else:
            logger.info("Not sending onboard to {}, what to send is {}".format(email, what_to_send))


    @classmethod
    def send_sales(cls, profile, onboarding, user_now):
        user_joined = profile.account.user.date_joined
        trial_end = profile.trial_end_time
        what_to_send = onboarding.sale_to_send(user_joined, trial_end, user_now, profile.profile_type)
        if what_to_send and what_to_send in cls.ONBOARD_DATA:
            email = profile.account.user.email
            cls.send_email(email, what_to_send, onboarding)
            logger.info("Sending {} to {}".format(what_to_send, email))
            onboarding.record_sending(what_to_send, user_now, profile.profile_type)
        else:
            logger.info("Not sending sales")

    @classmethod
    def send_email(cls, email, email_type, onboarding):
        subject = cls.ONBOARD_DATA[email_type]['subject']
        template_name = cls.ONBOARD_DATA[email_type]['template']
        ctx = {
            'onboard_id': onboarding.id
        }
        html_message = render_to_string("onboarding/{}".format(template_name), ctx)
        message = strip_tags(html_message)
        to = [email]
        header_content = {
            "campaign_id": "onboarding",
            "tags": ["onboarding", email_type]
        }
        mail = EmailMultiAlternatives(subject, message, EMAIL_FROM, to,
                                      headers={
                                          'X-MSYS-API': json.dumps(header_content)
                                      })
        mail.attach_alternative(html_message, 'text/html')
        return mail.send(fail_silently=False)


class Command(BaseCommand):
    help = "Sending onboarding, sales and trial expiring emails"

    def handle(self, *args, **options):
        for profile in Profile.objects.all():
            try:
                user_now = user_time_now(profile.utc_offset)
                email = profile.account.user.email
                onboarding = OnboardEvents.objects.filter(user=profile).first()
                if not onboarding:
                    onboarding = OnboardEvents.objects.create(user=profile)
                    profile.trial_end_time = datetime.datetime.utcnow().date() + datetime.timedelta(days=20)
                    profile.save()
                    logger.info("Creating onboarding object for {} and extending trial to {}".format(email, profile.trial_end_time.isoformat()))
                if onboarding.onboard_canceled:
                    if not onboarding.sales_canceled and profile.is_trial():
                        OnboardSender.send_sales(profile, onboarding, user_now)
                elif onboarding.onboard_finished:
                    if profile.is_trial():
                        OnboardSender.send_sales(profile, onboarding, user_now)
                else:
                    OnboardSender.onboard_user(profile, onboarding, user_now)
            except Exception as e:
                print("error onboarding user ", profile.account.user.email)
                print(e)
