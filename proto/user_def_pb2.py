# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: user_def.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='user_def.proto',
  package='',
  syntax='proto3',
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\x0euser_def.proto\"!\n\x04User\x12\x0b\n\x03uid\x18\x01 \x01(\t\x12\x0c\n\x04word\x18\x02 \x03(\t\"A\n\rEnlightenInfo\x12\x0c\n\x04word\x18\x01 \x01(\t\x12\x12\n\nbook_count\x18\x02 \x01(\x05\x12\x0e\n\x06weight\x18\x03 \x01(\x02\"v\n\x05Robot\x12\x0b\n\x03uid\x18\x01 \x01(\t\x12\x1a\n\x02\x65i\x18\x02 \x03(\x0b\x32\x0e.EnlightenInfo\x12!\n\tdetest_ei\x18\x03 \x03(\x0b\x32\x0e.EnlightenInfo\x12!\n\taddict_ei\x18\x04 \x03(\x0b\x32\x0e.EnlightenInfo\";\n\rRobotRegiment\x12\x13\n\x0bregiment_id\x18\x01 \x01(\t\x12\x15\n\x05robot\x18\x02 \x03(\x0b\x32\x06.Robot\">\n\tRobotArmy\x12\x0f\n\x07\x61rmy_id\x18\x01 \x01(\t\x12 \n\x08regiment\x18\x02 \x03(\x0b\x32\x0e.RobotRegimentb\x06proto3'
)




_USER = _descriptor.Descriptor(
  name='User',
  full_name='User',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='uid', full_name='User.uid', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='word', full_name='User.word', index=1,
      number=2, type=9, cpp_type=9, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=18,
  serialized_end=51,
)


_ENLIGHTENINFO = _descriptor.Descriptor(
  name='EnlightenInfo',
  full_name='EnlightenInfo',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='word', full_name='EnlightenInfo.word', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='book_count', full_name='EnlightenInfo.book_count', index=1,
      number=2, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='weight', full_name='EnlightenInfo.weight', index=2,
      number=3, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=53,
  serialized_end=118,
)


_ROBOT = _descriptor.Descriptor(
  name='Robot',
  full_name='Robot',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='uid', full_name='Robot.uid', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='ei', full_name='Robot.ei', index=1,
      number=2, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='detest_ei', full_name='Robot.detest_ei', index=2,
      number=3, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='addict_ei', full_name='Robot.addict_ei', index=3,
      number=4, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=120,
  serialized_end=238,
)


_ROBOTREGIMENT = _descriptor.Descriptor(
  name='RobotRegiment',
  full_name='RobotRegiment',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='regiment_id', full_name='RobotRegiment.regiment_id', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='robot', full_name='RobotRegiment.robot', index=1,
      number=2, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=240,
  serialized_end=299,
)


_ROBOTARMY = _descriptor.Descriptor(
  name='RobotArmy',
  full_name='RobotArmy',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='army_id', full_name='RobotArmy.army_id', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='regiment', full_name='RobotArmy.regiment', index=1,
      number=2, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=301,
  serialized_end=363,
)

_ROBOT.fields_by_name['ei'].message_type = _ENLIGHTENINFO
_ROBOT.fields_by_name['detest_ei'].message_type = _ENLIGHTENINFO
_ROBOT.fields_by_name['addict_ei'].message_type = _ENLIGHTENINFO
_ROBOTREGIMENT.fields_by_name['robot'].message_type = _ROBOT
_ROBOTARMY.fields_by_name['regiment'].message_type = _ROBOTREGIMENT
DESCRIPTOR.message_types_by_name['User'] = _USER
DESCRIPTOR.message_types_by_name['EnlightenInfo'] = _ENLIGHTENINFO
DESCRIPTOR.message_types_by_name['Robot'] = _ROBOT
DESCRIPTOR.message_types_by_name['RobotRegiment'] = _ROBOTREGIMENT
DESCRIPTOR.message_types_by_name['RobotArmy'] = _ROBOTARMY
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

User = _reflection.GeneratedProtocolMessageType('User', (_message.Message,), {
  'DESCRIPTOR' : _USER,
  '__module__' : 'user_def_pb2'
  # @@protoc_insertion_point(class_scope:User)
  })
_sym_db.RegisterMessage(User)

EnlightenInfo = _reflection.GeneratedProtocolMessageType('EnlightenInfo', (_message.Message,), {
  'DESCRIPTOR' : _ENLIGHTENINFO,
  '__module__' : 'user_def_pb2'
  # @@protoc_insertion_point(class_scope:EnlightenInfo)
  })
_sym_db.RegisterMessage(EnlightenInfo)

Robot = _reflection.GeneratedProtocolMessageType('Robot', (_message.Message,), {
  'DESCRIPTOR' : _ROBOT,
  '__module__' : 'user_def_pb2'
  # @@protoc_insertion_point(class_scope:Robot)
  })
_sym_db.RegisterMessage(Robot)

RobotRegiment = _reflection.GeneratedProtocolMessageType('RobotRegiment', (_message.Message,), {
  'DESCRIPTOR' : _ROBOTREGIMENT,
  '__module__' : 'user_def_pb2'
  # @@protoc_insertion_point(class_scope:RobotRegiment)
  })
_sym_db.RegisterMessage(RobotRegiment)

RobotArmy = _reflection.GeneratedProtocolMessageType('RobotArmy', (_message.Message,), {
  'DESCRIPTOR' : _ROBOTARMY,
  '__module__' : 'user_def_pb2'
  # @@protoc_insertion_point(class_scope:RobotArmy)
  })
_sym_db.RegisterMessage(RobotArmy)


# @@protoc_insertion_point(module_scope)
