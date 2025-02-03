"""
This module handles the views for the Django application. Currently,
it also contains all of the actual app functionality.
"""
from django.shortcuts import redirect
from django.http import HttpResponse
from django.template import loader
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
import json
import yaml
import os
import markdown
from huggingface_hub import InferenceClient
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.config import Config
from io import BytesIO

class ReactView(APIView):
  def get(self, request):
    template = loader.get_template("chatapp/index.html")
    # Create session
    #if not request.session.session_key:
    #  request.session.create()
    session_key = request.COOKIES.get("key")
    request.session['name'] = 'django-chatbot'
    #session_key = request.session.session_key

    convo_id = ""
    if "active_convo" in request.COOKIES:
      convo_id = request.session["active_convo"]
      messages = get_conversation(session_key, convo_id)
    else:
      convo_id, messages = get_most_recent_conversation(session_key)
      request.session["active_convo"] = convo_id

    all_convos = get_all_conversations(session_key)
      
    context = {
      "title": "django-chatbot",
      "convo_id": convo_id,
      "messages": messages,
      "convos": []
    }

    all_sums = [get_summary(session_key, c) for c in all_convos]
    convo_list = list(zip(all_convos, all_sums))
    context["convos"] = convo_list
    print(all_convos)

    update_convo_summary(session_key, convo_id)
    return Response(data=context)
  def post(self, request):
    template = loader.get_template("chatapp/index.html")
    # Create session
    if not request.session.session_key:
      request.session.create()
    session_key = request.session.session_key
    request.session['name'] = 'django-chatbot'
    session_key = request.session.session_key

    convo_id = ""
    if "active_convo" in request.session:
      convo_id = request.session["active_convo"]
      messages = get_conversation(session_key, convo_id)
    else:
      convo_id, messages = get_most_recent_conversation(session_key)
      request.session["active_convo"] = convo_id

    all_convos = get_all_conversations(session_key)
      
    context = {
      "title": "django-chatbot",
      "convo_id": convo_id,
      "messages": messages,
      "convos": []
    }

    user_message = request.data["text"]
    # Reflect new message in view
    context["messages"].append([0, user_message])
    # Store user message in conversation
    store_message(session_key,
                  convo_id,
                  True,
                  user_message)
    # Get LLM's reply
    ai_message = get_reply(session_key, convo_id)
    context["messages"].append([1, ai_message])
    # Store LLM message in conversation
    store_message(session_key,
                  convo_id,
                  False,
                  ai_message)

    all_sums = [get_summary(session_key, c) for c in all_convos]
    convo_list = list(zip(all_convos, all_sums))
    context["convos"] = convo_list
    print(all_convos)

    update_convo_summary(session_key, convo_id)
    return Response(data=context)

class NewView(APIView):
  def get(self, request):
    convo_id = create_conversation(request.session.session_key)
    return Response(data={"redirect": "/chat"})


def index(request):
  """
  Renders the main index page.

  Returns
  -------
  HttpResponse
    The content to be displayed to the user. Passes in a context and 
    request object to a template.
  """
  if not os.path.isdir(os.path.join(settings.BASE_DIR, "chatapp\\data")):
    os.mkdir(os.path.join(settings.BASE_DIR, "chatapp\\data"))

  template = loader.get_template("chatapp/index.html")
  # Create session
  if not request.session.session_key:
    request.session.create()
  session_key = request.session.session_key
  request.session['name'] = 'django-chatbot'
  session_key = request.session.session_key
  
  convo_id = ""
  if "active_convo" in request.session:
    convo_id = str(request.session["active_convo"])
    messages = get_conversation(session_key, convo_id)
  else:
    convo_id, messages = get_most_recent_conversation(session_key)
    request.session["active_convo"] = convo_id

  all_convos = get_all_conversations(session_key)

  context = {
    "title": "django-chatbot",
    "convo_id": convo_id,
    "messages": messages,
    "convos": []
  }

  if request.POST and request.POST["text"]:
    user_message = request.POST["text"]
    # Reflect new message in view
    context["messages"].append([0, user_message])
    # Store user message in conversation
    store_message(session_key,
                  convo_id,
                  True,
                  user_message)
    # Get LLM's reply
    ai_message = get_reply(session_key, convo_id)
    context["messages"].append([1, ai_message])
    # Store LLM message in conversation
    store_message(session_key,
                  convo_id,
                  False,
                  ai_message)

  all_sums = [get_summary(session_key, c) for c in all_convos]
  convo_list = list(zip(all_convos, all_sums))
  context["convos"] = convo_list
  print(all_convos)

  update_convo_summary(session_key, convo_id)
  return HttpResponse(template.render(context, request))

