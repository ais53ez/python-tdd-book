from django.core.mail import send_mail
from django.shortcuts import redirect
from django.contrib import auth, messages
from django.core.urlresolvers import reverse

from accounts.models import Token


def send_login_email(request):
    to_email = request.POST['email']
    token = Token.objects.create(email=to_email)
    url = request.build_absolute_uri(
        reverse('login') + '?token=' + str(token.uid)
    )

    subject = 'Your login link for Superlists'
    from_email = 'noreply@superlists'
    body = f'Use this link to log in:\n\n{url}'
    send_mail(subject, body, from_email, [to_email,])
    messages.success(
        request,
        "Check your email, we've sent you a link you can use to log in."
    )
    return redirect('/')


def login(request):
    user = auth.authenticate(uid=request.GET.get('token'))
    if user:
        auth.login(request, user)
    return redirect('/')

