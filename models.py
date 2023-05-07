from mongoengine import Document, PointField, StringField, ReferenceField, DateTimeField


class User(Document):
    user_type = StringField(required=True)
    email = StringField(required=True)
    password = StringField(required=True)
    first_name = StringField(required=True)
    last_name = StringField(required=True)
    modified = DateTimeField(required=True)


class Robot(Document):
    serial_no = StringField(required=True)
    user_id = StringField(required=False)
    master = StringField(required=False)
    status = StringField(required=True)
    location = PointField()
    modified = DateTimeField(required=True)