def new_convo_button(request):
  """
  Handles button press for "Start New Conversation" button.

  Returns
  -------
  HttpResponseRedirect
    A redirect to the index page (page reload).
  """
  convo_id = create_conversation(request.session.session_key)
  return redirect('index')

def switch_convo_button(request, convo_id):
  """
  Handles user selecting a new conversation. Change the active conversation.

  Returns
  -------
  HttpResponseRedirect
    A redirect to the index page (page reload).
  """
  request.session['active_convo'] = convo_id
  return redirect('index')

def get_summary(user_id, convo_id):
  """
  Get the summary in a specified conversation file.

  Parameters
  ----------
  user_id : string
    The ID of the user who owns the specified conversation.
  convo_id : string
    The ID of the specified conversation.

  Returns
  -------
  string
    The summary of the conversation.
  """
  convo = read_from_dynamo(user_id, convo_id)
  return convo["summary"]

def update_convo_summary(user_id, convo_id):
  """
  Update the summary of the specified conversation.

  Parameters
  ----------
  user_id : string
    The ID of the user who owns the specified conversation.
  convo_id : string
    The ID of the specified conversation.

  Returns
  -------
  boolean
    Indicates whether the summary could be successfully updated.
  """
  is_successful = False
  convo = get_conversation(user_id, convo_id)
  
  if len(convo) >= 2:
    client = InferenceClient(api_key=os.environ.get("HF_KEY"))

    messages = [{"role": "user", "content": m[1]}
                if m[0] == 0
                else {"role": "assistant", "content": m[1]}
                for m in convo]

    messages.append({"role": "user", "content": "Give this conversation a descriptive, 5-word title with no emojis"})

    stream = client.chat.completions.create(model="google/gemma-2-9b-it",
                                            messages=messages,
                                            temperature=0.5,
                                            max_tokens=1024,
                                            top_p=0.7,
                                            stream=True)
    reply = ""
    for chunk in stream:
      reply = reply + str(chunk.choices[0].delta.content)

    convo_dict = {
      "messages": convo,
      "summary": reply
    }
    update_to_dynamo(user_id, convo_id, convo_dict)

    is_successful = True
  else:
    convo_dict = {
      "messages": convo,
      "summary": "A new conversation"
    }
    update_to_dynamo(user_id, convo_id, convo_dict)

    is_successful = True
  return is_successful

def add_to_dynamo(convo_dict, user_id, convo_id):
  # Put an item in the table
  dynamo_config = Config(
    region_name = "us-east"
  )
  dynamodb = boto3.resource("dynamodb", dynamo_config)
  table = dynamodb.Table("django-chatbot-table")
  table.put_item(
    Item={
      "user_id": str(user_id),
      "convo_id": str(convo_id),
      "messages": convo_dict["messages"],
      "summary": convo_dict["summary"],
    }
  )
  return

def update_to_dynamo(user_id, convo_id, new_data):
  # Modify an existing item
  dynamo_config = Config(
    region_name = "us-east"
  )
  dynamodb = boto3.resource("dynamodb", dynamo_config)
  table = dynamodb.Table("django-chatbot-table")
  response = table.update_item(
    Key={
      "user_id": str(user_id),
      "convo_id": str(convo_id),
    },
    UpdateExpression="SET messages = :val1, summary = :val2",
    ExpressionAttributeValues={
      ":val1": new_data["messages"],
      ":val2": new_data["summary"]
    }
  )
  return

