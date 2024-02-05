from django.contrib import admin
from .models import OptimizerData, OptimizerFile

# Register your models here.
admin.site.register(OptimizerData)
admin.site.register(OptimizerFile)
