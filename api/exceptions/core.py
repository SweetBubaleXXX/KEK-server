from aiohttp.client import ClientResponse


class NoAvailableStorage(Exception):
    pass


class StorageNotFound(Exception):
    pass


class StorageResponseError(Exception):
    def __init__(self, res: ClientResponse):
        super().__init__(f'{res.method} {res.url} <{res.status}> {res.reason}')
        self.response = res
