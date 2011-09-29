from glustik import GluStik

glu = GluStik("awesome_sauce")

layout = {
    "%(name)s" : {
        "__init__.py" : glu.init,
        "foo": {
            "bar": glu.empty
        }
    }
}

glu.build(layout)