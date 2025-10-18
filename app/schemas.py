from marshmallow import Schema, fields

class BlacklistCreateSchema(Schema):
    email = fields.Email(required=True)
    app_uuid = fields.Str(required=True)
    blocked_reason = fields.Str(required=False, allow_none=True)

class BlacklistGetSchema(Schema):
    blocked = fields.Boolean(required=True)
    email = fields.Email(required=True)
    blocked_reason = fields.Str(allow_none=True)
    created_at = fields.DateTime(allow_none=True)
