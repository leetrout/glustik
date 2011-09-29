# About

GluStik is a simple utility to create package structures on disk using a
dictionary to describe the directory structure. A class with helpers specific
to django has been included. It does NOT use any templating engine but does
support simple contextualizing using standard string interpolation.

# Usage

Import GluStik, instantiate it, define a layout, and call build.

    from glustik import GluStik
    glu = GluStik("name")
    
    layout = {
        "%(name)s" : {
            "__init__.py" : glu.init,
            "%(name)s" : (glu.file, (), {}),
        }
    }
    
    glu.build(layout)
    
There are 4 basic execution rules as GluStik crawls through the dictionary's keys and values:

 * If the key is a string it gets appended to self.path_parts, an array representing
 the path we are building.
 
 * If the key is callable it will only be called if there is not a handler for the
 value in self.value_handlers[type(value)]. If it is called it will be passed the
 value in the first positional argument.
 
 * If the value is callable it will be called and passed the key in the 'key'
 keyword argument.
 
 * If the value is a pair it is assumed that the key is callable and the pair's
 values will be expanded into args and kwargs `func(*t[0],**t[1])`.  If, instead,
 a triple is found then it is assumed that the values are (callable, tuple, dict)
 and will be executed as `t[0](*t[1],**t[2])` in a standard function(*args,**kwargs)
 pattern

# Overview

GluStik inspects a Python dictionary and takes actions based of the types of the
keys and values present.  You can think of it as a tree describing the file
system layout in which all the keys that are strings become the path and that path
is accessible to callable values

Let's walk through a simple setup:

    from glustik import GluStik
    glu = GluStik("awesomesauce")
    
    layout = {
        "%(name)s" : {
            "__init__.py" : glu.init,
            "%(name)s" : (glu.file, (), {content="from os import *"}),
        }
    }
    
    glu.build(layout)

This would create:

    ./awesomesauce
    ./awesomesauce/__init__.py
    ./awesomesauce/awesomesauce.py

The file awesomesauce.py would contain the contents "from os import *" (without
the quotes, of course).

Let's go over how this happened:

    glu = GluStik("awesomesauce")

This instantiates GluStik and by default calls self._make_context with the provided
name.  The default _make_context method sets self.context = {} then self["name"]
= name. So now we have access to "awesomesauce" in our methods. Next it registers
the provided handlers.

