from datetime import datetime, date, timedelta
from unittest import skip

from account.models import Account
from dateutil.parser import parse
from django.contrib.auth.models import User
from django.test import TestCase

from apps.base.models import Profile, ProjectTodoItem
from apps.base.views import MasterPartialPlanWeek

# from unittest import TestCase

class ProfileTest(TestCase):

    def setUp(self):
        user = User(email='kolevdarko.work@gmail.com', username='kolevdarko')
        user.set_password("testpass")
        user.pk = 1
        user.save()
        account = Account(user_id=1)
        account.pk = 1
        account.save()
        self.profile = Profile(name='Dare', account_id=1)
        self.profile.save()

    def payment_succeeded_data(self):
        return {
            "alert_name": "subscription_payment_succeeded",
            "balance_currency": "GBP",
            "balance_earnings": "738.19",
            "balance_fee": "490.12",
            "balance_gross": "196.71",
            "balance_tax": "238.44",
            "checkout_id": "3-c1e7491fe340689-fd6c94d407",
            "country": "FR",
            "coupon": "Coupon 3",
            "currency": "GBP",
            "customer_name": "customer_name",
            "earnings": "992.7",
            "email": "egaylord@example.org",
            "event_time": "2019-02-12 05:55:45",
            "fee": "0.17",
            "initial_payment": "false",
            "instalments": "9",
            "marketing_consent": "",
            "next_bill_date": "2019-02-15",
            "order_id": "5",
            "passthrough": "Example String",
            "payment_method": "card",
            "payment_tax": "0.32",
            "plan_name": "Example String",
            "quantity": "93",
            "receipt_url": "https://my.paddle.com/receipt/5/e664802f445d050-93e9e0d73d",
            "sale_gross": "972.04",
            "status": "active",
            "subscription_id": "6",
            "subscription_plan_id": "5",
            "unit_price": "unit_price",
            "user_id": "9"
        }

    def subscription_created_data(self):
        return {
            "alert_name": "subscription_created",
            "cancel_url": "https://checkout.paddle.com/subscription/cancel?user=2&subscription=3&hash=78ab3a8a5d6cdcd22958c28844c8eb6a18fbc2db",
            "checkout_id": "9-c0f707892c9ffec-09ecb03593",
            "currency": "EUR",
            "email": "uwisoky@example.net",
            "event_time": "2019-02-12 06:14:18",
            "marketing_consent": "1",
            "next_bill_date": "2019-03-13",
            "passthrough": "Example String",
            "quantity": "90",
            "status": "trialing",
            "subscription_id": "9",
            "subscription_plan_id": "4",
            "unit_price": "unit_price",
            "update_url": "https://checkout.paddle.com/subscription/update?user=6&subscription=8&hash=941965f12cb0f4a10f2e5fc4a5cf56143f8c9049",
        }

    @skip("Dont want it")
    def test_subscription_created(self):
        self.profile.update_payment_status(self.subscription_created_data())
        self.assertEqual(self.profile.subscription_status, "trialing")
        self.assertEqual(self.profile.subscription_id, "9")
        self.assertEqual(self.profile.subscription_plan_id, "4")
        self.assertEqual(self.profile.update_url, "https://checkout.paddle.com/subscription/update?user=6&subscription=8&hash=941965f12cb0f4a10f2e5fc4a5cf56143f8c9049")
        self.assertEqual(self.profile.cancel_url, "https://checkout.paddle.com/subscription/cancel?user=2&subscription=3&hash=78ab3a8a5d6cdcd22958c28844c8eb6a18fbc2db")

    @skip("Dont want it")
    def test_subscription_payment_succeeded(self):
        self.profile.update_payment_status(self.payment_succeeded_data())
        self.assertEqual(self.profile.subscription_status, "active")
        self.assertEqual(self.profile.next_bill_date, parse("2019-02-15"))
        self.assertEqual(self.profile.subscription_last_event, parse("2019-02-12 05:55:45"))

class TestMasterPartialPlanWeek(TestCase):

    def create_tasks_full(self):
        all_tasks = []
        all_tasks.append(ProjectTodoItem(title='MOnday', due_date=datetime(2019, 9, 23)))
        all_tasks.append(ProjectTodoItem(title='Tuesday', due_date=datetime(2019, 9, 24)))
        all_tasks.append(ProjectTodoItem(title='Wed', due_date=datetime(2019, 9, 25)))
        all_tasks.append(ProjectTodoItem(title='THU', due_date=datetime(2019, 9, 26)))
        all_tasks.append(ProjectTodoItem(title='FRI', due_date=datetime(2019, 9, 27)))
        all_tasks.append(ProjectTodoItem(title='Sat', due_date=datetime(2019, 9, 28)))
        all_tasks.append(ProjectTodoItem(title='Sun', due_date=datetime(2019, 9, 29, 13, 30)))
        return all_tasks

    def tasks_with_gaps(self):
        all_tasks = []
        all_tasks.append(ProjectTodoItem(title='Tuesday', due_date=datetime(2019, 9, 24, 16)))
        all_tasks.append(ProjectTodoItem(title='THU', due_date=datetime(2019, 9, 26)))
        all_tasks.append(ProjectTodoItem(title='FRI', due_date=datetime(2019, 9, 27)))
        all_tasks.append(ProjectTodoItem(title='Saturday', due_date=datetime(2019, 9, 28, 12)))
        all_tasks.append(ProjectTodoItem(title='Second Saturday', due_date=datetime(2019, 9, 28, 13)))
        return all_tasks

    @skip("Dont want it")
    def test_group_by_day(self):
        str_offset = '2'
        week_tasks = self.create_tasks_full()
        rezult = MasterPartialPlanWeek.group_by_day(week_tasks, str_offset)
        self.assertEqual(len(rezult[0]), 1)
        self.assertEqual(rezult[0][0].title, 'MOnday')
        self.assertEqual(rezult[1][0].title, 'Tuesday')
        self.assertEqual(rezult[2][0].title, 'Wed')
        self.assertEqual(rezult[4][0].title, 'FRI')
        self.assertEqual(rezult[6][0].title, 'Sun')
        self.assertEqual(len(rezult), 7)

        rezult = MasterPartialPlanWeek.group_by_day(self.tasks_with_gaps(), str_offset)
        self.assertEqual(rezult[0], [])
        self.assertEqual(rezult[1][0].title, 'Tuesday')
        self.assertEqual(rezult[2], [])
        self.assertEqual(rezult[5][0].title, 'Saturday')
        self.assertEqual(rezult[5][1].title, 'Second Saturday')
        self.assertEqual(rezult[6], [])


    def test_create_day_lists(self):
        empty_tasks_grouped = []
        for i in range(7):
            empty_tasks_grouped.append(list())
        today = date.today()
        day_lists = MasterPartialPlanWeek.create_day_lists(empty_tasks_grouped, today)
        today_shortname = today.strftime("%A")[:3]
        next_shortname = (today + timedelta(days=1)).strftime("%A")[:3]
        self.assertEqual(day_lists[0].title, today_shortname)
        self.assertEqual(day_lists[1].title, next_shortname)
