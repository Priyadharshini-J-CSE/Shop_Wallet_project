from django.contrib import admin
from .models import Wallet

# Register your models here.
@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance')
    list_filter = ('user',)
    search_fields = ('user__username',)
