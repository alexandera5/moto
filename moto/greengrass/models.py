import uuid
from collections import OrderedDict
from datetime import datetime
import re

from moto.core import BaseBackend, BaseModel, get_account_id
from moto.core.utils import BackendDict, iso_8601_datetime_with_milliseconds
from .exceptions import (
    GreengrassClientError,
    IdNotFoundException,
    InvalidInputException,
    InvalidContainerDefinitionException,
    VersionNotFoundException,
)


class FakeCoreDefinition(BaseModel):
    def __init__(self, region_name, name):
        self.region_name = region_name
        self.name = name
        self.id = str(uuid.uuid4())
        self.arn = f"arn:aws:greengrass:{region_name}:{get_account_id()}:greengrass/definition/cores/{self.id}"
        self.created_at_datetime = datetime.utcnow()
        self.latest_version = ""
        self.latest_version_arn = ""

    def to_dict(self):
        return {
            "Arn": self.arn,
            "CreationTimestamp": iso_8601_datetime_with_milliseconds(
                self.created_at_datetime
            ),
            "Id": self.id,
            "LastUpdatedTimestamp": iso_8601_datetime_with_milliseconds(
                self.created_at_datetime
            ),
            "LatestVersion": self.latest_version,
            "LatestVersionArn": self.latest_version_arn,
            "Name": self.name,
        }


class FakeCoreDefinitionVersion(BaseModel):
    def __init__(self, region_name, core_definition_id, definition):
        self.region_name = region_name
        self.core_definition_id = core_definition_id
        self.definition = definition
        self.version = str(uuid.uuid4())
        self.arn = f"arn:aws:greengrass:{region_name}:{get_account_id()}:greengrass/definition/cores/{self.core_definition_id}/versions/{self.version}"
        self.created_at_datetime = datetime.utcnow()

    def to_dict(self, include_detail=False):
        obj = {
            "Arn": self.arn,
            "CreationTimestamp": iso_8601_datetime_with_milliseconds(
                self.created_at_datetime
            ),
            "Id": self.core_definition_id,
            "Version": self.version,
        }

        if include_detail:
            obj["Definition"] = self.definition

        return obj


class FakeDeviceDefinition(BaseModel):
    def __init__(self, region_name, name, initial_version):
        self.region_name = region_name
        self.id = str(uuid.uuid4())
        self.arn = f"arn:aws:greengrass:{region_name}:{get_account_id()}:greengrass/definition/devices/{self.id}"
        self.created_at_datetime = datetime.utcnow()
        self.update_at_datetime = datetime.utcnow()
        self.latest_version = ""
        self.latest_version_arn = ""
        self.name = name
        self.initial_version = initial_version

    def to_dict(self):
        res = {
            "Arn": self.arn,
            "CreationTimestamp": iso_8601_datetime_with_milliseconds(
                self.created_at_datetime
            ),
            "Id": self.id,
            "LastUpdatedTimestamp": iso_8601_datetime_with_milliseconds(
                self.update_at_datetime
            ),
            "LatestVersion": self.latest_version,
            "LatestVersionArn": self.latest_version_arn,
        }
        if self.name is not None:
            res["Name"] = self.name
        return res


class FakeDeviceDefinitionVersion(BaseModel):
    def __init__(self, region_name, device_definition_id, devices):
        self.region_name = region_name
        self.device_definition_id = device_definition_id
        self.devices = devices
        self.version = str(uuid.uuid4())
        self.arn = f"arn:aws:greengrass:{region_name}:{get_account_id()}:greengrass/definition/devices/{self.device_definition_id}/versions/{self.version}"
        self.created_at_datetime = datetime.utcnow()

    def to_dict(self, include_detail=False):
        obj = {
            "Arn": self.arn,
            "CreationTimestamp": iso_8601_datetime_with_milliseconds(
                self.created_at_datetime
            ),
            "Id": self.device_definition_id,
            "Version": self.version,
        }

        if include_detail:
            obj["Definition"] = {"Devices": self.devices}

        return obj


