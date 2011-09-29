import os
from random import choice
import re

import django
from django.core.management.base import copy_helper
from django.core.management.color import color_style

from glustik import GluStik

class DjangoGlu(GluStik):
    """
    GluStik subclass with Django specific helpers to create manage.py, settings.py,
    urls.py, and start an app.
    """
    def _make_context(self, name, context=None):
        super(DjangoGlu, self)._make_context(name, context)
        self.context["project"] = name
    
    def _get_django_path(self, join=[]):
        p = os.path.join(django.__path__[0], 'conf')
        if join:
            join.insert(0, p)
            p = os.path.join(*join)
        return p
    
    def _make_secret(self):
        return ''.join([choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(50)])
    
    def app(self, path=None, key=None):
        """
        Creates the standard Django app layout at the given path using key as the
        app name.
        """
        path = self._get_usable_path(path)
        key = self._contextualize(key)
        pparts = os.path.split(path)
        if key in pparts[1]:
            path = pparts[0]
        self.empty(path)
        copy_helper(color_style(), 'app', key, path, self.context["project"])
    
    def manage(self, path=None, key=None):
        """
        Drops in the standard Django manange.py
        """
        path = self._get_usable_path(path)
        self.empty(path)
        src = self._get_django_path(['project_template', 'manage.py'])
        dst = path
        content = open(src, 'r').read()
        fh = open(dst, 'w')
        fh.write(content)
        fh.close()
    
    def settings(self, path=None, key=None):
        """
        Drops in the standard Django settings.py
        """
        path = self._get_usable_path(path)
        self.empty(path)
        src = self._get_django_path(['project_template', 'settings.py'])
        dst = path
        content = open(src, 'r').read().replace("{{ project_name }}", self.context['project'])
        secret_key = self._make_secret()
        content = re.sub(r"(?<=SECRET_KEY = ')'", secret_key + "'", content)
        fh = open(dst, 'w')
        fh.write(content)
        fh.close()
    
    def urls(self, path=None, key=None):
        """
        Drops in the standard Django urls.py
        """
        path = self._get_usable_path(path)
        self.empty(path)
        src = self._get_django_path(['project_template', 'urls.py'])
        dst = path
        content = open(src, 'r').read().replace("{{ project_name }}", self.context['project'])
        fh = open(dst, 'w')
        fh.write(content)
        fh.close()
