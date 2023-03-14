from .util import remove_none


class SwaggerObject:
    def json(self):
        """ This method is used to recursively jsonify the entire OpenAPI object and its nested objects """
        json_allowed = [str, list, dict, int, float, type(None), bool]
        obj = {x: y if type(y) in json_allowed else y.json() for x, y in
               vars(self).copy().items()}  # Recursive jsonification

        for x, y in obj.copy().items():
            if type(y) == list:  # Jsonify items of lists
                obj[x] = [item if type(item) in json_allowed else item.json() for item in y]
            if type(y) == dict:  # Jsonify items of dictionaries
                for a, b in y.copy().items():
                    obj[x][a] = b if type(b) in json_allowed else b.json()

        for key in obj.copy().keys():
            if key[0] == "_":  # Edge case `in` for OpenAPI ParameterObject conflicts with python keyword so `_in` was used
                obj[key[1:]] = obj.pop(key)
            if key == "logo":  # Addition of x-logo for Redoc documentation
                obj["x-logo"] = obj.pop(key)

        return remove_none(obj)  # Fields that will not affect the swagger are removed

    def assign_attributes(self, local_dict):
        """ Used to set attributes for all kwargs provided to the object """
        for name, value in {x: y for x, y in local_dict.items() if x != "self"}.items():
            setattr(self, name, value)

    def __getitem__(self, item):
        """ Get item works for all OpenAPI objects """
        return self.__dict__[item]

    def __setitem__(self, item, value):
        """ Set item works for all OpenAPI objects """
        self.__dict__[item] = value


class SwaggerObjectDict(dict):
    """
    Some OpenAPI objects allow for non-standard field names e.g. path names resulting in non pythonic code

    In order to stay true to the specification a separate parent object has been made that inherits from the builtin dict
    """

    def json(self):
        """ Same as SwaggerObject jsonify method """
        json_allowed = [str, list, dict, int, float, type(None), bool]
        obj = {x: y if type(y) in json_allowed else y.json() for x, y in self.copy().items()}

        for x, y in obj.copy().items():
            if type(y) == list:
                obj[x] = [item if type(item) in json_allowed else item.json() for item in y]
            if type(y) == dict:
                for a, b in y.copy().items():
                    obj[x][a] = b if type(b) in json_allowed else b.json()

        for key in obj.copy().keys():
            if key[0] == "_":
                obj[key[1:]] = obj.pop(key)
            if key == "logo":
                obj["x-logo"] = obj.pop(key)

        return remove_none(obj)


class Map(dict):
    """ Dictionary with the added recursive json method """

    def json(self):
        """ Same as SwaggerObject jsonify method """
        json_allowed = [str, list, dict, int, float, type(None), bool]
        obj = {x: y if type(y) in json_allowed else y.json() for x, y in self.copy().items()}

        for x, y in obj.copy().items():
            if type(y) == list:
                obj[x] = [item if type(item) in json_allowed else item.json() for item in y]
            if type(y) == dict:
                for a, b in y.copy().items():
                    obj[x][a] = b if type(b) in json_allowed else b.json()

        for key in obj.copy().keys():
            if key[0] == "_":
                obj[key[1:]] = obj.pop(key)
            if key == "logo":
                obj["x-logo"] = obj.pop(key)

        return obj


def redoc_html(title: str, server: str):
    """
    :param title: The title of the page tab in browsers
    :param server: The server of the api to request the swagger.json from

    Credits: Redocly
    """
    return f"""<!DOCTYPE html>
<html>
  <head>
    <title>{title}</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <link
      href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700"
      rel="stylesheet"
    />
    <style>
      body {{
        margin: 0;
        padding: 0;
      }}
    </style>
  </head>
  <body>
    <redoc spec-url="{server}swagger.json"></redoc>
    <script src="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"></script>
  </body>
</html>"""


def find_openapi_type(var):
    """ Convert python types to OpenAPI type strings """
    var_type = type(var)

    if var_type == str:
        return "string"
    elif var_type == type(None):
        return None
    elif var_type == bool:
        return "boolean"
    elif var_type == dict:
        return "object"
    elif var_type in [int, float]:
        return "number"
    elif var_type == list:
        return "array"


def recursive_generation_of_json_response_schema(obj):
    """
    Creates OpenAPI schema from example response

    Example has been deprecated with possible plans for removal in the latest OpenAPI spec,
     so it is essential to use this instead of just passing an example where possible
    """

    schema = {}

    type = find_openapi_type(obj)  # Find the name of the type of object
    schema["type"] = type

    if type == "object":
        schema["properties"] = {}
        for key, sub_obj in obj.items():
            schema["properties"][key] = recursive_generation_of_json_response_schema(sub_obj)  # Recursion
    elif type == "array":
        schema["items"] = recursive_generation_of_json_response_schema(obj[0])  # Recursion (Limits to the first object)

    return schema
