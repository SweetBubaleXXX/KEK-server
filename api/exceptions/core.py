from aiohttp.client import ClientResponse


class NoAvailableStorage(Exception):
    pass


class StorageNotFound(Exception):
    pass


class StorageResponseError(Exception):
    def __init__(self, response: ClientResponse):
        super().__init__(f"Status code <{response.status}>")
        self.response = response
