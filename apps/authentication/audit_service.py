from datetime import datetime, timezone

from .audit_repository import AuditLogRepository


class AuditLogService:
    def __init__(self):
        self.repository = AuditLogRepository()

    def log(
        self,
        request,
        action,
        description="",
        target_type=None,
        target_id=None,
    ):
        user_id = request.session.get("user_id")
        username = request.session.get("username")
        role = request.session.get("role")

        log_data = {
            "userId": user_id,
            "username": username,
            "role": role,
            "action": action,
            "description": description,
            "targetType": target_type,
            "targetId": target_id,
            "ipAddress": self.get_client_ip(request),
            "createdAt": datetime.now(timezone.utc),
        }

        return self.repository.create(log_data)

    @staticmethod
    def get_client_ip(request):
        forwarded_for = request.META.get(
            "HTTP_X_FORWARDED_FOR"
        )

        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        return request.META.get(
            "REMOTE_ADDR"
        )