class FakeResourceDefinition(BaseModel):
    def __init__(self, region_name, name, initial_version):
        self.region_name = region_name
        self.id = str(uuid.uuid4())
        self.arn = f"arn:aws:greengrass:{region_name}:{get_account_id()}:greengrass/definition/resources/{self.id}"
        self.created_at_datetime = datetime.utcnow()
        self.update_at_datetime = datetime.utcnow()
        self.latest_version = ""
        self.latest_version_arn = ""
        self.name = name
        self.initial_version = initial_version

    def to_dict(self):
        return {
            "Arn": self.arn,
            "CreationTimestamp": iso_8601_datetime_with_milliseconds(
                self.created_at_datetime
            ),
            "Id": self.id,
            "LastUpdatedTimestamp": iso_8601_datetime_with_milliseconds(
                self.update_at_datetime
            ),
            "LatestVersion": self.latest_version,
            "LatestVersionArn": self.latest_version_arn,
            "Name": self.name,
        }


class FakeResourceDefinitionVersion(BaseModel):
    def __init__(self, region_name, resource_definition_id, resources):
        self.region_name = region_name
        self.resource_definition_id = resource_definition_id
        self.resources = resources
        self.version = str(uuid.uuid4())
        self.arn = f"arn:aws:greengrass:{region_name}:{get_account_id()}:greengrass/definition/resources/{self.resource_definition_id}/versions/{self.version}"
        self.created_at_datetime = datetime.utcnow()

    def to_dict(self):
        return {
            "Arn": self.arn,
            "CreationTimestamp": iso_8601_datetime_with_milliseconds(
                self.created_at_datetime
            ),
            "Definition": {"Resources": self.resources},
            "Id": self.resource_definition_id,
            "Version": self.version,
        }


class FakeFunctionDefinition(BaseModel):
    def __init__(self, region_name, name, initial_version):
        self.region_name = region_name
        self.id = str(uuid.uuid4())
        self.arn = f"arn:aws:greengrass:{self.region_name}:{get_account_id()}:greengrass/definition/functions/{self.id}"
        self.created_at_datetime = datetime.utcnow()
        self.update_at_datetime = datetime.utcnow()
        self.latest_version = ""
        self.latest_version_arn = ""
        self.name = name
        self.initial_version = initial_version

    def to_dict(self):
        res = {
            "Arn": self.arn,
            "CreationTimestamp": iso_8601_datetime_with_milliseconds(
                self.created_at_datetime
            ),
            "Id": self.id,
            "LastUpdatedTimestamp": iso_8601_datetime_with_milliseconds(
                self.update_at_datetime
            ),
            "LatestVersion": self.latest_version,
            "LatestVersionArn": self.latest_version_arn,
        }
        if self.name is not None:
            res["Name"] = self.name
        return res


class FakeFunctionDefinitionVersion(BaseModel):
    def __init__(self, region_name, function_definition_id, functions, default_config):
        self.region_name = region_name
        self.function_definition_id = function_definition_id
        self.functions = functions
        self.default_config = default_config
        self.version = str(uuid.uuid4())
        self.arn = f"arn:aws:greengrass:{self.region_name}:{get_account_id()}:greengrass/definition/functions/{self.function_definition_id}/versions/{self.version}"
        self.created_at_datetime = datetime.utcnow()

    def to_dict(self):
        return {
            "Arn": self.arn,
            "CreationTimestamp": iso_8601_datetime_with_milliseconds(
                self.created_at_datetime
            ),
            "Definition": {"Functions": self.functions},
            "Id": self.function_definition_id,
            "Version": self.version,
        }


class FakeSubscriptionDefinition(BaseModel):
    def __init__(self, region_name, name, initial_version):
        self.region_name = region_name
        self.id = str(uuid.uuid4())
        self.arn = f"arn:aws:greengrass:{self.region_name}:{get_account_id()}:greengrass/definition/subscriptions/{self.id}"
        self.created_at_datetime = datetime.utcnow()
        self.update_at_datetime = datetime.utcnow()
        self.latest_version = ""
        self.latest_version_arn = ""
        self.name = name
        self.initial_version = initial_version

    def to_dict(self):
        return {
            "Arn": self.arn,
            "CreationTimestamp": iso_8601_datetime_with_milliseconds(
                self.created_at_datetime
            ),
            "Id": self.id,
            "LastUpdatedTimestamp": iso_8601_datetime_with_milliseconds(
                self.update_at_datetime
            ),
            "LatestVersion": self.latest_version,
            "LatestVersionArn": self.latest_version_arn,
            "Name": self.name,
        }


