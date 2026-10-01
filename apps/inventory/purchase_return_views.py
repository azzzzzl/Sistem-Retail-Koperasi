from django.contrib import messages
from django.shortcuts import render, redirect
from apps.authentication.decorators import permission_required_custom
from apps.authentication.audit_service import AuditLogService
from apps.master_data.services import MasterDataService
from .purchase_return_service import PurchaseReturnService
from .purchase_services import PurchaseService

service=PurchaseReturnService()
purchase_service=PurchaseService()
master=MasterDataService()

@permission_required_custom("return_management")
def purchase_return_list(request):
    return render(request,"inventory/purchase_returns.html",{"returns":service.repository.find_all()})

@permission_required_custom("return_management")
def purchase_return_create(request):
    purchases=purchase_service.get_all_purchases()
    selected_id=request.POST.get("purchase_id") or request.GET.get("purchase_id")
    purchase=purchase_service.get_purchase_by_id(selected_id) if selected_id else None
    if request.method=="POST" and request.POST.get("confirm_return"):
        try:
            items=[]
            for idx,item in enumerate((purchase or {}).get("items",[])):
                qty=int(request.POST.get(f"qty_{idx}",0))
                if qty: items.append({"productId":item.get("productId"),"quantity":qty})
            ret=service.create_return(request.POST.get("return_number",""),selected_id,items,request.POST.get("reason",""),request.session.get("user_id"))
            AuditLogService().log(request,"CREATE","Retur pembelian dibuat.","purchase_return",str(ret["_id"]),module="returns",reference_id=str(ret["_id"]),after=ret)
            messages.success(request,"Retur pembelian diajukan dan menunggu approval.")
            return redirect("inventory_ui:purchase_return_list")
        except Exception as exc: messages.error(request,str(exc))
    elif request.method=="POST" and not purchase:
        messages.error(request,"Pembelian tidak ditemukan.")
    return render(request,"inventory/purchase_return_form.html",{"purchases":purchases,"purchase":purchase})

@permission_required_custom("return_management")
def purchase_return_approve(request, return_id):
    if request.method!="POST": return redirect("inventory_ui:purchase_return_list")
    try:
        ret=service.approve(return_id,request.session.get("user_id")); AuditLogService().log(request,"APPROVE","Retur pembelian disetujui dan stok dikurangi.","purchase_return",return_id,module="returns",reference_id=return_id,after=ret); messages.success(request,"Retur pembelian disetujui.")
    except Exception as exc: messages.error(request,str(exc))
    return redirect("inventory_ui:purchase_return_list")
