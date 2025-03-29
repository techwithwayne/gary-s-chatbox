from django.db import models

class StoreInfo(models.Model):
    hours = models.CharField(max_length=255)
    phone = models.CharField(max_length=50)
    address = models.CharField(max_length=255)
    services = models.TextField(help_text="Enter services separated by commas")
    flyer_url = models.URLField()

    def __str__(self):
        return "Gary's Foods Store Info"

class ConversationLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    user_message = models.TextField()
    bot_reply = models.TextField()

    def __str__(self):
        return f"[{self.timestamp}] {self.user_message[:50]}..."