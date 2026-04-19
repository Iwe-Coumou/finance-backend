import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class HTTPClient:
    def __init__(
        self,
        base_url: str,
        headers: dict | None = None,
        api_key: str | None = None,
        api_key_param: str = 'apikey',
        timeout: int = 30,
        retries: int = 3,
    ):
        self.base_url = base_url.rstrip("/")
        self.default_params = {api_key_param: api_key} if api_key else {}
        self.timeout = timeout
        
        self.session = requests.Session()
        if headers:
            self.session.headers.update(headers)
        
        retry = Retry(
            total=retries,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504],
        )
        
        self.session.mount("https://", HTTPAdapter(max_retries=retry))
        self.session.mount("http://", HTTPAdapter(max_retries=retry))
        
    def get(self, path: str, params: dict | None = None, **kwargs) -> requests.Response:
        url = f"{self.base_url}/{path.lstrip('/')}"
        merged = {**self.default_params, **(params or {})}
        try:
            response = self.session.get(url, params=merged, timeout=self.timeout, **kwargs)
            response.raise_for_status()
        except requests.HTTPError as e:
            raise requests.HTTPError(f"{e.response.status_code} Client Error for url: {url}", response=e.response)
        return response
    
    def post(self, path: str, json: dict | None = None, **kwargs) -> requests.Response:
        url = f"{self.base_url}/{path.lstrip('/')}"
        response = self.session.post(url, params=self.default_params, json=json, timeout=self.timeout, **kwargs)
        response.raise_for_status()
        return response