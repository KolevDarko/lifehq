from mastermind.utils import user_time_now


def user_first_letter(request):
    if 'user_letter' not in request.session:
        profile = request.user.account.profile
        first_letter = str(profile.name[0]).upper()
        request.session['user_letter'] = first_letter
    return request.session['user_letter']

def get_success_context(request):
    empty_success = {
        'valid': False,
        'total_score': 0,
        'rev_total_score': 100,
        'journals': {
            'score': 0,
            'rev_score': 100,
            'todo': 0,
            'done': 0
        },
        'habits': {
            'score': 0,
            'rev_score': 100,
            'todo': 0,
            'done': 0
        },
        'work': {
            'score': 0,
            'rev_score': 100,
            'todo': 0,
            'done': 0
        },
    }
    if 'success_data' in request.session:
        if not request.session['success_data']['valid']:
            request.session['success_data'] = empty_success
            context = empty_success
        else:
            profile = request.user.account.profile
            profile_today = user_time_now(profile.utc_offset).date().isoformat()
            if request.session['success_data']['date'] != profile_today:
                request.session['success_data'] = empty_success
                context = empty_success
            else:
                context = request.session['success_data']
    else:
        request.session['success_data'] = empty_success
        context = empty_success
    return context

def my_extra_info_processor(request):
    if not request.user.is_authenticated:
        return {}
    success_context = get_success_context(request)

    return {'day_success': success_context}
