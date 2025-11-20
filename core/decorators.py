from functools import wraps

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


def role_required(*roles):
    """
    Decorator enforcing that the current user has one of the allowed roles.

    Example:
        @role_required(User.Roles.ADMIN, User.Roles.SUPERADMIN)
        def my_view(...):
            ...
    """

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            if roles and request.user.role not in roles:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator


class RoleRequiredMixin(LoginRequiredMixin):
    """Class-based view mixin for enforcing allowed roles."""

    required_roles = ()

    def dispatch(self, request, *args, **kwargs):
        if self.required_roles and request.user.role not in self.required_roles:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

