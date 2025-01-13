from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

def index(request):
  template = loader.get_template("chatapp/index.html")
  context = {
    "title": "django-chatbot",
    "messages": [
      [0, "Hello, world! I am the user"],
      [1, "Hello, I am a robot"]
    ],
  }
  if request.POST:
    # Reflect new message in view
    context["messages"].append([0, request.POST["text"]])
    # Comm with AWS
    # Get LLM's reply
  print(context)
  return HttpResponse(template.render(context, request))