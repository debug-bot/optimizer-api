import mimetypes
from django.http import FileResponse
from .models import OptimizerFile
from rest_framework import  status
from rest_framework.response import Response


def file_response(request):
    instance = OptimizerFile.objects.filter(user=request.user).first()
    if not instance:
        return Response(
            {"message": "No File Found"}, status=status.HTTP_400_BAD_REQUEST
        )
    if not instance.file:
        return Response(
            {"message": "No File Found"}, status=status.HTTP_400_BAD_REQUEST
        )

    file_handle = instance.file.open()
    mimetype, _ = mimetypes.guess_type(instance.file.url)
    response = FileResponse(file_handle, content_type=mimetype)
    response["Content-Length"] = instance.file.size
    response["Content-Disposition"] = 'attachment; filename="%s"' % instance.file.name
    response["Access-Control-Expose-Headers"] = "Content-Disposition"
    return response
