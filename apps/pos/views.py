from django.http import HttpResponse

from apps.authentication.decorators import permission_required_custom


@permission_required_custom("sales")
def pos_view(request):
    return HttpResponse("Halaman POS")