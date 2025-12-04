
from django.db import models
from solo.models import SingletonModel

class Layout(SingletonModel):
    titulo = models.CharField(max_length=200, default="Mi sitio")
    logo = models.ImageField(upload_to="images/", null=True, blank=True)

    def __str__(self):
        return "Layout"
