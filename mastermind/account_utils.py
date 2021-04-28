def expunge_account(account_delete):
    user = account_delete.user
    user.delete()
    account_delete.user = None
    account_delete.email = ""
    return True


def deactivate_account(account_delete):
    user = account_delete.user
    user.is_active = False
    user.save()
