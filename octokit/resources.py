# -*- coding: utf-8 -*-

"""
octokit.resources
~~~~~~~~~~~~~~~~~

This module contains the workhorse of octokit.py, the Resources.
"""

from .exceptions import handle_status

from inflection import humanize, singularize

class Resource(object):
  """The workhorse of octokit.py, this class makes the API calls and interprets
  them into an accessible schema. The API calls and schema parsing are lazy and
  only happen when an attribute of the resource is requested.
  """

  def __init__(self, session, url=None, schema=None, name=None):
    self.session = session
    self.name = name
    if url:
      self.url = url
      self.schema = {}
    elif schema:
      self.url = schema['url']
      self.schema = self.parse_schema_dict(schema)
    else:
      raise Exception("what the fuck?")

  def __getattr__(self, name):
    self.ensure_schema_loaded()
    if name in self.schema:
      return self.schema[name]
    else:
      raise handle_status(404)

  def __getitem__(self, name):
    self.ensure_schema_loaded()
    return self.schema[name]

  def __repr__(self):
    self.ensure_schema_loaded()
    schema_type = type(self.schema)
    if schema_type == dict:
      subtitle = ", ".join(self.keys())
    elif schema_type == list:
      subtitle = str(len(self.schema))

    return "<Octokit %s(%s)>" % (self.name, subtitle)

  def variables(self):
    return uritemplate.variables(self.url)

  def keys(self):
    self.ensure_schema_loaded()
    return self.schema.keys()

  def ensure_schema_loaded(self):
    if not self.schema:
      self.load_schema()

  def load_schema(self):
    data = self.fetch_resource(self.url)
    data_type = type(data)
    if data_type == dict:
      self.schema = self.parse_schema_dict(data)
    elif data_type == list:
      self.schema = self.parse_schema_list(data, self.name)
    else:
      raise Exception("Unknown type of response from the API.")

  def fetch_resource(self, url):
    response = self.session.get(url)
    handle_status(response.status_code)
    return response.json()

  def parse_schema_dict(self, data):
    schema = {}
    for key in data:
      name = key.split('_url')[0]
      if key.endswith('_url'):
        if data[key]:
          schema[name] = Resource(self.session, url=data[key], name=humanize(name))
        else:
          schema[name] = data[key]
      else:
        data_type = type(data[key])
        if data_type == dict:
          schema[name] = Resource(self.session, schema=data[key], name=humanize(name))
        elif data_type == list:
          schema[name] = self.parse_schema_list(data[key], name=name)
        else:
          schema[name] = data[key]

    return schema

  def parse_schema_list(self, data, name):
    schema = []
    for resource in data:
      name = humanize(singularize(name))
      resource = Resource(self.session, schema=resource, name=name)
      schema.append(resource)

    return schema

