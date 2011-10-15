import imp
import os
import re
import shutil


__version__ = '0.2'


class GluStik(object):
    """
    GluStik builds file structures from a dictionary based layout.
    """
    base_path = '' # string containing the root of where file ops should happen
    context = {} # string formatting context
    dry_run = False # don't alter the file system
    key_handlers = {} # handlers for dictionary key types
    path_parts = [] # relative path parts as the layout is traversed
    value_handlers = {} # handlers for dictionary value types
    
    def __init__(self, name, base_path=None, context=None, safe=True,
                check_name=True):
        """
        Constructs a glustik instance and defines the context based on the given
        name.
        """
        if check_name and not self._is_name_safe(name):
            raise Exception("%s is not a valid name" % name)
        self.safe = safe
        if not base_path:
            base_path = os.getcwd()
        self.base_path = base_path
        self._make_context(name, context)
        self._register_handlers()
    
    def _reset(self):
        """
        Reset state.
        """
        self.path_parts = []
    
    def _contextualize(self, s, context=None):
        """
        Substitutes any placeholders in the given string with values from
        context or self.context if a context is not provided.
        
        >>> self.context["color"] = "green"
        >>> self._contextualize("My %(color)s wagon")
        'My green wagon'
        >>> self._contextualize("My %(color)s wagon", context={"color":"red"})
        'My red wagon'
        """
        if s:
            if context:
                return s % context
            return s % self.context
        else:
            return ''
    
    def _get_usable_path(self, path):
        """
        Returns a path as a string suitable for using in an file operations by
        determining if a path was provided or if it should use the self.path_parts
        list and then converts it to a string and contextualizes it.
        """
        if not path: path = [self.base_path] + self.path_parts
        path = self._path_as_str(path)
        path = self._contextualize(path)
        return path
    
    def _handle_string_key(self, s, value):
        self.path_parts.append(s)
        if callable(value):
            value(key=s)
        else:
            vt = type(value)
            try:
                self.value_handlers[vt](value, key=s)
            except KeyError:
                self._reset()
                raise Exception("No handler for value type %s" % str(vt))
        self.path_parts.pop()
    
    def _handle_dict_value(self, d, key):
        if callable(key):
            key(d)
        else:
            self.build(d)
    
    def _handle_tuple_value(self, t, key):
        func = callable(key)
        if len(t) == 3 and not func:
            t[0](*t[1], **t[2])
        elif len(t) == 2 and func:
            key(*t[0], **t[1])
        elif func:
            key(t)
        else:
            self._reset()
            raise Exception("No execution path for key %s with tuple value %s" % (str(key),str(t)))
    
    def _is_name_safe(self, name):
        try:
            imp.find_module(name)
        except ImportError:
            if re.search(r'^[_a-zA-Z]\w*$', name):
                return True
        return False
    
    def _is_safe(self, path):
        """
        Checks self.safe to determine if we are operating in "safe mode" and
        whether the given path is safe (doesn't exist if self.safe is True).
        """
        if self.safe:
            if os.path.exists(path):
                return False
        return True
    
    def _make_context(self, name, context=None):
        """
        Creates the context dict based on the given name and sets a base path to
        the current working directory.
        """
        self.context = {}
        self.context["base_path"] = self.base_path
        self.context["name"] = name
        if context:
            self.context.update(context)
    
    def _path_as_str(self, str_or_list):
        """
        Accepts a path as a list or a string and returns a string. If a list
        is provided then os.path.join will join them into a path string.
        """
        tx = type(str_or_list)
        if tx is list:
            return os.path.join(*str_or_list)
        elif tx is str:
            return str_or_list
        else:
            self._reset()
            raise Exception("Path arguments should be string or list. Got %s instead" % tx)
    
    def _register_handlers(self):
        self.key_handlers = {
            str : self._handle_string_key
        }
        self.value_handlers = {
            tuple : self._handle_tuple_value,
            dict : self._handle_dict_value
        }
    
    def _strip_file(self, full_path):
        """
        Strips off a file if it is given in the path (based on existence of an
        extension).
        """
        path, file = os.path.split(full_path)
        if os.path.splitext(file)[1]:
            return path
        return full_path
    
    def build(self, layout, dry_run=None):
        """
        Inspects the given layout dictionary, interprets the pieces, and takes
        the necessary action based on whether the key is callable. It also performs lookups
        based on types in self.key_handlers and self.value_handlers
        """
        old_dry_run = self.dry_run
        if dry_run is not None:
            self.dry_run = dry_run
        if type(layout) is dict:
            for key, val in layout.items():
                val_type = type(val)
                key_type = type(key)
                if callable(key):
                    try:
                        self.value_handlers[val_type](val, key=key)
                    except KeyError:
                        key(val)
                else:
                    try:
                        self.key_handlers[key_type](key, val)
                    except IndexError:
                        self._reset()
                        raise Exception("No handler for key type %s" % str(key_type))
        else:
            self._reset()
            raise TypeError("Layout must be a dictionary. Got %s instead" % type(layout))
        self.dry_run = old_dry_run
    
    def copy(self, path=None, key=None, src=None, contextualize=False, context=None):
        """
        Copies the given source to the destination path. Can optionally
        contextualize the contents after the copy. Wraps shutil.copy.
        """
        path = self._get_usable_path(path)
        self.empty(path)
        shutil.copy(src, path)
        if contextualize:
            content = open(path, 'r').read()
            content = self._contextualize(content, context)
            if not self.dry_run:
                fh = open(path, 'w')
                fh.write(content)
                fh.close()
            else:
                print "open", path
                print "write", content
    
    def dir(self, path=None, key=None):
        """
        Wraps self.empty for aestetics.
        """
        self.empty(path)
    
    def dirs(self, dirs=None, key=None):
        """
        Bascially a wrapper for self.build by passing dirs to self.build if dirs
        is a dict otherwise dirs should be a list of strings that will be passed
        to self.build to create an empty directory.
        """
        dt = type(dirs)
        if dt is dict:
            self.build(dirs)
        elif dt is list:
            for d in dirs:
                if type(d) is str:
                    self.build({d:self.empty})
                else:
                    self._reset()
                    raise TypeError("A list passed to the dirs method should only contain strings")
        else:
            self._reset()
            raise TypeError("dirs method requires a list or dictionary. Got %s instead" % dt)
    
    def empty(self, path=None, key=None):
        """
        Creates an empty directory at the given path.  Wraps os.makedirs so the
        whole path will be created.
        """
        path = self._get_usable_path(path)
        path = self._strip_file(path)
        if self._is_safe(path):
            if not self.dry_run:
                os.makedirs(path)
            else:
                print "makedirs", path
    
    def file(self, path=None, key=None, file_name=None, content=None, template_path=None, context=None):
        """
        Creates a file at the given path. If a file name is provided it will be
        joined using os.path.join to the determined path. File handles are opened
        using append mode. If content is provided it will be written to the file.
        Alternately a template path can be provided and the file contents will
        be copied into the new file. In either case contents are contextualized
        before they are written. You may also provide a context just for this
        operation that will update self.context.
        """
        path = self._get_usable_path(path)
        self.empty(path=path)
        if file_name:
            path = os.path.join(path, file_name)
        if not self.dry_run:
            fh = open(path, 'a')
        else:
            print "open", path
        if context:
            ctx = self.context.copy()
            ctx.update(context)
            context = ctx
        if content:
            if not self.dry_run:
                fh.write(self._contextualize(content, context=context))
            else:
                print "write", self._contextualize(content, context=context)
        if template_path:
            if not self.dry_run:
                fh.write(self._contextualize(open(template_path).read(), context=context))
            else:
                print "opening", template_path
                print "write", self._contextualize(open(template_path).read(), context=context)
        if not self.dry_run:
            fh.close()
    
    def init(self, path=None, key=None):
        """
        Helper to drop in an empty __init__.py Use self.file instead if you need
        to write file content.
        """
        path = self._get_usable_path(path)
        self.empty(path=path)
        if not path.endswith("__init__.py"):
            path = os.path.join(path, "__init__.py")
        if not self.dry_run:
            fh = open(path, 'a')
            fh.close()
        else:
            print "create", path