class FakeSubscriptionDefinitionVersion(BaseModel):
    def __init__(self, region_name, subscription_definition_id, subscriptions):
        self.region_name = region_name
        self.subscription_definition_id = subscription_definition_id
        self.subscriptions = subscriptions
        self.version = str(uuid.uuid4())
        self.arn = f"arn:aws:greengrass:{self.region_name}:{get_account_id()}:greengrass/definition/subscriptions/{self.subscription_definition_id}/versions/{self.version}"
        self.created_at_datetime = datetime.utcnow()

    def to_dict(self):
        return {
            "Arn": self.arn,
            "CreationTimestamp": iso_8601_datetime_with_milliseconds(
                self.created_at_datetime
            ),
            "Definition": {"Subscriptions": self.subscriptions},
            "Id": self.subscription_definition_id,
            "Version": self.version,
        }


class FakeGroup(BaseModel):
    def __init__(self, region_name, name):
        self.region_name = region_name
        self.group_id = str(uuid.uuid4())
        self.name = name
        self.arn = f"arn:aws:greengrass:{self.region_name}:{get_account_id()}:greengrass/groups/{self.group_id}"
        self.created_at_datetime = datetime.utcnow()
        self.last_updated_datetime = datetime.utcnow()
        self.latest_version = ""
        self.latest_version_arn = ""

    def to_dict(self):
        obj = {
            "Arn": self.arn,
            "CreationTimestamp": iso_8601_datetime_with_milliseconds(
                self.created_at_datetime
            ),
            "Id": self.group_id,
            "LastUpdatedTimestamp": iso_8601_datetime_with_milliseconds(
                self.last_updated_datetime
            ),
            "LatestVersion": self.latest_version,
            "LatestVersionArn": self.latest_version_arn,
            "Name": self.name,
        }
        return obj


class FakeGroupVersion(BaseModel):
    def __init__(
        self,
        region_name,
        group_id,
        core_definition_version_arn,
        device_definition_version_arn,
        function_definition_version_arn,
        resource_definition_version_arn,
        subscription_definition_version_arn,
    ):
        self.region_name = region_name
        self.group_id = group_id
        self.version = str(uuid.uuid4())
        self.arn = f"arn:aws:greengrass:{self.region_name}:{get_account_id()}:greengrass/groups/{self.group_id}/versions/{self.version}"
        self.created_at_datetime = datetime.utcnow()
        self.core_definition_version_arn = core_definition_version_arn
        self.device_definition_version_arn = device_definition_version_arn
        self.function_definition_version_arn = function_definition_version_arn
        self.resource_definition_version_arn = resource_definition_version_arn
        self.subscription_definition_version_arn = subscription_definition_version_arn

    def to_dict(self, include_detail=False):

        definition = {}
        if self.core_definition_version_arn:
            definition["CoreDefinitionVersionArn"] = self.core_definition_version_arn

        if self.device_definition_version_arn:
            definition[
                "DeviceDefinitionVersionArn"
            ] = self.device_definition_version_arn

        if self.function_definition_version_arn:
            definition[
                "FunctionDefinitionVersionArn"
            ] = self.function_definition_version_arn

        if self.resource_definition_version_arn:
            definition[
                "ResourceDefinitionVersionArn"
            ] = self.resource_definition_version_arn

        if self.subscription_definition_version_arn:
            definition[
                "SubscriptionDefinitionVersionArn"
            ] = self.subscription_definition_version_arn

        obj = {
            "Arn": self.arn,
            "CreationTimestamp": iso_8601_datetime_with_milliseconds(
                self.created_at_datetime
            ),
            "Id": self.group_id,
            "Version": self.version,
        }

        if include_detail:
            obj["Definition"] = definition

        return obj


