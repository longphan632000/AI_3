"""HTML must track deployed asset changes even when Flask debug mode is off."""
import unittest
from unittest.mock import patch

from jinja2 import DictLoader


class TestTemplateReload(unittest.TestCase):
    def test_cached_template_is_refreshed_when_its_source_changes(self):
        from app import app
        self.assertTrue(app.config['TEMPLATES_AUTO_RELOAD'])
        self.assertTrue(app.jinja_env.auto_reload)
        loader=DictLoader({'qa-template-reload.html':'old layout'})
        with patch.object(app.jinja_env,'loader',loader),patch.object(app.jinja_env,'cache',{}):
            self.assertEqual(app.jinja_env.get_template('qa-template-reload.html').render(),'old layout')
            loader.mapping['qa-template-reload.html']='updated layout'
            self.assertEqual(app.jinja_env.get_template('qa-template-reload.html').render(),'updated layout')
