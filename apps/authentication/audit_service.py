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
        module=None,
        reference_id=None,
        before=None,
        after=None,
    ):
        user_id = request.session.get("user_id")
        username = request.session.get("username")
        role = request.session.get("role")
        normalized_action = str(action or "OTHER").upper()
        normalized_module = module or self._module_from_target(target_type)
        reference = reference_id if reference_id is not None else target_id

        log_data = {
            "userId": user_id,
            "username": username,
            "role": role,
            "action": normalized_action,
            "module": normalized_module,
            "referenceId": str(reference) if reference is not None else None,
            "description": description,
            "before": before,
            "after": after,
            "ipAddress": self.get_client_ip(request),
            "createdAt": datetime.now(timezone.utc),
            # Backward-compatible aliases for older records/UI.
            "targetType": target_type,
            "targetId": target_id,
        }
        return self.repository.create(log_data)

    @staticmethod
    def _module_from_target(target_type):
        value = str(target_type or "general").lower()
        mapping = {
            "user": "authentication",
            "product": "master_data",
            "supplier": "master_data",
            "member": "master_data",
            "category": "master_data",
            "product_supplier": "master_data",
            "sale": "sales",
            "sales_return": "returns",
            "purchase": "procurement",
            "purchase_order": "procurement",
            "goods_receipt": "procurement",
            "invoice": "procurement",
            "supplier_payment": "procurement",
            "stock": "inventory",
            "stock_adjustment": "inventory",
            "stock_opname": "inventory",
            "expense": "finance",
            "purchase_return": "returns",
        }
        return mapping.get(value, value or "general")

    @staticmethod
    def get_client_ip(request):
        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")
