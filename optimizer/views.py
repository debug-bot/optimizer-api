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
from .data.filter import filter_data
from .data.constraints import constraints_data
from .data.esg_constraints import esg_constraints_data
from .data.result import result_data
from .data.summary import summary_data
from rest_framework.decorators import action


class OptimizerFileViewSet(generics.CreateAPIView, generics.RetrieveAPIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = (permissions.IsAuthenticated,)
    # authentication_classes = []
    serializer_class = OptimizerFileSerializer

    def post(self, request):
        """This method is used to Make POST requests to save a file in the media folder"""
        file_serializer = self.get_serializer(
            OptimizerFile.objects.filter(user=request.user).first(), data=request.data
        )
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

            # Normalize column names
            data_frame.columns = [
                col.lower().replace(" ", "_") for col in data_frame.columns
            ]

            # Search
            search_query = request.GET.get("search")
            if search_query:
                data_frame = data_frame[
                    data_frame.apply(
                        lambda row: row.astype(str).str.contains(search_query).any(),
                        axis=1,
                    )
                ]

            # Ordering
            ordering_field = request.GET.get("ordering")
            if ordering_field:
                ascending = True if ordering_field[0] != "-" else False
                ordering_field = ordering_field.strip("-")
                data_frame = data_frame.sort_values(
                    ordering_field, ascending=ascending
                )

            # Pagination
            total_count = len(data_frame)
            per_page = int(request.GET.get("per_page", 10))
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


class FieldsViewSet(viewsets.ViewSet):
    @swagger_auto_schema(method="get", responses={200: "Success"})
    @action(detail=False, methods=["get"])
    def filter_api(self, request):
        data = filter_data
        return Response(data, status=status.HTTP_200_OK)

    @swagger_auto_schema(method="get", responses={200: "Success"})
    @action(detail=False, methods=["get"])
    def constraints_api(self, request):
        data = constraints_data
        return Response(data, status=status.HTTP_200_OK)

    @swagger_auto_schema(method="get", responses={200: "Success"})
    @action(detail=False, methods=["get"])
    def esg_constraints_api(self, request):
        data = esg_constraints_data
        return Response(data, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(method="get", responses={200: "Success"})
    @action(detail=False, methods=["get"])
    def result_api(self, request):
        data = result_data
        return Response(data, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(method="get", responses={200: "Success"})
    @action(detail=False, methods=["get"])
    def summary_api(self, request):
        data = summary_data
        return Response(data, status=status.HTTP_200_OK)

    @swagger_auto_schema(method="post", responses={200: "Success"})
    @action(detail=False, methods=["post"])
    def run_optimizer(self, request):
        data = request.data
        print(data)
        return Response(data, status=status.HTTP_200_OK)
