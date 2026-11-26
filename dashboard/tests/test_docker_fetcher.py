#!/usr/bin/env python3
"""Regression tests for the Docker Engine API fetchers."""
import sys
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import data_fetcher
from data_fetcher import get_docker_logs, get_docker_status


STATS_SAMPLE = {
    'cpu_stats': {
        'cpu_usage': {'total_usage': 200, 'percpu_usage': [1, 2]},
        'system_cpu_usage': 1000,
        'online_cpus': 2,
    },
    'precpu_stats': {'cpu_usage': {'total_usage': 100}, 'system_cpu_usage': 900},
    'memory_stats': {
        'usage': 200 * 1024 * 1024,
        'stats': {'cache': 100 * 1024 * 1024},
        'limit': 400 * 1024 * 1024,
    },
    'pids_stats': {'current': 7},
}


class FakeContainer:
    def __init__(self, container_id, name, image, health=None):
        state = {
            'Status': 'running',
            'Running': True,
            'StartedAt': '2026-11-24T12:00:00.000000000Z',
        }
        if health:
            state['Health'] = {'Status': health}
        self.id = container_id
        self.name = name
        self.attrs = {
            'State': state,
            'Config': {'Image': image},
            'NetworkSettings': {
                'Ports': {'8080/tcp': [{'HostIp': '0.0.0.0', 'HostPort': '3000'}]},
            },
        }

    def logs(self, **kwargs):
        return b'2026-11-25T12:00:00Z line one\n2026-11-25T12:00:01Z line two\n'


class DockerFetcherTests(unittest.TestCase):
    def setUp(self):
        self.containers = [
            FakeContainer('a' * 64, 'web', 'nginx:1.29', 'healthy'),
            FakeContainer('b' * 64, 'worker', 'redis:8.2'),
        ]
        self.client = SimpleNamespace(
            info=lambda: {
                'Containers': 2,
                'ContainersRunning': 2,
                'ContainersStopped': 0,
                'ContainersPaused': 0,
                'Images': 5,
                'ServerVersion': '29.1.3',
            },
            containers=SimpleNamespace(
                list=lambda: self.containers,
                get=lambda name: self.containers[0],
            ),
            api=SimpleNamespace(_version='1.52'),
        )
        for target, replacement in (
            (data_fetcher, '_get_docker_client'),
            (data_fetcher, '_fetch_container_stats'),
        ):
            patcher = patch.object(
                target,
                replacement,
                return_value=(
                    self.client
                    if replacement == '_get_docker_client'
                    else {container.id: STATS_SAMPLE for container in self.containers}
                ),
            )
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_get_docker_status_called_twice_keeps_container_list_intact(self):
        # GIVEN a fake Engine client whose list() always returns the same objects:
        # WHEN the fetcher runs twice with caching bypassed,
        # THEN both results must contain exactly the two original containers:
        first = get_docker_status(force=True)
        second = get_docker_status(force=True)

        self.assertEqual(first['status'], 'ok')
        self.assertEqual(second['status'], 'ok')
        self.assertEqual(len(first['containers']), 2)
        self.assertEqual(len(second['containers']), 2)
        self.assertEqual([item['name'] for item in second['containers']], ['web', 'worker'])

    def test_get_docker_status_maps_engine_fields_to_dashboard_contract(self):
        # GIVEN two running containers with one health check:
        # WHEN status is fetched,
        # THEN image, ports, stats and health use the existing dashboard shape:
        result = get_docker_status(force=True)
        web = next(item for item in result['containers'] if item['name'] == 'web')

        self.assertEqual(web['image'], 'nginx:1.29')
        self.assertEqual(web['ports'], '0.0.0.0:3000->8080/tcp')
        self.assertEqual(web['health'], 'healthy')
        self.assertEqual(web['cpu'], '200.00%')
        self.assertEqual(web['memory_pct'], '25.00%')
        self.assertEqual(web['pids'], 7)
        self.assertEqual(result['docker_version'], '29.1.3')
        self.assertEqual(result['running'], 2)

    def test_get_docker_logs_with_invalid_name_returns_error(self):
        # GIVEN a name that is not a valid Docker container name:
        # WHEN logs are requested,
        # THEN an error payload is returned without calling the engine:
        result = get_docker_logs('bad name; rm -rf /', lines=10)

        self.assertEqual(result['status'], 'error')
        self.assertIn('Invalid container name', result['message'])

    def test_get_docker_logs_with_running_container_returns_lines(self):
        # GIVEN a running container with two timestamped log lines:
        # WHEN logs are requested,
        # THEN decoded lines are returned in order:
        result = get_docker_logs('web', lines=2)

        self.assertEqual(result['status'], 'ok')
        self.assertEqual(len(result['lines']), 2)
        self.assertIn('line one', result['lines'][0])

    def test_start_docker_cache_refresher_warms_cache_and_starts_daemon(self):
        # GIVEN a patchable status fetcher:
        # WHEN the refresher starts,
        # THEN it warms the cache immediately and runs on a daemon thread:
        self.addCleanup(data_fetcher._docker_refresh_stop.set)
        with patch.object(data_fetcher, 'get_docker_status') as mock_status:
            data_fetcher.start_docker_cache_refresher()

        mock_status.assert_called_once_with(force=True)
        refreshers = [
            thread for thread in threading.enumerate()
            if thread.name == 'docker-status-refresher'
        ]
        self.assertTrue(refreshers)
        self.assertTrue(refreshers[0].daemon)


if __name__ == '__main__':
    unittest.main()
