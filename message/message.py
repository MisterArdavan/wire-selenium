import json    


class Message:
    def __init__(self, message):
        try:
            self.size = message['size']
            self.text = message['text'] if 'text' in message and message['text'] else None
            self.attachments = message['attachments']
            self.timestamp = message['timestamp'] # in milliseconds
            self.source = message['source'] if 'source' in message else None
            self.groupID = message['groupID'] if 'groupID' in message else None
            self.type = message['type'] if 'type' in message else self.determine_type(message)
            self.id = message['id'] if 'id' in message else None
        except KeyError as err:
            raise KeyError('Messaged should have {} specified'.format(err))

    def determine_type(self, message):
        if self.text is not None:
            if not self.attachments:
                return 'text'
            return 'text with attachments'
        elif self.attachments:
            return 'attachments'
        else:
            return 'unknown'


    def get_timestamp(self):
        return self.timestamp

    def get_text(self):
        return self.text

    def get_type(self):
        return self.type

    def get_attachments(self):
        return self.attachments

    def get_size(self):
        return self.size

    def get_id(self):
        return self.id

    def get_json(self):
        o = {}
        for k in self.__dict__:
            if self.__dict__[k] is not None:
                o[k] = self.__dict__[k]
        return o