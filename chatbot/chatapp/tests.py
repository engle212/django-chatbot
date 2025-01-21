from django.test import TestCase
from django.conf import settings
from . import views
import os

class chatbotTestCase(TestCase):
  def test_import(self):
    self.assertEqual(str(type(views).__name__), "module")

  def test_gen_filename_user123_convo900(self):
    filename = views.gen_filename(123, 900)
    self.assertEqual(filename, os.path.join(settings.BASE_DIR, "chatapp\\data\\123_convo_900.json"))

  def test_gen_filename_usera1s2d3f4_convo005(self):
    filename = views.gen_filename("a1s2d3f4", "005")
    self.assertEqual(filename, os.path.join(settings.BASE_DIR, "chatapp\\data\\a1s2d3f4_convo_005.json"))

  def test_get_convo_id_path1(self):
    convo_id = views.get_convo_id("chatbot/chatapp/data/ebr0bfej7g_convo_1.json")
    self.assertEqual(convo_id, "1")

  def test_get_convo_id_file34(self):
    convo_id = views.get_convo_id("ebr0bfej7g_convo_34.json")
    self.assertEqual(convo_id, "34")

  def test_get_convo_id_file0011(self):
    convo_id = views.get_convo_id("ebr0bfej7g_convo_0011.json")
    self.assertEqual(convo_id, "0011")

  def test_get_convo_id_file_extra_underscore(self):
    convo_id = views.get_convo_id("ebr0b_fej7g_convo_2.json")
    self.assertEqual(convo_id, "2")

  def test_get_convo_id_file_missing_underscore(self):
    convo_id = views.get_convo_id("ebr0bfej7gconvo_4.json")
    self.assertEqual(convo_id, "4")

  def test_get_convo_id_file_misplaced_underscore(self):
    convo_id = views.get_convo_id("ebr0b_fej7gconvo_25.json")
    self.assertEqual(convo_id, "25")

  def test_get_convo_id_path_extra_underscore(self):
    convo_id = views.get_convo_id("chatbot/chat_app/data/ebr0bfej7g_convo_677.json")
    self.assertEqual(convo_id, "677")

  def test_get_convo_id_filef612(self):
    convo_id = views.get_convo_id("ebr0bfej7g_convo_f612.json")
    self.assertEqual(convo_id, "f612")