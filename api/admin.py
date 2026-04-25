from django.contrib import admin

from .models import Incident, IncidentAttachment, IncidentComment, IncidentConfirmation, Location, User

admin.site.register(User)
admin.site.register(Location)
admin.site.register(Incident)
admin.site.register(IncidentAttachment)
admin.site.register(IncidentComment)
admin.site.register(IncidentConfirmation)
