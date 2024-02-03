from django.db import models

# Create your models here.


class OptimizerFile(models.Model):
    user = models.OneToOneField("auth.User", on_delete=models.CASCADE)
    file = models.FileField(
        upload_to="files/", null=True, verbose_name="Optimizer File"
    )
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        try:
            return self.user.username + " - " + self.file.name
        except:
            return self.user.username + " - No File Uploaded"

class OptimizerData(models.Model):
    file = models.ForeignKey(OptimizerFile, on_delete=models.CASCADE)
    metrics = models.JSONField(null=True) 
    buffers = models.JSONField(null=True)
    filters_metrics = models.JSONField(null=True)
    filters_groups = models.JSONField(null=True)
    sectors = models.JSONField(null=True)
    seniorities = models.JSONField(null=True)
    ratings = models.JSONField(null=True)
    esg_ratings = models.JSONField(null=True)
    countries = models.JSONField(null=True)
    maturities = models.JSONField(null=True)
    tickers = models.JSONField(null=True)
    comparison = models.JSONField(null=True)
    history = models.JSONField(null=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        try:
            return self.file.user.username + " - " + self.file.file.name
        except:
            return self.file.user.username + " - No File Uploaded"
    
