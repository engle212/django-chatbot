"""
This module handles the views for the Django application. Currently,
it also contains all of the actual app functionality.
"""
from django.shortcuts import redirect
from django.http import HttpResponse
from django.template import loader
from django.conf import settings
import json
import yaml
import os
import markdown
from huggingface_hub import InferenceClient

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
    convo_id = request.session["active_convo"]
    messages = get_conversation(session_key, convo_id)
    filename = gen_filename(session_key, convo_id)
  else:
    filename, messages = get_most_recent_conversation(session_key)
    convo_id = get_convo_id(filename)
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
    # Store user message in S3 bucket
    store_message(session_key,
                  convo_id,
                  True,
                  user_message)
    # Get LLM's reply
    ai_message = get_reply(session_key, convo_id)
    context["messages"].append([1, ai_message])
    # Store LLM message in S3 bucket
    store_message(session_key,
                  convo_id,
                  False,
                  ai_message)

  all_sums = [get_summary(os.path.join(settings.BASE_DIR, "chatapp\\data\\" + c)) for c in all_convos]
  all_convo_ids = [get_convo_id(c) for c in all_convos]
  convo_list = zip(all_convo_ids, all_convos, all_sums)
  context["convos"] = convo_list

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
  filename = create_conversation(request.session.session_key)
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

def get_summary(filename):
  """
  Get the summary in a specified conversation file.

  Parameters
  ----------
  filename : string
    The path to the file of the conversation whose summary is requested.
  Returns
  -------
  string
    The summary of the conversation.
  """
  summary = ""
  with open(filename, "r") as infile:
    summary = json.load(infile)["summary"]
  return summary

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
  filename = gen_filename(user_id, convo_id)
  convo = get_conversation(user_id, convo_id)
  
  if len(convo) >= 2:
    with open(filename, "w") as file:
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
      # Save dictionary to file
      json.dump(convo_dict, file)

      is_successful = True
  else:
    with open(filename, "w") as file:
      convo_dict = {
        "messages": convo,
        "summary": "A new conversation"
      }
      # Save dictionary to file
      json.dump(convo_dict, file)

      is_successful = True
  return is_successful

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
  convo = {
    "messages": [],
    "summary": "A new conversation"
  }
  filename = gen_filename(user_id, str(len(convo_files)+1))

  with open(filename, "w") as outfile:
    json.dump(convo, outfile)
  
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
  filename = gen_filename(user_id, convo_id)
  messages = []
  with open(filename, "r") as infile:
    messages = json.load(infile)
  return list(messages["messages"])

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

def get_reply(user_id, convo_id):
  """
  Prompts the LLM for a response. Uses the chat history from S3 as
  input for the model.
  
  Returns
  -------
  string
    The output of the LLM based on the latest input message.
  """
  # Authenticate
  data = []
  with open(os.path.join(settings.BASE_DIR, 
                         "chatapp\\data\\api_key.yaml")) as file:
    data = yaml.safe_load(file)

  key = ""
  if len(data) > 0:
    key = data["key"]
  else:
    return "API key must be supplied."

  print("Getting response...")
  client = InferenceClient(api_key=key)

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
  messages = get_conversation(user_id, convo_id)
  summary = get_summary(gen_filename(user_id, convo_id))
  messages.append([(not is_user) * 1, message])
  is_successful = update_conversation(user_id,
                                      convo_id,
                                      {"messages": messages, "summary": summary})

  return is_successful
