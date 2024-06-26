from dependency import *

class JSONLoader:
    def __init__(self, data: Union[str, Dict[str, Any]], jq_schema: str, text_content: bool = False):
        if isinstance(data, str):
            self.data = json.loads(data)
        else:
            self.data = data
        self.jq_schema = jq_schema
        self.text_content = text_content

    def load(self):
        import jq
        return jq.compile(self.jq_schema).input(self.data).all()

class Document:
    def __init__(self, page_content: str, metadata: Dict[str, Any] = None):
        self.page_content = page_content
        self.metadata = metadata or {}