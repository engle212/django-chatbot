"""
This module handles the views for the Django application. Currently,
it also contains all of the actual app functionality.
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
    The content to be displayed to the user. Passes in a context and 
    request object to a template.
  """
  template = loader.get_template("chatapp/index.html")
  # Create session
  request.session['name'] = 'django-chatbot'
  session_key = request.session.session_key
  
  filename, messages = get_most_recent_conversation(session_key)
  all_convos = get_all_conversations(session_key)

  context = {
    "title": "django-chatbot",
    "messages": messages,
    "convos": all_convos,
  }

  if request.POST:
    user_message = request.POST["text"]
    # Reflect new message in view
    context["messages"].append([0, user_message])
    # Store user message in S3 bucket
    store_message(session_key,
                  get_convo_id(filename),
                  True,
                  user_message)
    # Get LLM's reply
    ai_message = get_reply()
    context["messages"].append([1, ai_message])
    # Store LLM message in S3 bucket
    store_message(session_key,
                  get_convo_id(filename),
                  False,
                  ai_message)

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
  filename = gen_filename(user_id, str(len(convo_files)+1))

  with open(filename, "w") as outfile:
    json.dump(messages, outfile)
  
  return str(filename)

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
  data_files = os.listdir(os.path.join(settings.BASE_DIR,
                                       "chatapp\\data"))
  filtered = [f for f in data_files if user_id in f]
  return list(filtered)

def get_most_recent_conversation(user_id):
  """
  Gets the user's most-recently created conversation.

  Parameters
  ----------
  user_id : string
    The current session ID.

  Returns
  -------
  string
    The name of the user's most-recently created conversation file.
  list
    The messages from the user's most-recently created conversation.
  """
  messages = []
  filename = ""
  all_convos = get_all_conversations(user_id)
  if len(all_convos) > 0:
    all_convos.sort(key=get_convo_id)
    convo_id = get_convo_id(all_convos[-1])
    filename = gen_filename(user_id, convo_id)
    messages = get_conversation(user_id, convo_id)
  else:
    filename = create_conversation(user_id)
    messages = get_conversation(user_id, get_convo_id(filename))
  return str(filename), list(messages)

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
  """
  Get the messages of a specific conversation.

  Parameters
  ----------
  user_id : string
    The ID of the user who owns the specified conversation.
  convo_id : string
    The ID of the specified conversation.

  Returns
  -------
  list
    The messages from the specified conversation.
  """
  filename = gen_filename(user_id, convo_id)
  messages = []
  with open(filename, "r") as infile:
    messages = json.load(infile)
  return list(messages)

def update_conversation(user_id, convo_id, new_data):
  """
  Overwrite the data in a conversation.

  Parameters
  ----------
  user_id : string
    The ID of the user who owns the specified conversation.
  convo_id : string
    The ID of the specified conversation.
  new_data : string
    The conversation data to replace the existing contents of the
    conversation.
    
  Returns
  -------
  boolean
    Indicates whether the conversation could be successfully updated.

  """
  is_successful = False
  filename = gen_filename(user_id, convo_id)
  
  with open(filename, "w") as outfile:
    json.dump(new_data, outfile)
    is_successful = True

  return is_successful

def gen_filename(user_id, convo_id):
  """
  Get the filename of a specific conversation.

  Parameters
  ----------
  user_id : string
    The ID of the user who owns the specified conversation.
  convo_id : string
    The ID of the specified conversation.

  Returns
  -------
  string
    The filename of the specified conversation.
  """
  filename = os.path.join(settings.BASE_DIR, 
                          "chatapp\\data\\"
                          + str(user_id)
                          + "_convo_"
                          + str(convo_id)
                          + ".json")
  return str(filename)

def get_reply():
  """
  Prompts the LLM for a response. Uses the chat history from S3 as
  input for the model.
  
  Returns
  -------
  string
    The output of the LLM based on the latest input message.
  """
  print("Getting response...")
  reply = "Robot words and such"
  return reply

def store_message(user_id, convo_id, is_user, message):
  """
  Communicates with the S3 bucket to add a new message to the correct
  convo file.

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
  print(user_id)
  print(convo_id)
  messages = get_conversation(user_id, convo_id)
  messages.append([(not is_user) * 1, message])
  is_successful = update_conversation(user_id, convo_id, messages)

  return is_successful
