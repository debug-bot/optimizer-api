from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework import generics, status
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .utils import file_response

from .serializers import OptimizerFileSerializer
from .models import OptimizerFile
import pandas as pd
from django.core.exceptions import ObjectDoesNotExist
from drf_yasg.utils import swagger_auto_schema
from . import swagger_params


# Create your views here.
class DeviceViewSet(viewsets.ViewSet):
    authentication_classes = []
    # permission_classes = (permissions.IsAuthenticated,)

    def list(self, request):
        parameters = ["length", "width", "instep", "modelname", "brandname"]
        for parameter in parameters:
            if parameter not in request.query_params:
                return Response(
                    {
                        "error": "{} is not present in parameters".format(parameter),
                        "solution": "length, width, instep, modelname and brandname are needed parameters",
                        "success": False,
                        "parameters": request.query_params,
                    }
                )
        return Response({"success": True, "parameters": request.query_params})


class OptimizerFileViewSet(generics.CreateAPIView, generics.RetrieveAPIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = (permissions.IsAuthenticated,)
    # authentication_classes = []
    serializer_class = OptimizerFileSerializer

    def post(self, request):
        """This method is used to Make POST requests to save a file in the media folder"""
        file_serializer = self.get_serializer(data=request.data)
        if file_serializer.is_valid():
            instance = file_serializer.save(user=request.user)
            return Response({"success": True})
        else:
            return Response(file_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, format="csv"):
        response = file_response(request)
        return response


class TableViewSet(viewsets.ViewSet):
    # authentication_classes = []
    permission_classes = (permissions.IsAuthenticated,)

    @swagger_auto_schema(manual_parameters=swagger_params.table_params)
    def list(self, request):
        try:
            # Assuming OptimizerFile contains the path to the CSV file
            file_record = OptimizerFile.objects.filter(user=request.user).first()
            if not file_record:
                return Response(
                    {"error": "File not found"}, status=status.HTTP_404_NOT_FOUND
                )

            # Read CSV file
            data_frame = pd.read_csv(file_record.file.path)

            # Replace NaN with 0
            data_frame = data_frame.fillna(0)

            print(data_frame.head())
            total_count = len(data_frame)

            # Pagination
            per_page = int(request.GET.get("per_page", 25))
            page = int(request.GET.get("page", 1))
            paginator = Paginator(data_frame.to_dict(orient="records"), per_page)

            try:
                data = paginator.page(page)
            except PageNotAnInteger:
                data = paginator.page(1)
            except EmptyPage:
                data = paginator.page(paginator.num_pages)

            return Response(
                {
                    "results": list(data),
                    "total": total_count,
                    "page": page,
                    "per_page": per_page,
                },
                status=status.HTTP_200_OK,
            )

        except ObjectDoesNotExist:
            return Response(
                {"error": "OptimizerFile object does not exist"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
