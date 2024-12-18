from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.views import View
from django.apps import apps
from django.contrib.auth import get_user_model
from django.conf import settings
import jwt

import json

@method_decorator(csrf_exempt, name='dispatch')
class ModelAPI(View):
    def get(self, request, app_label, model_name, object_id, field_name):
        model = apps.get_model(app_label, model_name)
        try:
            instance = model.objects.get(pk=object_id)
            field_value = getattr(instance, field_name)
            data = {
                field_name: field_value
            }
            return JsonResponse(data)
        except model.DoesNotExist:
            return JsonResponse({"error": "Object not found"}, status=404)

    def post(self, request, app_label, model_name, object_id, field_name):
        model = apps.get_model(app_label, model_name)
        instance = model.objects.get(pk=object_id)
        try:
            data = json.loads(request.body)
            field_value = data.get(field_name)
        except ValueError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        if field_value is None or field_value == '':
            return JsonResponse({'error': 'Field value cannot be empty'}, status=400)

        if field_name and hasattr(instance, field_name):
            setattr(instance, field_name, field_value)
            instance.save(update_fields=[field_name])
            return JsonResponse({field_name: getattr(instance, field_name)})

        return JsonResponse({'error': 'Field not found or invalid data'}, status=400)


class AuthModelAPI(ModelAPI):

    def get(self, request, app_label, model_name, object_id, field_name):
        auth_header = request.headers.get("Authorization")
        if auth_header != '':
            token = auth_header.split(" ")[1] if " " in auth_header else auth_header
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            print(payload.token)
            user = get_user_model().objects.get(token=payload.token)
            if user:
                return super().get(request, app_label, model_name, object_id, field_name)
        return JsonResponse({field_name: 'No valid access'})

    def post(self, request, app_label, model_name, object_id, field_name):
        auth_header = request.headers.get("Authorization")
        if auth_header != '':
            token = auth_header.split(" ")[1] if " " in auth_header else auth_header
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user = get_user_model().objects.get(token=payload.token)
            if user:
                return super().post(request, app_label, model_name, object_id, field_name)
        return JsonResponse({field_name: 'No valid access'})
