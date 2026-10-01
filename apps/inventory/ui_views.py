from datetime import datetime, timezone
import uuid

from django.contrib import messages
from django.shortcuts import render, redirect

from apps.authentication.decorators import permission_required_custom
from apps.authentication.audit_service import AuditLogService
from apps.master_data.services import MasterDataService
from .po_services import PurchaseOrderService
from .gr_services import GoodsReceiptService
from .purchase_services import PurchaseService
from .invoice_services import SupplierInvoiceService
from .payment_services import SupplierPaymentService
from .opname_services import StockOpnameService
from .adjustment_services import StockAdjustmentService
from .services import StockMovementService
from .purchase_return_views import purchase_return_list, purchase_return_create, purchase_return_approve

master = MasterDataService()
po_service = PurchaseOrderService()
gr_service = GoodsReceiptService()
purchase_service = PurchaseService()
invoice_service = SupplierInvoiceService()
payment_service = SupplierPaymentService()
opname_service = StockOpnameService()
adjustment_service = StockAdjustmentService()
stock_service = StockMovementService()


def _safe_date(value):
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def _num(value, default=0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


@permission_required_custom("inventory")
def inventory_home(request):
    products = master.search_products(status="active")
    movements = stock_service.get_all_movements()[:50]
    return render(request, "inventory/index.html", {"products": products, "movements": movements})


@permission_required_custom("inventory")
def stock_movement_list_ui(request):
    movements = stock_service.get_all_movements()[:200]
    return render(request, "inventory/movements.html", {"movements": movements})


@permission_required_custom("inventory")
def stock_opname_list_ui(request):
    opnames = opname_service.get_all_opnames()
    return render(request, "inventory/stock_opname.html", {"opnames": opnames})


@permission_required_custom("inventory")
def stock_opname_create_ui(request):
    products = master.search_products(status="active")
    if request.method == "POST":
        try:
            items=[]
            for i,p in enumerate(products):
                physical=request.POST.get(f"physical_{i}","").strip()
                if physical != "": items.append({"productId":str(p["_id"]),"physicalStock":int(physical),"notes":request.POST.get(f"notes_{i}","")})
            result=opname_service.create_opname(request.POST.get("opname_number",f"OP-{uuid.uuid4().hex[:8].upper()}"),items,request.session.get("user_id"))
            AuditLogService().log(request,"CREATE","Stock opname dibuat.","stock_opname",str(result["_id"]),module="inventory",reference_id=str(result["_id"]),after=result)
            messages.success(request,"Stock opname dibuat."); return redirect("inventory_ui:stock_opname_list")
        except Exception as exc: messages.error(request,str(exc))
    return render(request,"inventory/stock_opname_form.html",{"products":products})


@permission_required_custom("inventory")
def stock_opname_submit_ui(request, opname_id):
    if request.method=="POST":
        try: opname_service.submit_opname(opname_id); messages.success(request,"Stock opname disubmit.")
        except Exception as exc: messages.error(request,str(exc))
    return redirect("inventory_ui:stock_opname_list")


@permission_required_custom("inventory")
def stock_opname_approve_ui(request, opname_id):
    if request.method=="POST":
        try:
            result=opname_service.approve_opname(opname_id,request.session.get("user_id")); AuditLogService().log(request,"APPROVE","Stock opname disetujui dan penyesuaian stok diterapkan.","stock_opname",opname_id,module="inventory",reference_id=opname_id,after=result); messages.success(request,"Stock opname disetujui.")
        except Exception as exc: messages.error(request,str(exc))
    return redirect("inventory_ui:stock_opname_list")


@permission_required_custom("inventory")
def stock_adjustment_list_ui(request):
    adjustments=adjustment_service.get_all_adjustments()
    return render(request,"inventory/adjustments.html",{"adjustments":adjustments})


@permission_required_custom("inventory")
def stock_adjustment_create_ui(request):
    products=master.search_products(status="active")
    if request.method=="POST":
        try:
            result=adjustment_service.create_adjustment(request.POST.get("adjustment_number",f"ADJ-{uuid.uuid4().hex[:8].upper()}"),request.POST.get("product_id"),request.POST.get("adjustment_type"),request.POST.get("quantity"),request.POST.get("reason",""),request.POST.get("notes",""),request.session.get("user_id"))
            AuditLogService().log(request,"STOCK_ADJUSTMENT","Stock adjustment dibuat.","stock_adjustment",str(result["_id"]),module="inventory",reference_id=str(result["_id"]),after=result)
            messages.success(request,"Stock adjustment berhasil."); return redirect("inventory_ui:stock_adjustment_list")
        except Exception as exc: messages.error(request,str(exc))
    return render(request,"inventory/adjustment_form.html",{"products":products})


@permission_required_custom("procurement")
def purchase_order_list_ui(request):
    return render(request,"inventory/purchase_orders.html",{"purchase_orders":po_service.get_all_purchase_orders()})


@permission_required_custom("procurement")
def purchase_order_create_ui(request):
    suppliers=master.search_suppliers(status="active"); products=master.search_products(status="active")
    if request.method=="POST":
        try:
            items=[]
            for i,p in enumerate(products):
                q=request.POST.get(f"qty_{i}","").strip()
                if q and _num(q)>0:
                    items.append({"productId":str(p["_id"]),"name":p.get("name",""),"quantity":int(q),"purchasePrice":_num(request.POST.get(f"price_{i}",p.get("purchase_price",0)))})
            result=po_service.create_purchase_order(request.POST.get("po_number",f"PO-{uuid.uuid4().hex[:8].upper()}"),request.POST.get("supplier_id"),_safe_date(request.POST.get("order_date")),items,_num(request.POST.get("discount",0)),request.POST.get("notes",""),request.session.get("user_id"))
            AuditLogService().log(request,"CREATE","Purchase Order dibuat.","purchase_order",str(result["_id"]),module="procurement",reference_id=str(result["_id"]),after=result); messages.success(request,"PO berhasil dibuat."); return redirect("inventory_ui:purchase_order_list")
        except Exception as exc: messages.error(request,str(exc))
    return render(request,"inventory/purchase_order_form.html",{"suppliers":suppliers,"products":products})


@permission_required_custom("procurement")
def purchase_order_detail_ui(request, po_id):
    po=po_service.get_purchase_order_by_id(po_id)
    if not po: messages.error(request,"PO tidak ditemukan."); return redirect("inventory_ui:purchase_order_list")
    return render(request,"inventory/purchase_order_detail.html",{"po":po})


@permission_required_custom("procurement")
def purchase_order_action_ui(request, po_id, action):
    if request.method!="POST": return redirect("inventory_ui:purchase_order_detail",po_id=po_id)
    try:
        if action=="submit": result=po_service.submit_purchase_order(po_id)
        elif action=="approve": result=po_service.approve_purchase_order(po_id,request.session.get("user_id"))
        elif action=="cancel": result=po_service.cancel_purchase_order(po_id)
        else: raise ValueError("Aksi PO tidak valid.")
        AuditLogService().log(request,action.upper(),f"PO {po_id} diproses dengan aksi {action}.","purchase_order",po_id,module="procurement",reference_id=po_id,after=result); messages.success(request,"PO berhasil diproses.")
    except Exception as exc: messages.error(request,str(exc))
    return redirect("inventory_ui:purchase_order_detail",po_id=po_id)


@permission_required_custom("goods_receipt")
def goods_receipt_list_ui(request):
    return render(request,"inventory/goods_receipts.html",{"receipts":gr_service.get_all_goods_receipts(),"pos":po_service.get_all_purchase_orders()})


@permission_required_custom("goods_receipt")
def goods_receipt_create_ui(request):
    pos=[p for p in po_service.get_all_purchase_orders() if p.get("status") in {"APPROVED","PARTIAL"}]
    selected=request.POST.get("po_id") or request.GET.get("po_id")
    po=po_service.get_purchase_order_by_id(selected) if selected else None
    if request.method=="POST" and po and request.POST.get("submit_receipt"):
        try:
            items=[]
            for i,item in enumerate(po.get("items",[])):
                received=int(request.POST.get(f"received_{i}",0)); accepted=int(request.POST.get(f"accepted_{i}",0)); rejected=int(request.POST.get(f"rejected_{i}",0))
                if received: items.append({"productId":item["productId"],"receivedQuantity":received,"acceptedQuantity":accepted,"rejectedQuantity":rejected})
            result=gr_service.create_goods_receipt(request.POST.get("receipt_number",f"GR-{uuid.uuid4().hex[:8].upper()}"),selected,_safe_date(request.POST.get("receipt_date")),items,request.session.get("user_id"),request.POST.get("notes","")); AuditLogService().log(request,"CREATE","Goods Receipt dibuat.","goods_receipt",str(result["_id"]),module="procurement",reference_id=str(result["_id"]),after=result); messages.success(request,"Goods Receipt berhasil dibuat."); return redirect("inventory_ui:goods_receipt_list")
        except Exception as exc: messages.error(request,str(exc))
    return render(request,"inventory/goods_receipt_form.html",{"pos":pos,"po":po})


@permission_required_custom("procurement")
def goods_receipt_detail_ui(request, receipt_id):
    receipt=gr_service.get_goods_receipt_by_id(receipt_id)
    if not receipt: messages.error(request,"Goods Receipt tidak ditemukan."); return redirect("inventory_ui:goods_receipt_list")
    return render(request,"inventory/goods_receipt_detail.html",{"receipt":receipt})


@permission_required_custom("procurement")
def purchase_list_ui(request): return render(request,"inventory/purchases.html",{"purchases":purchase_service.get_all_purchases(),"receipts":gr_service.get_all_goods_receipts()})


@permission_required_custom("procurement")
def purchase_create_ui(request):
    receipts=gr_service.get_all_goods_receipts(); pos=po_service.get_all_purchase_orders()
    if request.method=="POST":
        try:
            receipt_id=request.POST.get("goods_receipt_id"); receipt=gr_service.get_goods_receipt_by_id(receipt_id)
            if not receipt: raise ValueError("Goods Receipt tidak ditemukan.")
            result=purchase_service.create_purchase(request.POST.get("purchase_number",f"PUR-{uuid.uuid4().hex[:8].upper()}"),str(receipt.get("poId")),receipt_id,_safe_date(request.POST.get("purchase_date")),_num(request.POST.get("discount",0)),_num(request.POST.get("tax",0)),request.session.get("user_id")); AuditLogService().log(request,"CREATE","Pembelian dibuat.","purchase",str(result["_id"]),module="procurement",reference_id=str(result["_id"]),after=result); messages.success(request,"Pembelian berhasil dibuat."); return redirect("inventory_ui:purchase_list")
        except Exception as exc: messages.error(request,str(exc))
    return render(request,"inventory/purchase_form.html",{"receipts":receipts,"pos":pos})


@permission_required_custom("procurement")
def purchase_detail_ui(request, purchase_id):
    purchase=purchase_service.get_purchase_by_id(purchase_id)
    if not purchase: messages.error(request,"Pembelian tidak ditemukan."); return redirect("inventory_ui:purchase_list")
    return render(request,"inventory/purchase_detail.html",{"purchase":purchase})


@permission_required_custom("procurement")
def supplier_invoice_list_ui(request): return render(request,"inventory/invoices.html",{"invoices":invoice_service.get_all_invoices(),"purchases":purchase_service.get_all_purchases()})


@permission_required_custom("procurement")
def supplier_invoice_create_ui(request):
    purchases=purchase_service.get_all_purchases()
    if request.method=="POST":
        try:
            result=invoice_service.create_invoice(request.POST.get("invoice_number",f"INV-{uuid.uuid4().hex[:8].upper()}"),request.POST.get("purchase_id"),_safe_date(request.POST.get("invoice_date")),_safe_date(request.POST.get("due_date")),request.session.get("user_id")); AuditLogService().log(request,"CREATE","Supplier invoice dibuat.","invoice",str(result["_id"]),module="procurement",reference_id=str(result["_id"]),after=result); messages.success(request,"Invoice supplier berhasil dibuat."); return redirect("inventory_ui:supplier_invoice_list")
        except Exception as exc: messages.error(request,str(exc))
    return render(request,"inventory/invoice_form.html",{"purchases":purchases})


@permission_required_custom("procurement")
def supplier_invoice_detail_ui(request, invoice_id):
    invoice=invoice_service.get_invoice_by_id(invoice_id)
    if not invoice: messages.error(request,"Invoice tidak ditemukan."); return redirect("inventory_ui:supplier_invoice_list")
    payments=payment_service.get_payments_by_invoice(invoice_id)
    return render(request,"inventory/invoice_detail.html",{"invoice":invoice,"payments":payments})


@permission_required_custom("procurement")
def supplier_payment_list_ui(request): return render(request,"inventory/payments.html",{"payments":payment_service.get_all_payments(),"invoices":invoice_service.get_outstanding_invoices()})


@permission_required_custom("procurement")
def supplier_payment_create_ui(request):
    invoices=invoice_service.get_outstanding_invoices()
    if request.method=="POST":
        try:
            result=payment_service.create_payment(request.POST.get("payment_number",f"PAY-{uuid.uuid4().hex[:8].upper()}"),request.POST.get("invoice_id"),request.POST.get("amount"),_safe_date(request.POST.get("payment_date")),request.POST.get("payment_method","TRANSFER"),request.POST.get("reference_number",""),request.POST.get("notes",""),request.session.get("user_id")); AuditLogService().log(request,"PAYMENT","Pembayaran supplier tercatat.","supplier_payment",str(result["payment"]["_id"]),module="procurement",reference_id=str(result["payment"]["_id"]),after=result); messages.success(request,"Pembayaran supplier berhasil dicatat."); return redirect("inventory_ui:supplier_payment_list")
        except Exception as exc: messages.error(request,str(exc))
    return render(request,"inventory/payment_form.html",{"invoices":invoices})
