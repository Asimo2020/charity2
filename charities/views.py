from rest_framework import status, generics
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status  
from .serializers import BenefactorSerializer  
from .models import Task  
from .permissions import IsCharity  

from accounts.permissions import IsCharityOwner, IsBenefactor
from charities.models import Task
from charities.serializers import (
    TaskSerializer, CharitySerializer, BenefactorSerializer
)


class BenefactorRegistration(APIView):
    permission_classes = [IsAuthenticated]  

    def post(self, request):  
        serializer = BenefactorSerializer(data=request.data, context={'request': request})  
        if serializer.is_valid():  
            serializer.save()  
            return Response(serializer.data, status=status.HTTP_201_CREATED)  
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)  


class CharityRegistration(APIView):
    pass


class Tasks(generics.ListCreateAPIView):
    serializer_class = TaskSerializer

    def get_queryset(self):
        return Task.objects.all_related_tasks_to_user(self.request.user)

    def post(self, request, *args, **kwargs):
        data = {
            **request.data,
            "charity_id": request.user.charity.id
        }
        serializer = self.serializer_class(data = data)
        serializer.is_valid(raise_exception = True)
        serializer.save()
        return Response(serializer.data, status = status.HTTP_201_CREATED)

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            self.permission_classes = [IsAuthenticated, ]
        else:
            self.permission_classes = [IsCharityOwner, ]

        return [permission() for permission in self.permission_classes]

    def filter_queryset(self, queryset):
        filter_lookups = {}
        for name, value in Task.filtering_lookups:
            param = self.request.GET.get(value)
            if param:
                filter_lookups[name] = param
        exclude_lookups = {}
        for name, value in Task.excluding_lookups:
            param = self.request.GET.get(value)
            if param:
                exclude_lookups[name] = param

        return queryset.filter(**filter_lookups).exclude(**exclude_lookups)


class TaskRequest(APIView):  
    permission_classes = [IsBenefactor]  

    def get(self, request, task_id):  
        try:  
            task = Task.objects.get(id=task_id)  
        except Task.DoesNotExist:  
            return Response({'detail': 'Task not found.'}, status=status.HTTP_404_NOT_FOUND)  

        if task.state != 'PENDING':  
            return Response({'detail': 'This task is not pending.'}, status=status.HTTP_404_NOT_FOUND)  

        task.state = 'WAITING'  
        task.save()  
        task.assign_to_user(request.user)  

        return Response({'detail': 'Request sent.'}, status=status.HTTP_200_OK)


class TaskResponse(APIView):
    permission_classes = [IsCharity]  

    def post(self, request, task_id):  
        try:  
            task = Task.objects.get(id=task_id)  
        except Task.DoesNotExist:  
            return Response({'detail': 'Task not found.'}, status=status.HTTP_404_NOT_FOUND)  

        if task.state != 'WAITING':  
            return Response({'detail': 'This task is not waiting.'}, status=status.HTTP_404_NOT_FOUND)  

        response = request.data.get('response')  
        if response not in ['A', 'R']:  
            return Response({'detail': 'Required field ("A" for accepted / "R" for rejected)'}, status=status.HTTP_400_BAD_REQUEST)  

        if response == 'A':  
            task.state = 'ASSIGNED'  
        else:  
            task.state = 'PENDING'  
            task.assigned_benefactor = None  
        task.save()  

        return Response({'detail': 'Response sent.'}, status=status.HTTP_200_OK)  


class DoneTask(APIView):
    permission_classes = [IsCharity]  

    def post(self, request, task_id):  
        try:  
            task = Task.objects.get(id=task_id)  
        except Task.DoesNotExist:  
            return Response({'detail': 'Task not found.'}, status=status.HTTP_404_NOT_FOUND)  

        if task.state != 'ASSIGNED':  
            return Response({'detail': 'Task is not assigned yet.'}, status=status.HTTP_404_NOT_FOUND)  

        task.state = 'DONE'  
        task.save()  

        return Response({'detail': 'Task has been done successfully.'}, status=status.HTTP_200_OK)  