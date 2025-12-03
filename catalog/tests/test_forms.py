import datetime
from django.test import TestCase
from django.utils import timezone

from catalog.forms import RenewBookModelForm


class RenewBookFormTest(TestCase):

    def test_renew_form_date_field_label(self):
        """Test that the label of due_back is correct."""
        form = RenewBookModelForm()
        self.assertTrue(
            form.fields['due_back'].label is None or form.fields['due_back'].label == 'Renewal date'
        )

    def test_renew_form_date_field_help_text(self):
        """Test that the help_text of due_back is correct."""
        form = RenewBookModelForm()
        self.assertEqual(
            form.fields['due_back'].help_text,
            'Enter a date between now and 4 weeks (default 3).'
        )

    def test_renew_form_date_in_past(self):
        """Test that a past date is invalid."""
        date = datetime.date.today() - datetime.timedelta(days=1)
        form = RenewBookModelForm(data={'due_back': date})
        self.assertFalse(form.is_valid())

    def test_renew_form_date_too_far_in_future(self):
        """Test that a date more than 4 weeks ahead is invalid."""
        date = datetime.date.today() + datetime.timedelta(weeks=4) + datetime.timedelta(days=1)
        form = RenewBookModelForm(data={'due_back': date})
        self.assertFalse(form.is_valid())

    def test_renew_form_date_today(self):
        """Test that today's date is valid."""
        date = datetime.date.today()
        form = RenewBookModelForm(data={'due_back': date})
        self.assertTrue(form.is_valid())

    def test_renew_form_date_max(self):
        """Test that the max allowed date (4 weeks from today) is valid."""
        date = datetime.date.today() + datetime.timedelta(weeks=4)
        form = RenewBookModelForm(data={'due_back': date})
        self.assertTrue(form.is_valid())
