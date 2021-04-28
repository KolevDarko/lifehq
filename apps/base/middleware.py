import datetime

from django import urls
from django.shortcuts import redirect
from django.core.cache import cache


class TrialCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def get_profile_id(self, request):
        if 'profile_id' not in request.session:
            request.session['profile_id'] = str(request.user.account.profile.id)
        return request.session['profile_id']

    def check_plan_and_cache(self, request):
        profile_id = self.get_profile_id(request)
        billing_key = "billing:{}".format(profile_id)
        DAY = 60 * 60 * 24
        if cache.get(billing_key):
            billing_info = cache.get(billing_key)
            return billing_info['plan_valid']
        else:
            today = datetime.datetime.utcnow().date()
            profile = request.user.account.profile
            if profile.is_trial():
                if profile.trial_end_time:
                    plan_valid = profile.trial_end_time >= today
                    plan_end_time = profile.trial_end_time
                    plan_type = 'trial'
                else:
                    plan_valid = True
                    plan_end_time = datetime.datetime.utcnow() + datetime.timedelta(days=30)
                    plan_type = 'trial'
            else:
                plan_valid = self.check_plan_valid(profile.plan_end_time, today)
                plan_end_time = profile.plan_end_time
                plan_type = profile.plan_name

            cache.set(billing_key, {"plan_valid": plan_valid, "plan_end_time": plan_end_time, "plan_type": plan_type}, timeout=DAY)
            return plan_valid

    def check_plan_valid(self, plan_end_time, today):
        if not plan_end_time:
            return True
        else:
            return plan_end_time >= today

    def outside_path(self, path):
        return path in ['/logout/', '/login/', '/policy/', '/settings/']

    def __call__(self, request):
        if request.user.is_anonymous or request.user.is_staff:
            response = self.get_response(request)
            return response
        else:
            if request.path == '/billing/':
                response = self.get_response(request)
                return response
            else:
                valid = self.check_plan_and_cache(request)
                if valid or self.outside_path(request.path):
                    response = self.get_response(request)
                    return response
                else:
                    billing_url = urls.reverse('billing')
                    return redirect(billing_url)
