from django.http import HttpResponse
from django.shortcuts import render


def index(request):
    context={}
    # if not request.user.is_authenticated:
    #     return redirect('mainapp:login')
    return render(request, 'dashboard/index.html', context)
