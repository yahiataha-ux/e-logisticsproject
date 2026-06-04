from django.utils import timezone
from apps.authentication.models import User

class ActiveUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Update last activity and IP
            now = timezone.now()
            
            # Get IP
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')
            
            # Update user fields without full save if possible for performance
            User.objects.filter(pk=request.user.pk).update(
                last_activity=now,
                last_ip=ip
            )
            
        response = self.get_response(request)
        return response
