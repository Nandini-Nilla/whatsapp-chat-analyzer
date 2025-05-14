from django.contrib import admin
from django.urls import path, include
from analyzer.views import home, upload_chat  # Import the views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('upload/', upload_chat, name='upload_chat'),  # Existing upload URL
    path('', home, name='home'),  # Root URL points to home view
]