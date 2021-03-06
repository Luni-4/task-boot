# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import logging
import os
from typing import IO
from typing import Any
from typing import Dict

import taskcluster
import yaml

logger = logging.getLogger(__name__)

TASKCLUSTER_DEFAULT_URL = "https://taskcluster.net"


class Configuration(object):
    config: Dict[str, Any] = {}

    def __init__(self, args: argparse.Namespace) -> None:
        if args.secret:
            self.load_secret(args.secret)
        elif args.config:
            self.load_config(args.config)
        else:
            logger.warn("No configuration available")

    def __getattr__(self, key: str) -> Any:
        if key in self.config:
            return self.config[key]
        raise KeyError

    def get_root_url(self) -> str:
        if "TASKCLUSTER_ROOT_URL" in os.environ:
            return os.environ["TASKCLUSTER_ROOT_URL"]
        return TASKCLUSTER_DEFAULT_URL

    def get_taskcluster_options(self) -> Dict[str, Any]:
        """
        Helper to get the Taskcluster setup options
        according to current environment (local or Taskcluster)
        """
        options = taskcluster.optionsFromEnvironment()
        proxy_url = os.environ.get("TASKCLUSTER_PROXY_URL")

        if proxy_url is not None:
            # Always use proxy url when available
            options["rootUrl"] = proxy_url

        if "rootUrl" not in options:
            # Always have a value in root url
            options["rootUrl"] = TASKCLUSTER_DEFAULT_URL

        return options

    def load_secret(self, name: str) -> None:
        secrets = taskcluster.Secrets(self.get_taskcluster_options())
        logging.info("Loading Taskcluster secret {}".format(name))
        payload = secrets.get(name)
        assert "secret" in payload, "Missing secret value"
        self.config = payload["secret"]

    def load_config(self, fileobj: IO) -> None:
        self.config = yaml.safe_load(fileobj)
        assert isinstance(self.config, dict), "Invalid YAML structure"

    def has_docker_auth(self) -> bool:
        docker = self.config.get("docker")
        if docker is None:
            return False
        return "registry" in docker and "username" in docker and "password" in docker

    def has_aws_auth(self) -> bool:
        aws = self.config.get("aws")
        if aws is None:
            return False
        return "access_key_id" in aws and "secret_access_key" in aws

    def has_pypi_auth(self) -> bool:
        pypi = self.config.get("pypi")
        if pypi is None:
            return False
        return "username" in pypi and "password" in pypi

    def has_git_auth(self) -> bool:
        git = self.config.get("git")
        if git is None:
            return False
        return "token" in git

    def has_cargo_auth(self) -> bool:
        cargo = self.config.get("cargo")
        if cargo is None:
            return False
        return "token" in cargo
