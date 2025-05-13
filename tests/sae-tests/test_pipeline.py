import logging
import time

import pytest
from testcontainers.core.container import DockerContainer
from testcontainers.redis import RedisContainer
from testcontainers.core.network import Network

logger = logging.getLogger(__name__)

@pytest.fixture(scope='module')
def container_network():
    with Network() as network:
        yield network


@pytest.fixture(scope='module')
def valkey_container(container_network):
    with RedisContainer("valkey/valkey:8").with_network(container_network).with_network_aliases('valkey') as valkey:
        yield valkey

@pytest.fixture(scope='module')
def video_source_container(valkey_container, container_network):
    print(f'valkey container host: {valkey_container.get_container_host_ip()}')
    
    container_context = DockerContainer("starwitorg/sae-video-source-py:1.1.0")\
        .with_network(container_network)\
        .with_env('REDIS__HOST', 'valkey')\
        .with_env('REDIS__PORT', 6379)\
        .with_env('ID', 'stream1')\
        .with_env('URI', 'rtsp://192.168.176.66:8554/video-stream')\
        .with_env('MAX_FPS', '10')\
        .with_env('JPEG_QUALITY', '95')\
        .with_env('SCALE_WIDTH', '1280')\
        .with_env('LOG_LEVEL', 'DEBUG')\
    
    with container_context as video_source:
        yield video_source

def test_video_source_container(video_source_container):
    time.sleep(5)
    for entry in video_source_container.get_logs():
        for line in entry.decode("utf-8").splitlines():
            logger.error(line)
    assert False