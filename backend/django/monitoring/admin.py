from django.contrib import admin
from .models import MLModel, PipelineRun, PredictionLog, Incident

admin.site.register(MLModel)
admin.site.register(PipelineRun)
admin.site.register(PredictionLog)
admin.site.register(Incident)