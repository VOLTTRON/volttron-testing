# -*- coding: utf-8 -*- {{{
# ===----------------------------------------------------------------------===
#
#                 Installable Component of Eclipse VOLTTRON
#
# ===----------------------------------------------------------------------===
#
# Copyright 2022 Battelle Memorial Institute
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# ===----------------------------------------------------------------------===
# }}}
import os

import pytest

from volttrontesting.platformwrapper import PlatformWrapper, with_os_environ, create_server_options
from volttrontesting.fixtures.volttron_platform_fixtures import volttron_instance
from volttrontesting.fixtures import get_pyproject_toml
from pathlib import Path


def test_can_enable_sys_queue(get_pyproject_toml):
    options = create_server_options()

    p = PlatformWrapper(options=options, project_toml_file=get_pyproject_toml, enable_sys_queue=True)

    for data in p.pop_stdout_queue():
        assert data
        p.shutdown_platform()

    p.cleanup()


def test_value_error_raised_sys_queue(get_pyproject_toml):
    options = create_server_options()

    p = PlatformWrapper(options=options, project_toml_file=get_pyproject_toml)

    with pytest.raises(ValueError):
        for data in p.pop_stdout_queue():
            pass

    with pytest.raises(ValueError):
        for data in p.clear_stdout_queue():
            pass

    p.shutdown_platform()

    p.cleanup()


def test_install_library(get_pyproject_toml):
    options = create_server_options()

    p = PlatformWrapper(options=options, project_toml_file=get_pyproject_toml)
    try:
        p.install_library("pint")
        values = p.show()

        assert next(filter(lambda x: x.strip().startswith("pint"), values))

    finally:
        p.shutdown_platform()
        p.cleanup()

def test_will_update_environ():
    to_update = dict(farthing="50")
    with with_os_environ(to_update):
        assert os.environ.get("farthing") == "50"

    assert "farthing" not in os.environ


@pytest.mark.parametrize("auth_enabled", [
    True,
    # False
])
def test_can_create_platform_wrapper(auth_enabled: bool, get_pyproject_toml: Path):
    options = create_server_options()
    options.auth_enabled = auth_enabled
    p = PlatformWrapper(options=options, project_toml_file=get_pyproject_toml)
    try:
        assert p.is_running()
        assert p.volttron_home.startswith("/tmp/tmp")
    finally:
        p.shutdown_platform()

    assert not p.is_running()
    p.cleanup()

def test_not_cleanup_works(get_pyproject_toml: Path):
    options = create_server_options()
    options.auth_enabled = True
    p = PlatformWrapper(options=options, project_toml_file=get_pyproject_toml, skip_cleanup=True)
    try:
        assert p.is_running()
        assert p.volttron_home.startswith("/tmp/tmp")
        agent_uuid = p.install_from_github(org="eclipse-volttron", repo="volttron-listener", branch="v10")
        assert agent_uuid
    finally:
        if p:
            p.shutdown_platform()
            assert Path(p.volttron_home).exists()
            for d in p._added_from_github:
                assert d.exists()
    assert not p.is_running()
    p.cleanup()

def test_fixture_creation(volttron_instance):
    vi = volttron_instance
    if not vi.is_running():
        vi.startup_platform()
    assert vi.is_running()
    vi.stop_platform()
    assert not vi.is_running()


def test_install_agent_pypi(volttron_instance):
    vi = volttron_instance
    if not vi.is_running():
        vi.startup_platform()
    try:
        agent_uuid = vi.install_agent()
        assert agent_uuid
        assert vi.list_agents()
    finally:
        vi.remove_all_agents()
        assert len(vi.list_agents()) == 0

def test_install_agent_from_github(volttron_instance):
    vi = volttron_instance
    if not vi.is_running():
        vi.startup_platform()
    try:
        agent_uuid = vi.install_from_github(org="eclipse-volttron",
                                            repo="volttron-listener",
                                            branch="v10")
        assert agent_uuid
        assert vi.is_agent_running(agent_uuid)
        assert vi.list_agents()
        vi.stop_agent(agent_uuid=agent_uuid)
        assert not vi.is_agent_running(agent_uuid)
        vi.start_agent(agent_uuid)
        assert vi.is_agent_running(agent_uuid)
        current_pid = vi.agent_pid(agent_uuid)
        vi.restart_agent(agent_uuid)
        new_pid = vi.agent_pid(agent_uuid)
        assert current_pid != new_pid
    finally:
        vi.remove_all_agents()
        assert len(vi.list_agents()) == 0

