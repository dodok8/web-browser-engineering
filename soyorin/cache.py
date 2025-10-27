import pickle
import abc
from pathlib import Path
from typing import Dict, Optional, NamedTuple
from datetime import datetime
import hashlib


class BrowserCacheKey(NamedTuple):
    url: str

    @staticmethod
    def from_http_info(url_info) -> "BrowserCacheKey":
        """HttpUrlInfo에서 원래 URL을 복원하여 BrowserCacheKey를 생성합니다."""
        url = f"{url_info.scheme}://"

        # username과 password가 있으면 추가
        if url_info.username:
            url += url_info.username
            if url_info.password:
                url += f":{url_info.password}"
            url += "@"

        # host 추가
        if url_info.host:
            url += url_info.host

        # port가 있고 기본 포트가 아니면 추가
        if url_info.port:
            default_port = 443 if url_info.scheme == "https" else 80
            if url_info.port != default_port:
                url += f":{url_info.port}"

        # path 추가
        if url_info.path:
            url += url_info.path

        # query 추가
        if url_info.query:
            url += f"?{url_info.query}"

        return BrowserCacheKey(url=url)


class BrowserCacheEntry(NamedTuple):
    content: str
    max_age: int
    timestamp: Optional[datetime] = None


class Cache(abc.ABC):
    @abc.abstractmethod
    def get(self, browser_cache_key: BrowserCacheKey) -> Optional[BrowserCacheEntry]:
        """캐시에서 엔트리를 가져옵니다."""
        pass

    @abc.abstractmethod
    def set(self, browser_cache_key: BrowserCacheKey, entry: BrowserCacheEntry) -> None:
        """캐시에 엔트리를 저장합니다."""
        pass

    @abc.abstractmethod
    def delete(self, browser_cache_key: BrowserCacheKey) -> None:
        """캐시에서 엔트리를 삭제합니다."""
        pass

    @abc.abstractmethod
    def __contains__(self, browser_cache_key: BrowserCacheKey) -> bool:
        """캐시에 키가 존재하는지 확인합니다."""
        pass


class InMemoryCache(Cache):
    """메모리 기반 캐시 구현"""

    def __init__(self):
        self._cache: Dict[BrowserCacheKey, BrowserCacheEntry] = {}

    def get(self, browser_cache_key: BrowserCacheKey) -> Optional[BrowserCacheEntry]:
        return self._cache.get(browser_cache_key)

    def set(self, browser_cache_key: BrowserCacheKey, entry: BrowserCacheEntry) -> None:
        self._cache[browser_cache_key] = entry

    def delete(self, browser_cache_key: BrowserCacheKey) -> None:
        self._cache.pop(browser_cache_key, None)

    def __contains__(self, browser_cache_key: BrowserCacheKey) -> bool:
        return browser_cache_key in self._cache


class FileCache(Cache):
    """파일 기반 캐시 구현 (pickle 사용)"""

    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def _get_cache_path(self, browser_cache_key: BrowserCacheKey) -> Path:
        """캐시 키를 파일 경로로 변환합니다."""
        # URL을 안전한 파일명으로 변환

        url_hash = hashlib.sha256(browser_cache_key.url.encode()).hexdigest()
        return self.cache_dir / f"{url_hash}.pkl"

    def get(self, browser_cache_key: BrowserCacheKey) -> Optional[BrowserCacheEntry]:
        cache_path = self._get_cache_path(browser_cache_key)
        if not cache_path.exists():
            return None

        try:
            with open(cache_path, "rb") as f:
                return pickle.load(f)
        except (pickle.PickleError, IOError, EOFError):
            # 캐시 파일이 손상된 경우 삭제
            cache_path.unlink(missing_ok=True)
            return None

    def set(self, browser_cache_key: BrowserCacheKey, entry: BrowserCacheEntry) -> None:
        cache_path = self._get_cache_path(browser_cache_key)
        with open(cache_path, "wb") as f:
            pickle.dump(entry, f)

    def delete(self, browser_cache_key: BrowserCacheKey) -> None:
        cache_path = self._get_cache_path(browser_cache_key)
        cache_path.unlink(missing_ok=True)

    def __contains__(self, browser_cache_key: BrowserCacheKey) -> bool:
        cache_path = self._get_cache_path(browser_cache_key)
        return cache_path.exists()
