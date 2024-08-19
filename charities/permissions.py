from rest_framework.permissions import BasePermission  

class IsBenefactor(BasePermission):  
    def has_permission(self, request, view):  
        return request.user.is_benefactor