def read_from_dynamo(user_id, convo_id):
  # Find and return an item as a dictionary
  dynamo_config = Config(
    region_name = "us-east"
  )
  dynamodb = boto3.resource("dynamodb", dynamo_config)
  table = dynamodb.Table("django-chatbot-table")
  response = table.get_item(
    Key={
      "user_id": str(user_id),
      "convo_id": str(convo_id),
    }
  )
  return response["Item"]

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
    The ID of the newly-created conversation.
  """
  convo_id_list = get_all_conversations(user_id)
  convo = {
    "messages": [],
    "summary": "A new conversation"
  }
  convo_id = str(len(convo_id_list)+1)
  add_to_dynamo(convo, user_id, convo_id)
  
  return convo_id

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
    The convo_id's associated with the user_id.
  """
  dynamo_config = Config(
    region_name = "us-east"
  )
  dynamodb = boto3.resource("dynamodb", dynamo_config)
  table = dynamodb.Table("django-chatbot-table")

  response = table.query(
    KeyConditionExpression=Key("user_id").eq(str(user_id))
  )

  items = response["Items"]
  
  ids = []

  if len(items) > 0:
    ids = [i["convo_id"] for i in items]

  return list(ids)

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
    The ID of the user's most-recently created conversation.
  list
    The messages from the user's most-recently created conversation.
  """
  messages = []
  convo_id = ""
  all_convos = get_all_conversations(user_id)
  if len(all_convos) > 0:
    all_convos.sort(key=int)
    convo_id = get_convo_id(all_convos[-1])
    messages = get_conversation(user_id, convo_id)
  else:
    convo_id = create_conversation(user_id)
    messages = get_conversation(user_id, convo_id)
  return convo_id, list(messages)

def get_convo_id(filename):
  """
  Get the conversation ID as an integer.

  Parameters
  ----------
  filename : string
    A filename pointing to a conversation JSON file.

  Returns
  -------
  string
    ID of the conversation associated with filename.
  """
  num_str = os.path.splitext(filename)[0].split("_")[-1]
  return num_str

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
  item = read_from_dynamo(str(user_id), str(convo_id))

  return list(item["messages"])

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
  update_to_dynamo(user_id, convo_id, new_data)
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

def get_reply(user_id, convo_id):
  """
  Prompts the LLM for a response. Uses the chat history from DynamoDB
  as input for the model.
  
  Returns
  -------
  string
    The output of the LLM based on the latest input message.
  """

  print("Getting response...")
  client = InferenceClient(api_key=os.environ.get("HF_KEY"))

  convo = get_conversation(user_id, convo_id)
  messages = [{"role": "user", "content": "Write an introduction before your response. " + m[1] }
              if m[0] == 0
              else {"role": "assistant", "content": m[1]}
              for m in convo]

  stream = client.chat.completions.create(model="google/gemma-2-9b-it",
                                          messages=messages,
                                          temperature=0.5,
                                          max_tokens=1024,
                                          top_p=0.7,
                                          stream=True)
  reply = ""
  for chunk in stream:
    reply = reply + str(chunk.choices[0].delta.content)

  html = markdown.markdown(reply, 
                           extensions=[
                             "pymdownx.superfences",
                             "markdown.extensions.codehilite",
                             "markdown.extensions.tables",
                             "markdown.extensions.sane_lists"
                           ])
  return html

def store_message(user_id, convo_id, is_user, message):
  """
  Communicates with the DynamoDB to add a new message to the correct
  convo Item.

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
  messages = get_conversation(user_id, convo_id)
  summary = get_summary(user_id, convo_id)
  messages.append([(not is_user) * 1, message])
  is_successful = update_conversation(user_id,
                                      convo_id,
                                      {
                                        "messages": messages, 
                                        "summary": summary
                                      })

  return is_successful
