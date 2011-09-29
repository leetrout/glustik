"""
Somewhat complicated example of using GluStik to build out a Django skeleton.

This demonstrates a majority of the features of GluStik including copying a file
and making a file from a template.  /tmp/glu_wsgi.txt & /tmp/foo.txt would
have to exist for the code to execute properly.

The resulting structure would be build in /tmp (/tmp/foo-pkg)

Assumes the user is on a POSIX style system.
"""
from glustik.django_glu import DjangoGlu

class MyDjangoGlu(DjangoGlu):
    PACKAGE_SUFFIX = '-pkg'
    PROJECT_SUFFIX = "_proj"
    
    def _make_context(self, name, context=None):
        super(MyDjangoGlu, self)._make_context(name, context)
        self.context["package"] = '%s%s' % (name.replace('_','-'),self.PACKAGE_SUFFIX)
        self.context["project"] = '%s%s' % (name.replace('-','_'),self.PROJECT_SUFFIX)
        self.context["project_dash"] = self.context["project"].replace('_','-')
        self.context["name"] = self.context["project"].replace('_proj','')
        self.context["name_dash"] = self.context["name"].replace('_','-')
        self.context["libs_path"] = "/opt/python/" + self.context["name_dash"] + "-libs"
        self.context["project_path"] = self.context["libs_path"] + "/" + self.context["project"]
        self.context["apps_path"] = self.context["project_path"] + "/apps" 

glu = MyDjangoGlu('foo', base_path='/tmp/')

glu.CONFIG_INIT = """import admin
import base
import dev
import prod
import stage
"""

glu.SETTINGS = "from %(project)s.config.base.settings import *"

glu.URLS = """from django.conf.urls.defaults import patterns, include, url
from %(project)s.config.base.urls import urlpatterns
"""

glu.WSGI = """import os, sys
sys.path.insert(0, '%(libs_path)s')
sys.path.append('%(project_path)s')
sys.path.append('%(apps_path)s')
os.environ['DJANGO_SETTINGS_MODULE'] = '%(project)s.config.%(config_env)s.settings'
import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
"""

layout = {
    "%(package)s" : {
        "%(project)s" : {
            glu.dirs : {
                "libs" : glu.init,
                "apps" : {
                    "__init__.py" : glu.init,
                    "%(name)s" : glu.app
                },
                "media" : {
                    "%(name)s" : glu.empty
                },
                "templates" : {
                    "%(name)s" : glu.empty
                },
                "config" : {
                    "__init__.py" : (glu.file, (), {"content":glu.CONFIG_INIT}),
                    glu.dirs : {
                        "base" : {
                            "__init__.py" : glu.init,
                            "settings.py" : glu.settings,
                            "urls.py" : glu.urls,
                        },
                        "dev" : {
                            "%(name)s.wsgi" : (glu.file, (), {"content":glu.WSGI, "context":{"config_env":"dev"}}),
                            "settings.py" : (glu.file, (), {"content":glu.SETTINGS}),
                            "urls.py" : (glu.file, (), {"content":glu.URLS})
                        },
                        "stage" : {
                            "%(name)s.wsgi" : (glu.file, (), {"content":glu.WSGI, "context":{"config_env":"stage"}}),
                            "settings.py" : (glu.file, (), {"content":glu.SETTINGS}),
                            "urls.py" : (glu.file, (), {"content":glu.URLS})
                        },
                        "admin" : {
                            "%(name)s.wsgi" : (glu.file, (), {"content":glu.WSGI, "context":{"config_env":"admin"}}),
                            "settings.py" : (glu.file, (), {"content":glu.SETTINGS}),
                            "urls.py" : (glu.file, (), {"content":glu.URLS})
                        },
                        "prod" : {
                            "%(name)s.wsgi" : (glu.file, (), {"template_path":"/tmp/glu_wsgi.txt", "context":{"config_env":"prod"}}),
                            "settings.py" : (glu.file, (), {"content":glu.SETTINGS}),
                            "urls.py" : (glu.file, (), {"content":glu.URLS})
                        },
                        "test" : (glu.copy, (), {"src":"/tmp/foo.txt"}),
                        glu.copy : ((),{"src":"/tmp/foo.txt"})
                    }
                }
            }
        }
    }
}

glu.build(layout)
