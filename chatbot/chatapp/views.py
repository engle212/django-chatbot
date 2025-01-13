"""This module handles the views for the Django application. Currently, it also contains all of the actual app functionality."""
from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

def index(request):
  """
  Renders the main index page.

  Returns
  -------
  HttpResponse
    The content to be displayed to the user. Passes in a context and request object to a template.
  """
  template = loader.get_template("chatapp/index.html")
  context = {
    "title": "django-chatbot",
    "messages": [
      [0, "Hello, world! I am the user"],
      [1, "Hello, I am a robot"]
    ],
  }
  if request.POST:
    user_message = request.POST["text"]
    # Reflect new message in view
    context["messages"].append([0, user_message])
    # Store user message in S3 bucket
    store_message(request.session.session_key, 3, True, user_message)
    # Get LLM's reply
    ai_message = get_reply()
    context["messages"].append([1, ai_message])
    # Store LLM message in S3 bucket
    store_message(request.session.session_key, 3, False, ai_message)

  print(context)
  return HttpResponse(template.render(context, request))

def get_reply():
  """
  Prompts the LLM for a response. Uses the chat history from S3 as input for the model.
  
  Returns
  -------
  string
    The output of the LLM based on the latest input message.
  """
  
  return "Robot words..."

def store_message(user_id, convo_id, is_user, message):
  """
  Communicates with the S3 bucket to add a new message to the correct convo file.

  Parameters
  ----------
  user_id : string
    The current session ID.
  convo_id : string
    The ID of the conversation.
  is_user : boolean
    Indicates whether the message is from the user or not.
  message : string
    The message to be stored.

  Returns
  -------
  boolean
    Indicates whether the message could be successfully stored.
  """
  is_successful = False

  print(f"User ID: {user_id}")
  print(f"Conversation ID: {convo_id}")
  print(f"Is User?: {is_user}")
  print(f"User ID: {message}")

  is_successful = True

  return is_successful