class GreengrassBackend(BaseBackend):
    def __init__(self, region_name, account_id):
        super().__init__(region_name, account_id)
        self.groups = OrderedDict()
        self.group_versions = OrderedDict()
        self.core_definitions = OrderedDict()
        self.core_definition_versions = OrderedDict()
        self.device_definitions = OrderedDict()
        self.device_definition_versions = OrderedDict()
        self.function_definitions = OrderedDict()
        self.function_definition_versions = OrderedDict()
        self.resource_definitions = OrderedDict()
        self.resource_definition_versions = OrderedDict()
        self.subscription_definitions = OrderedDict()
        self.subscription_definition_versions = OrderedDict()
        self.deployments = OrderedDict()

    def create_core_definition(self, name, initial_version):

        core_definition = FakeCoreDefinition(self.region_name, name)
        self.core_definitions[core_definition.id] = core_definition
        self.create_core_definition_version(
            core_definition.id, initial_version["Cores"]
        )
        return core_definition

    def list_core_definitions(self):
        return self.core_definitions.values()

    def get_core_definition(self, core_definition_id):

        if core_definition_id not in self.core_definitions:
            raise IdNotFoundException("That Core List Definition does not exist")
        return self.core_definitions[core_definition_id]

    def delete_core_definition(self, core_definition_id):
        if core_definition_id not in self.core_definitions:
            raise IdNotFoundException("That cores definition does not exist.")
        del self.core_definitions[core_definition_id]
        del self.core_definition_versions[core_definition_id]

    def update_core_definition(self, core_definition_id, name):

        if name == "":
            raise InvalidContainerDefinitionException(
                "Input does not contain any attributes to be updated"
            )
        if core_definition_id not in self.core_definitions:
            raise IdNotFoundException("That cores definition does not exist.")
        self.core_definitions[core_definition_id].name = name

    def create_core_definition_version(self, core_definition_id, cores):

        definition = {"Cores": cores}
        core_def_ver = FakeCoreDefinitionVersion(
            self.region_name, core_definition_id, definition
        )
        core_def_vers = self.core_definition_versions.get(
            core_def_ver.core_definition_id, {}
        )
        core_def_vers[core_def_ver.version] = core_def_ver
        self.core_definition_versions[core_def_ver.core_definition_id] = core_def_vers

        self.core_definitions[core_definition_id].latest_version = core_def_ver.version
        self.core_definitions[core_definition_id].latest_version_arn = core_def_ver.arn

        return core_def_ver

    def list_core_definition_versions(self, core_definition_id):

        if core_definition_id not in self.core_definitions:
            raise IdNotFoundException("That cores definition does not exist.")
        return self.core_definition_versions[core_definition_id].values()

    def get_core_definition_version(
        self, core_definition_id, core_definition_version_id
    ):

        if core_definition_id not in self.core_definitions:
            raise IdNotFoundException("That cores definition does not exist.")

        if (
            core_definition_version_id
            not in self.core_definition_versions[core_definition_id]
        ):
            raise VersionNotFoundException(
                f"Version {core_definition_version_id} of Core List Definition {core_definition_id} does not exist."
            )

        return self.core_definition_versions[core_definition_id][
            core_definition_version_id
        ]

    def create_device_definition(self, name, initial_version):
        device_def = FakeDeviceDefinition(self.region_name, name, initial_version)
        self.device_definitions[device_def.id] = device_def
        init_ver = device_def.initial_version
        init_device_def = init_ver.get("Devices", {})
        self.create_device_definition_version(device_def.id, init_device_def)

        return device_def

    def list_device_definitions(self):
        return self.device_definitions.values()

    def create_device_definition_version(self, device_definition_id, devices):

        if device_definition_id not in self.device_definitions:
            raise IdNotFoundException("That devices definition does not exist.")

        device_ver = FakeDeviceDefinitionVersion(
            self.region_name, device_definition_id, devices
        )
        device_vers = self.device_definition_versions.get(
            device_ver.device_definition_id, {}
        )
        device_vers[device_ver.version] = device_ver
        self.device_definition_versions[device_ver.device_definition_id] = device_vers
        self.device_definitions[
            device_definition_id
        ].latest_version = device_ver.version
        self.device_definitions[
            device_definition_id
        ].latest_version_arn = device_ver.arn

        return device_ver

    def list_device_definition_versions(self, device_definition_id):

        if device_definition_id not in self.device_definitions:
            raise IdNotFoundException("That devices definition does not exist.")
        return self.device_definition_versions[device_definition_id].values()

    def get_device_definition(self, device_definition_id):

        if device_definition_id not in self.device_definitions:
            raise IdNotFoundException("That Device List Definition does not exist.")
        return self.device_definitions[device_definition_id]

    def delete_device_definition(self, device_definition_id):
        if device_definition_id not in self.device_definitions:
            raise IdNotFoundException("That devices definition does not exist.")
        del self.device_definitions[device_definition_id]
        del self.device_definition_versions[device_definition_id]

    def update_device_definition(self, device_definition_id, name):

        if name == "":
            raise InvalidContainerDefinitionException(
                "Input does not contain any attributes to be updated"
            )
        if device_definition_id not in self.device_definitions:
            raise IdNotFoundException("That devices definition does not exist.")
        self.device_definitions[device_definition_id].name = name

    def get_device_definition_version(
        self, device_definition_id, device_definition_version_id
    ):

        if device_definition_id not in self.device_definitions:
            raise IdNotFoundException("That devices definition does not exist.")

        if (
            device_definition_version_id
            not in self.device_definition_versions[device_definition_id]
        ):
            raise VersionNotFoundException(
                f"Version {device_definition_version_id} of Device List Definition {device_definition_id} does not exist."
            )

        return self.device_definition_versions[device_definition_id][
            device_definition_version_id
        ]

    def create_resource_definition(self, name, initial_version):

        resources = initial_version.get("Resources", [])
        GreengrassBackend._validate_resources(resources)

        resource_def = FakeResourceDefinition(self.region_name, name, initial_version)
        self.resource_definitions[resource_def.id] = resource_def
        init_ver = resource_def.initial_version
        resources = init_ver.get("Resources", {})
        self.create_resource_definition_version(resource_def.id, resources)

        return resource_def

    def list_resource_definitions(self):
        return self.resource_definitions

    def get_resource_definition(self, resource_definition_id):

        if resource_definition_id not in self.resource_definitions:
            raise IdNotFoundException("That Resource List Definition does not exist.")
        return self.resource_definitions[resource_definition_id]

    def delete_resource_definition(self, resource_definition_id):
        if resource_definition_id not in self.resource_definitions:
            raise IdNotFoundException("That resources definition does not exist.")
        del self.resource_definitions[resource_definition_id]
        del self.resource_definition_versions[resource_definition_id]

    def update_resource_definition(self, resource_definition_id, name):

        if name == "":
            raise InvalidInputException("Invalid resource name.")
        if resource_definition_id not in self.resource_definitions:
            raise IdNotFoundException("That resources definition does not exist.")
        self.resource_definitions[resource_definition_id].name = name

    def create_resource_definition_version(self, resource_definition_id, resources):

        if resource_definition_id not in self.resource_definitions:
            raise IdNotFoundException("That resource definition does not exist.")

        GreengrassBackend._validate_resources(resources)

        resource_def_ver = FakeResourceDefinitionVersion(
            self.region_name, resource_definition_id, resources
        )

        resources_ver = self.resource_definition_versions.get(
            resource_def_ver.resource_definition_id, {}
        )
        resources_ver[resource_def_ver.version] = resource_def_ver
        self.resource_definition_versions[
            resource_def_ver.resource_definition_id
        ] = resources_ver

        self.resource_definitions[
            resource_definition_id
        ].latest_version = resource_def_ver.version

        self.resource_definitions[
            resource_definition_id
        ].latest_version_arn = resource_def_ver.arn

        return resource_def_ver

    def list_resource_definition_versions(self, resource_definition_id):

        if resource_definition_id not in self.resource_definition_versions:
            raise IdNotFoundException("That resources definition does not exist.")

        return self.resource_definition_versions[resource_definition_id].values()

    def get_resource_definition_version(
        self, resource_definition_id, resource_definition_version_id
    ):

        if resource_definition_id not in self.resource_definition_versions:
            raise IdNotFoundException("That resources definition does not exist.")

        if (
            resource_definition_version_id
            not in self.resource_definition_versions[resource_definition_id]
        ):
            raise VersionNotFoundException(
                f"Version {resource_definition_version_id} of Resource List Definition {resource_definition_id} does not exist."
            )

        return self.resource_definition_versions[resource_definition_id][
            resource_definition_version_id
        ]

    @staticmethod
    def _validate_resources(resources):
        for resource in resources:
            volume_source_path = (
                resource.get("ResourceDataContainer", {})
                .get("LocalVolumeResourceData", {})
                .get("SourcePath", "")
            )
            if volume_source_path == "/sys" or volume_source_path.startswith("/sys/"):
                raise GreengrassClientError(
                    "400",
                    "The resources definition is invalid. (ErrorDetails: [Accessing /sys is prohibited])",
                )

            local_device_resource_data = resource.get("ResourceDataContainer", {}).get(
                "LocalDeviceResourceData", {}
            )
            if local_device_resource_data:
                device_source_path = local_device_resource_data["SourcePath"]
                if not device_source_path.startswith("/dev"):
                    raise GreengrassClientError(
                        "400",
                        f"The resources definition is invalid. (ErrorDetails: [Device resource path should begin with "
                        "/dev"
                        f", but got: {device_source_path}])",
                    )

    def create_function_definition(self, name, initial_version):
        func_def = FakeFunctionDefinition(self.region_name, name, initial_version)
        self.function_definitions[func_def.id] = func_def
        init_ver = func_def.initial_version
        init_func_def = init_ver.get("Functions", {})
        init_config = init_ver.get("DefaultConfig", {})
        self.create_function_definition_version(func_def.id, init_func_def, init_config)

        return func_def

    def list_function_definitions(self):
        return self.function_definitions.values()

    def get_function_definition(self, function_definition_id):

        if function_definition_id not in self.function_definitions:
            raise IdNotFoundException("That Lambda List Definition does not exist.")
        return self.function_definitions[function_definition_id]

    def delete_function_definition(self, function_definition_id):
        if function_definition_id not in self.function_definitions:
            raise IdNotFoundException("That lambdas definition does not exist.")
        del self.function_definitions[function_definition_id]
        del self.function_definition_versions[function_definition_id]

    def update_function_definition(self, function_definition_id, name):

        if name == "":
            raise InvalidContainerDefinitionException(
                "Input does not contain any attributes to be updated"
            )
        if function_definition_id not in self.function_definitions:
            raise IdNotFoundException("That lambdas definition does not exist.")
        self.function_definitions[function_definition_id].name = name

    def create_function_definition_version(
        self, function_definition_id, functions, default_config
    ):

        if function_definition_id not in self.function_definitions:
            raise IdNotFoundException("That lambdas does not exist.")

        func_ver = FakeFunctionDefinitionVersion(
            self.region_name, function_definition_id, functions, default_config
        )
        func_vers = self.function_definition_versions.get(
            func_ver.function_definition_id, {}
        )
        func_vers[func_ver.version] = func_ver
        self.function_definition_versions[func_ver.function_definition_id] = func_vers
        self.function_definitions[
            function_definition_id
        ].latest_version = func_ver.version
        self.function_definitions[
            function_definition_id
        ].latest_version_arn = func_ver.arn

        return func_ver

    def list_function_definition_versions(self, function_definition_id):
        if function_definition_id not in self.function_definition_versions:
            raise IdNotFoundException("That lambdas definition does not exist.")
        return self.function_definition_versions[function_definition_id]

    def get_function_definition_version(
        self, function_definition_id, function_definition_version_id
    ):

        if function_definition_id not in self.function_definition_versions:
            raise IdNotFoundException("That lambdas definition does not exist.")

        if (
            function_definition_version_id
            not in self.function_definition_versions[function_definition_id]
        ):
            raise IdNotFoundException(
                f"Version {function_definition_version_id} of Lambda List Definition {function_definition_id} does not exist."
            )

        return self.function_definition_versions[function_definition_id][
            function_definition_version_id
        ]

    @staticmethod
    def _is_valid_subscription_target_or_source(target_or_source):

        if target_or_source in ["cloud", "GGShadowService"]:
            return True

        if re.match(
            r"^arn:aws:iot:[a-zA-Z0-9-]+:[0-9]{12}:thing/[a-zA-Z0-9-]+$",
            target_or_source,
        ):
            return True

        if re.match(
            r"^arn:aws:lambda:[a-zA-Z0-9-]+:[0-9]{12}:function:[a-zA-Z0-9-_]+:[a-zA-Z0-9-_]+$",
            target_or_source,
        ):
            return True

        return False

    @staticmethod
    def _validate_subscription_target_or_source(subscriptions):

        target_errors = []
        source_errors = []

        for subscription in subscriptions:
            subscription_id = subscription["Id"]
            source = subscription["Source"]
            target = subscription["Target"]

            if not GreengrassBackend._is_valid_subscription_target_or_source(source):
                target_errors.append(
                    f"Subscription source is invalid. ID is '{subscription_id}' and Source is '{source}'"
                )

            if not GreengrassBackend._is_valid_subscription_target_or_source(target):
                target_errors.append(
                    f"Subscription target is invalid. ID is '{subscription_id}' and Target is '{target}'"
                )

        if source_errors:
            error_msg = ", ".join(source_errors)
            raise GreengrassClientError(
                "400",
                f"The subscriptions definition is invalid or corrupted. (ErrorDetails: [{error_msg}])",
            )

        if target_errors:
            error_msg = ", ".join(target_errors)
            raise GreengrassClientError(
                "400",
                f"The subscriptions definition is invalid or corrupted. (ErrorDetails: [{error_msg}])",
            )

    def create_subscription_definition(self, name, initial_version):

        GreengrassBackend._validate_subscription_target_or_source(
            initial_version["Subscriptions"]
        )

        sub_def = FakeSubscriptionDefinition(self.region_name, name, initial_version)
        self.subscription_definitions[sub_def.id] = sub_def
        init_ver = sub_def.initial_version
        subscriptions = init_ver.get("Subscriptions", {})
        sub_def_ver = self.create_subscription_definition_version(
            sub_def.id, subscriptions
        )

        sub_def.latest_version = sub_def_ver.version
        sub_def.latest_version_arn = sub_def_ver.arn
        return sub_def

    def list_subscription_definitions(self):
        return self.subscription_definitions.values()

    def get_subscription_definition(self, subscription_definition_id):

        if subscription_definition_id not in self.subscription_definitions:
            raise IdNotFoundException(
                "That Subscription List Definition does not exist."
            )
        return self.subscription_definitions[subscription_definition_id]

    def delete_subscription_definition(self, subscription_definition_id):
        if subscription_definition_id not in self.subscription_definitions:
            raise IdNotFoundException("That subscriptions definition does not exist.")
        del self.subscription_definitions[subscription_definition_id]
        del self.subscription_definition_versions[subscription_definition_id]

    def update_subscription_definition(self, subscription_definition_id, name):

        if name == "":
            raise InvalidContainerDefinitionException(
                "Input does not contain any attributes to be updated"
            )
        if subscription_definition_id not in self.subscription_definitions:
            raise IdNotFoundException("That subscriptions definition does not exist.")
        self.subscription_definitions[subscription_definition_id].name = name

    def create_subscription_definition_version(
        self, subscription_definition_id, subscriptions
    ):

        GreengrassBackend._validate_subscription_target_or_source(subscriptions)

        if subscription_definition_id not in self.subscription_definitions:
            raise IdNotFoundException("That subscriptions does not exist.")

        sub_def_ver = FakeSubscriptionDefinitionVersion(
            self.region_name, subscription_definition_id, subscriptions
        )

        sub_vers = self.subscription_definition_versions.get(
            subscription_definition_id, {}
        )
        sub_vers[sub_def_ver.version] = sub_def_ver
        self.subscription_definition_versions[subscription_definition_id] = sub_vers

        return sub_def_ver

    def list_subscription_definition_versions(self, subscription_definition_id):
        if subscription_definition_id not in self.subscription_definition_versions:
            raise IdNotFoundException("That subscriptions definition does not exist.")
        return self.subscription_definition_versions[subscription_definition_id]

    def get_subscription_definition_version(
        self, subscription_definition_id, subscription_definition_version_id
    ):

        if subscription_definition_id not in self.subscription_definitions:
            raise IdNotFoundException("That subscriptions definition does not exist.")

        if (
            subscription_definition_version_id
            not in self.subscription_definition_versions[subscription_definition_id]
        ):
            raise VersionNotFoundException(
                f"Version {subscription_definition_version_id} of Subscription List Definition {subscription_definition_id} does not exist."
            )

        return self.subscription_definition_versions[subscription_definition_id][
            subscription_definition_version_id
        ]

    def create_group(self, name, initial_version):
        group = FakeGroup(self.region_name, name)
        self.groups[group.group_id] = group

        definitions = initial_version or {}
        core_definition_version_arn = definitions.get("CoreDefinitionVersionArn")
        device_definition_version_arn = definitions.get("DeviceDefinitionVersionArn")
        function_definition_version_arn = definitions.get(
            "FunctionDefinitionVersionArn"
        )
        resource_definition_version_arn = definitions.get(
            "ResourceDefinitionVersionArn"
        )
        subscription_definition_version_arn = definitions.get(
            "SubscriptionDefinitionVersionArn"
        )

        self.create_group_version(
            group.group_id,
            core_definition_version_arn=core_definition_version_arn,
            device_definition_version_arn=device_definition_version_arn,
            function_definition_version_arn=function_definition_version_arn,
            resource_definition_version_arn=resource_definition_version_arn,
            subscription_definition_version_arn=subscription_definition_version_arn,
        )

        return group

    def list_groups(self):
        return self.groups.values()

    def get_group(self, group_id):
        if group_id not in self.groups:
            raise IdNotFoundException("That Group Definition does not exist.")
        return self.groups.get(group_id)

    def delete_group(self, group_id):
        if group_id not in self.groups:
            # I don't know why, the error message is different between get_group and delete_group
            raise IdNotFoundException("That group definition does not exist.")
        del self.groups[group_id]
        del self.group_versions[group_id]

    def update_group(self, group_id, name):

        if name == "":
            raise InvalidContainerDefinitionException(
                "Input does not contain any attributes to be updated"
            )
        if group_id not in self.groups:
            raise IdNotFoundException("That group definition does not exist.")
        self.groups[group_id].name = name

    def create_group_version(
        self,
        group_id,
        core_definition_version_arn,
        device_definition_version_arn,
        function_definition_version_arn,
        resource_definition_version_arn,
        subscription_definition_version_arn,
    ):

        if group_id not in self.groups:
            raise IdNotFoundException("That group does not exist.")

        self._validate_group_version_definitions(
            core_definition_version_arn=core_definition_version_arn,
            device_definition_version_arn=device_definition_version_arn,
            function_definition_version_arn=function_definition_version_arn,
            resource_definition_version_arn=resource_definition_version_arn,
            subscription_definition_version_arn=subscription_definition_version_arn,
        )

        group_ver = FakeGroupVersion(
            self.region_name,
            group_id=group_id,
            core_definition_version_arn=core_definition_version_arn,
            device_definition_version_arn=device_definition_version_arn,
            function_definition_version_arn=function_definition_version_arn,
            resource_definition_version_arn=resource_definition_version_arn,
            subscription_definition_version_arn=subscription_definition_version_arn,
        )
        group_vers = self.group_versions.get(group_ver.group_id, {})
        group_vers[group_ver.version] = group_ver
        self.group_versions[group_ver.group_id] = group_vers
        self.groups[group_id].latest_version_arn = group_ver.arn
        self.groups[group_id].latest_version = group_ver.version
        return group_ver

    def _validate_group_version_definitions(
        self,
        core_definition_version_arn=None,
        device_definition_version_arn=None,
        function_definition_version_arn=None,
        resource_definition_version_arn=None,
        subscription_definition_version_arn=None,
    ):
        def _is_valid_def_ver_arn(definition_version_arn, kind="cores"):

            if definition_version_arn is None:
                return True

            if kind == "cores":
                versions = self.core_definition_versions
            elif kind == "devices":
                versions = self.device_definition_versions
            elif kind == "functions":
                versions = self.function_definition_versions
            elif kind == "resources":
                versions = self.resource_definition_versions
            elif kind == "subscriptions":
                versions = self.subscription_definition_versions
            else:
                raise Exception("invalid args")

            arn_regex = (
                r"^arn:aws:greengrass:[a-zA-Z0-9-]+:[0-9]{12}:greengrass/definition/"
                + kind
                + r"/[a-z0-9-]{36}/versions/[a-z0-9-]{36}$"
            )

            if not re.match(arn_regex, definition_version_arn):
                return False

            definition_id = definition_version_arn.split("/")[-3]

            if definition_id not in versions:
                return False

            definition_version_id = definition_version_arn.split("/")[-1]
            if definition_version_id not in versions[definition_id]:
                return False

            if (
                versions[definition_id][definition_version_id].arn
                != definition_version_arn
            ):
                return False

            return True

        errors = []

        if not _is_valid_def_ver_arn(core_definition_version_arn, kind="cores"):
            errors.append("Cores definition reference does not exist")

        if not _is_valid_def_ver_arn(function_definition_version_arn, kind="functions"):
            errors.append("Lambda definition reference does not exist")

        if not _is_valid_def_ver_arn(resource_definition_version_arn, kind="resources"):
            errors.append("Resource definition reference does not exist")

        if not _is_valid_def_ver_arn(device_definition_version_arn, kind="devices"):
            errors.append("Devices definition reference does not exist")

        if not _is_valid_def_ver_arn(
            subscription_definition_version_arn, kind="subscriptions"
        ):
            errors.append("Subscription definition reference does not exist")

        if errors:
            error_details = ", ".join(errors)
            raise GreengrassClientError(
                "400",
                f"The group is invalid or corrupted. (ErrorDetails: [{error_details}])",
            )

    def list_group_versions(self, group_id):
        if group_id not in self.group_versions:
            raise IdNotFoundException("That group definition does not exist.")
        return self.group_versions[group_id].values()

    def get_group_version(self, group_id, group_version_id):

        if group_id not in self.group_versions:
            raise IdNotFoundException("That group definition does not exist.")

        if group_version_id not in self.group_versions[group_id]:
            raise VersionNotFoundException(
                f"Version {group_version_id} of Group Definition {group_id} does not exist."
            )

        return self.group_versions[group_id][group_version_id]


greengrass_backends = BackendDict(GreengrassBackend, "greengrass")
