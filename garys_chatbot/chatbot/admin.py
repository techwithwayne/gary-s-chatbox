from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import StoreInfo, ConversationLog

@admin.register(StoreInfo)
class StoreInfoAdmin(admin.ModelAdmin):
    list_display = ("address", "phone", "hours")
    fieldsets = (
        (None, {
            "fields": ("hours", "phone", "address", "flyer_url")
        }),
        ("Services Offered", {
            "fields": ("services",),
            "description": "Separate each service with a comma. Ex: Deli, Bakery, Produce"
        }),
    )
    
@admin.register(ConversationLog)
class ConversationLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "short_question", "short_response")
    list_filter = ("timestamp",)
    readonly_fields = ("timestamp", "user_message", "bot_reply")

    def short_question(self, obj):
        return obj.user_message[:50]

    def short_response(self, obj):
        return obj.bot_reply[:50]

    short_question.short_description = "User Question"
    short_response.short_description = "Bot Reply"