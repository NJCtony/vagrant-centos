from django.http import HttpResponse
from django.shortcuts import render

# Security
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.shortcuts import redirect

def index(request):
    context={}
    # if not request.user.is_authenticated:
    #     return redirect('dashboard:login')
    return render(request, 'dashboard/index.html', context)

def login(request):
    context = {}
    auth_logout(request)
    try:
        del request.session['userid']
    except KeyError:
        pass

    if request.POST:
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            auth_login(request, user)
            request.session['userid'] = username
            return redirect('dashboard:index')
    return render(request, 'dashboard/login.html', context)
