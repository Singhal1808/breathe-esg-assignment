from django.contrib import admin

from .models import ActivityRecord, AuditEvent, IngestionBatch, RawRecord, Site, SourceSystem, Tenant

admin.site.register(Tenant)
admin.site.register(Site)
admin.site.register(SourceSystem)
admin.site.register(IngestionBatch)
admin.site.register(RawRecord)
admin.site.register(ActivityRecord)
admin.site.register(AuditEvent)

