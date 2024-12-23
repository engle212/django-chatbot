from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

def index(request):
  template = loader.get_template("chatapp/index.html")
  context = {
    "title": "django-chatbot",
    "message": "Hello, world! from views.index()"
  }
  return HttpResponse(template.render(context, request))
