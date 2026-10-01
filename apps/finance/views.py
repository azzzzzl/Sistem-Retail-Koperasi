from datetime import datetime, timezone

from django.contrib import messages
from django.shortcuts import redirect, render

from apps.authentication.decorators import permission_required_custom
from apps.authentication.audit_service import AuditLogService

from .services import ExpenseService

service = ExpenseService()


@permission_required_custom("expenses")
def expense_list(request):
    expenses = service.list()
    for expense in expenses:
        expense["id"] = str(expense["_id"])
    return render(request, "finance/expenses.html", {"expenses": expenses})


@permission_required_custom("expenses")
def expense_create(request):
    if request.method == "POST":
        try:
            date_value = request.POST.get("date") or None
            date = datetime.strptime(date_value, "%Y-%m-%d").replace(tzinfo=timezone.utc) if date_value else None
            expense = service.create(
                request.POST.get("expense_number", "").strip(), date,
                request.POST.get("category", "Operasional lainnya"),
                request.POST.get("description", "").strip(),
                request.POST.get("amount", "0"), request.POST.get("payment_method", "CASH"),
                request.POST.get("reference_number", "").strip(), request.session.get("user_id"),
            )
            AuditLogService().log(request, "CREATE", f"Pengeluaran {expense['expenseNumber']} dibuat.",
                                  "expense", str(expense["_id"]), module="finance", reference_id=str(expense["_id"]), after=expense)
            messages.success(request, "Pengeluaran berhasil dicatat.")
            return redirect("finance:expenses")
        except Exception as exc:
            messages.error(request, str(exc))
    return render(request, "finance/expense_form.html", {"categories": sorted(service.CATEGORIES), "payment_methods": sorted(service.PAYMENT_METHODS)})


@permission_required_custom("expenses")
def expense_detail(request, expense_id):
    expense = service.get(expense_id)
    if not expense:
        messages.error(request, "Pengeluaran tidak ditemukan.")
        return redirect("finance:expenses")
    expense["id"] = str(expense["_id"])
    return render(request, "finance/expense_detail.html", {"expense": expense})


@permission_required_custom("expenses")
def expense_edit(request, expense_id):
    expense = service.get(expense_id)
    if not expense:
        messages.error(request, "Pengeluaran tidak ditemukan.")
        return redirect("finance:expenses")
    if request.method == "POST":
        try:
            before = dict(expense)
            updated = service.update(expense_id, {
                "category": request.POST.get("category", expense.get("category")),
                "description": request.POST.get("description", "").strip(),
                "amount": request.POST.get("amount", "0"),
                "paymentMethod": request.POST.get("payment_method", expense.get("paymentMethod")),
                "referenceNumber": request.POST.get("reference_number", "").strip(),
            })
            if not updated:
                raise ValueError("Pengeluaran tidak ditemukan.")
            AuditLogService().log(request, "UPDATE", f"Pengeluaran {expense.get('expenseNumber')} diperbarui.",
                                  "expense", expense_id, module="finance", reference_id=expense_id, before=before, after=updated)
            messages.success(request, "Pengeluaran diperbarui.")
            return redirect("finance:expense_detail", expense_id=expense_id)
        except Exception as exc:
            messages.error(request, str(exc))
    return render(request, "finance/expense_form.html", {"expense": expense, "categories": sorted(service.CATEGORIES), "payment_methods": sorted(service.PAYMENT_METHODS)})