Calling glu.build(layout) starts looping through the layouts keys and values and
passing them to functions as defined by our handlers based on their type or to
the value if it itself is callable.

    "%(name)s" : {
    
This is the first key they build loop discovers and first it determines if it is
callable. In this case it is not so it proceeds to get the type of the key, str
in this case, and look up a handler for that type. If the lookup is successful
it calls the handler giving it 2 arguments: the key and the key's value. In our
example this went like:

    self.key_handlers[type("%(name)s")]("%(name)s", {...})

By default self._handle_string_key appends its key to self.path_parts and then
parses the value, finally popping the appended key off self.path_parts.
self.path_parts is an array of the relative path as we traverse the layout.

So now we've called the string handler and the handler has appened now it repeats
a similar lookup on the value (our nested dictionary) and finds
self._handle_dict_value which basically starts the whole process again.

Eventually your dictionaries will need to reach an endpoint where you will
describe the key with an action in the value.

    "__init__.py" : glu.init

This tells GluStik to make an empty init file there. You could also use

    "__init__.py" : glu.file

It's important to note here that if the key isn't the exact string `"__init__.py"`
GluStik will create the init in a sub directory.

Assume we didn't want anything else in the directory- this would work as well:

    layout = {
        "%(name)s" : glu.init
    }

This would create:

    ./awesomesauce
    ./awesomesauce/__init__.py

Any string, path or file content or file template content, gets passed to
self._contextualize where substitutions are made. GluStik becomes quite powerful
when you leverage that ability.

# Reference

## Default GluStik Methods

### build

    build(self, layout)

Inspects the given layout dictionary, interprets the pieces, and takes
the necessary action based on whether the key is callable. It also performs lookups
based on types in self.key_handlers and self.value_handlers

### copy

    copy(self, path=None, key=None, src=None, contextualize=False, context=None)

Copies the given source to the destination path. Can optionally contextualize the
contents after the copy. Wraps shutil.copy.

### dir

    dir(self, path=None, key=None)

Wraps self.empty for aestetics.

### dirs

    dirs(self, dirs=None, key=None)

Bascially a wrapper for self.build by passing the first positional argument to
self.build if it's a dict. Otherwise the arg should be a list of strings that
will be passed to self.build to create an empty directories.

### empty

    empty(self, path=None, key=None)

Creates an empty directory at the given path.  Wraps os.makedirs so the whole
path will be created.

### file

    file(self, path=None, key=None, file_name=None, content=None, template_path=None, context=None)

Creates a file at the given path. If a file name is provided it will be
joined using os.path.join to the determined path. File handles are opened
using append mode. If content is provided it will be written to the file.
Alternately a template path can be provided and the file contents will
be copied into the new file. In either case contents are contextualized
before they are written. You may also provide a context just for this
operation that will update self.context.

### init

    init(self, path=None, key=None)

Helper to drop in an empty __init__.py Use self.file instead if you need to
write file content.

## Default DjangoGlu Methods

### app

    app(self, path=None, key=None)

Creates the standard Django app layout at the given path using key as the app
name.

### manage

    manage(self, path=None, key=None)

Drops in the standard Django manange.py

### settings

    settings(self, path=None, key=None)

Drops in the standard Django settings.py

### urls

    urls(self, path=None, key=None)

Drops in the standard Django urls.py

# Example

Here's an example of a glu script to build out a somewhat complicated Django
package structure and enforce some basic naming conventions.

    from glustik.django_glu import DjangoGlu

    class MyDjangoGlu(DjangoGlu):
        PACKAGE_SUFFIX = '-pkg'
        PROJECT_SUFFIX = "_proj"
        
        def _make_context(self, name):
            super(MyDjangoGlu, self)._make_context(name)
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
                                "%(name)s.wsgi" : (glu.file, (), {"template_path":"/tmp/dozer_wsgi.txt", "context":{"config_env":"prod"}}),
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

This would result in:

    /tmp/foo-pkg
    /tmp/foo-pkg/foo_proj
    /tmp/foo-pkg/foo_proj/apps
    /tmp/foo-pkg/foo_proj/apps/__init__.py
    /tmp/foo-pkg/foo_proj/apps/foo
    /tmp/foo-pkg/foo_proj/apps/foo/__init__.py
    /tmp/foo-pkg/foo_proj/apps/foo/models.py
    /tmp/foo-pkg/foo_proj/apps/foo/tests.py
    /tmp/foo-pkg/foo_proj/apps/foo/views.py
    /tmp/foo-pkg/foo_proj/config
    /tmp/foo-pkg/foo_proj/config/__init__.py
    /tmp/foo-pkg/foo_proj/config/admin
    /tmp/foo-pkg/foo_proj/config/admin/foo.wsgi
    /tmp/foo-pkg/foo_proj/config/admin/settings.py
    /tmp/foo-pkg/foo_proj/config/admin/urls.py
    /tmp/foo-pkg/foo_proj/config/base
    /tmp/foo-pkg/foo_proj/config/base/__init__.py
    /tmp/foo-pkg/foo_proj/config/base/settings.py
    /tmp/foo-pkg/foo_proj/config/base/urls.py
    /tmp/foo-pkg/foo_proj/config/dev
    /tmp/foo-pkg/foo_proj/config/dev/foo.wsgi
    /tmp/foo-pkg/foo_proj/config/dev/settings.py
    /tmp/foo-pkg/foo_proj/config/dev/urls.py
    /tmp/foo-pkg/foo_proj/config/foo.txt
    /tmp/foo-pkg/foo_proj/config/prod
    /tmp/foo-pkg/foo_proj/config/prod/foo.wsgi
    /tmp/foo-pkg/foo_proj/config/prod/settings.py
    /tmp/foo-pkg/foo_proj/config/prod/urls.py
    /tmp/foo-pkg/foo_proj/config/stage
    /tmp/foo-pkg/foo_proj/config/stage/foo.wsgi
    /tmp/foo-pkg/foo_proj/config/stage/settings.py
    /tmp/foo-pkg/foo_proj/config/stage/urls.py
    /tmp/foo-pkg/foo_proj/config/test
    /tmp/foo-pkg/foo_proj/config/test/foo.txt
    /tmp/foo-pkg/foo_proj/libs
    /tmp/foo-pkg/foo_proj/libs/__init__.py
    /tmp/foo-pkg/foo_proj/media
    /tmp/foo-pkg/foo_proj/media/foo
    /tmp/foo-pkg/foo_proj/templates
    /tmp/foo-pkg/foo_proj/templates/foo
