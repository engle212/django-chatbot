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