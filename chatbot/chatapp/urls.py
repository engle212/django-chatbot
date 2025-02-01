from django.urls import path

from . import views

urlpatterns = [
    path("chat/", views.ReactView.as_view(), name="react_view"),
    path("chat/new/", views.NewView.as_view(), name="new_button"),
    path("", views.index, name="index"),
    path("new/", views.new_convo_button, name="new_convo_button"),
    path("swap/<int:convo_id>", views.switch_convo_button, name="switch_convo_button")
]