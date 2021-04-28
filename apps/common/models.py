from django.db.models import Model
from hashid_field import HashidAutoField


class HashedModel(Model):

    id = HashidAutoField(primary_key=True)

    class Meta:
        abstract = True

