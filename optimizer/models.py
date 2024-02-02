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

