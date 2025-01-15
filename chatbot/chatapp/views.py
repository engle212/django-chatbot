"""
This module handles the views for the Django application. Currently, it also contains all of the actual app functionality.
"""
from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from django.conf import settings
import json
import time
import os

def index(request):
  """
  Renders the main index page.

  Returns
  -------
  HttpResponse
    The content to be displayed to the user. Passes in a context and request object to a template.
  """
  template = loader.get_template("chatapp/index.html")
  # Create session
  request.session['name'] = 'django-chatbot'
  session_key = request.session.session_key
  
  convo_filename = create_conversation(session_key)
  
  

  context = {
    "title": "django-chatbot",
    "messages": [
      [0, "Hello, world! I am the user"],
      [1, "Hello, I am a robot"]
    ]
  }

  if request.POST:
    user_message = request.POST["text"]
    # Reflect new message in view
    context["messages"].append([0, user_message])
    # Store user message in S3 bucket
    store_message(session_key, 3, True, user_message)
    # Get LLM's reply
    ai_message = get_reply()
    context["messages"].append([1, ai_message])
    # Store LLM message in S3 bucket
    store_message(session_key, 3, False, ai_message)

  print(context)
  return HttpResponse(template.render(context, request))

def create_conversation(user_id):
  """
  Create a new conversation file for the specified user.

  Parameters
  ----------
  user_id : string
    The current session ID.
  
  Returns
  -------
  string
    The name of the file created.
  """
  convo_files = get_all_conversations(user_id)
  messages = {
    "messages": []
  }
  filename = os.path.join(settings.BASE_DIR, str(user_id) + "_convo_" + str(len(convo_files)+1) + ".json")

  with open(filename, "w") as outfile:
    json.dump(messages, outfile)
  
  return filename

def get_all_conversations(user_id):
  """
  Gets all of the user's conversation file names.

  Parameters
  ----------
  user_id : string
    The current session ID.

  Returns
  -------
  list
    The conversation file names associated with the user_id.
  """
  data_files = os.listdir(os.path.join(settings.BASE_DIR, "chatapp/data"))
  filtered = [f for f in data_files if user_id in f]
  return filtered

def get_most_recent_conversation(user_id):
  """
  Gets the user's most-recently created conversation.

  Parameters
  ----------
  user_id : string
    The current session ID.

  Returns
  -------
  list
    The messages from the user's most-recently created conversation.
  """
  messages = []
  all_convos = get_all_conversations(user_id)
  if len(all_convos) > 0:
    all_convos.sort(key=get_convo_id)
    messages = get_conversation(user_id, get_convo_id(all_convos[-1]))
  else:
    filename = create_conversation(user_id)
    messages = get_conversation(user_id, get_convo_id(filename))
  return messages

def get_convo_id(filename):
  """
  Get the conversation ID as an integer.

  Parameters
  ----------
  filename : string
    A filename pointing to a conversation JSON file.

  Returns
  -------
  int
    ID of the conversation associated with filename.
  """
  num_str = os.path.splitext(filename)[0].split("_")[2]
  return int(num_str)

def get_conversation(user_id, convo_id):
  filename = os.path.join(settings.BASE_DIR, str(user_id) + "convo" + str(convo_id) + ".json")
  messages = []
  with open(filename, "r") as infile:
    messages = json.load(infile)["messages"]
  return messages

def get_reply():
  """
  Prompts the LLM for a response. Uses the chat history from S3 as input for the model.
  
  Returns
  -------
  string
    The output of the LLM based on the latest input message.
  """
  print("Getting response...")
  time.sleep(2)
  
  return "Robot words and such"

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
