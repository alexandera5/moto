import time
import re
from collections import OrderedDict
from datetime import datetime

from moto.core import BaseBackend, BaseModel
from moto.core.models import get_account_id
from moto.core.utils import BackendDict
from moto.glue.exceptions import CrawlerRunningException, CrawlerNotRunningException
from .exceptions import (
    JsonRESTError,
    CrawlerAlreadyExistsException,
    CrawlerNotFoundException,
    DatabaseAlreadyExistsException,
    DatabaseNotFoundException,
    TableAlreadyExistsException,
    TableNotFoundException,
    PartitionAlreadyExistsException,
    PartitionNotFoundException,
    VersionNotFoundException,
    JobNotFoundException,
    ConcurrentRunsExceededException,
    GSRAlreadyExistsException,
    ResourceNumberLimitExceededException,
    ResourceNameTooLongException,
    ParamValueContainsInvalidCharactersException,
    InvalidNumberOfTagsException,
)
from .utils import PartitionFilter
from ..utilities.paginator import paginate
from ..utilities.tagging_service import TaggingService


class GlueBackend(BaseBackend):
    PAGINATION_MODEL = {
        "list_crawlers": {
            "input_token": "next_token",
            "limit_key": "max_results",
            "limit_default": 100,
            "unique_attribute": "name",
        },
        "list_jobs": {
            "input_token": "next_token",
            "limit_key": "max_results",
            "limit_default": 100,
            "unique_attribute": "name",
        },
    }

    def __init__(self, region_name, account_id):
        super().__init__(region_name, account_id)
        self.databases = OrderedDict()
        self.crawlers = OrderedDict()
        self.jobs = OrderedDict()
        self.job_runs = OrderedDict()
        self.tagger = TaggingService()
        self.registries = OrderedDict()

    @staticmethod
    def default_vpc_endpoint_service(service_region, zones):
        """Default VPC endpoint service."""
        return BaseBackend.default_vpc_endpoint_service_factory(
            service_region, zones, "glue"
        )

    def create_database(self, database_name, database_input):
        if database_name in self.databases:
            raise DatabaseAlreadyExistsException()

        database = FakeDatabase(database_name, database_input)
        self.databases[database_name] = database
        return database

    def get_database(self, database_name):
        try:
            return self.databases[database_name]
        except KeyError:
            raise DatabaseNotFoundException(database_name)

    def get_databases(self):
        return [self.databases[key] for key in self.databases] if self.databases else []

    def delete_database(self, database_name):
        if database_name not in self.databases:
            raise DatabaseNotFoundException(database_name)
        del self.databases[database_name]

    def create_table(self, database_name, table_name, table_input):
        database = self.get_database(database_name)

        if table_name in database.tables:
            raise TableAlreadyExistsException()

        table = FakeTable(database_name, table_name, table_input)
        database.tables[table_name] = table
        return table

    def get_table(self, database_name, table_name):
        database = self.get_database(database_name)
        try:
            return database.tables[table_name]
        except KeyError:
            raise TableNotFoundException(table_name)

    def get_tables(self, database_name):
        database = self.get_database(database_name)
        return [table for table_name, table in database.tables.items()]

    def delete_table(self, database_name, table_name):
        database = self.get_database(database_name)
        try:
            del database.tables[table_name]
        except KeyError:
            raise TableNotFoundException(table_name)
        return {}

    def create_crawler(
        self,
        name,
        role,
        database_name,
        description,
        targets,
        schedule,
        classifiers,
        table_prefix,
        schema_change_policy,
        recrawl_policy,
        lineage_configuration,
        configuration,
        crawler_security_configuration,
        tags,
    ):
        if name in self.crawlers:
            raise CrawlerAlreadyExistsException()

        crawler = FakeCrawler(
            name=name,
            role=role,
            database_name=database_name,
            description=description,
            targets=targets,
            schedule=schedule,
            classifiers=classifiers,
            table_prefix=table_prefix,
            schema_change_policy=schema_change_policy,
            recrawl_policy=recrawl_policy,
            lineage_configuration=lineage_configuration,
            configuration=configuration,
            crawler_security_configuration=crawler_security_configuration,
            tags=tags,
            backend=self,
        )
        self.crawlers[name] = crawler

    def get_crawler(self, name):
        try:
            return self.crawlers[name]
        except KeyError:
            raise CrawlerNotFoundException(name)

    def get_crawlers(self):
        return [self.crawlers[key] for key in self.crawlers] if self.crawlers else []

    @paginate(pagination_model=PAGINATION_MODEL)
    def list_crawlers(self):
        return [crawler for _, crawler in self.crawlers.items()]

    def start_crawler(self, name):
        crawler = self.get_crawler(name)
        crawler.start_crawler()

    def stop_crawler(self, name):
        crawler = self.get_crawler(name)
        crawler.stop_crawler()

    def delete_crawler(self, name):
        try:
            del self.crawlers[name]
        except KeyError:
            raise CrawlerNotFoundException(name)

    def create_job(
        self,
        name,
        role,
        command,
        description,
        log_uri,
        execution_property,
        default_arguments,
        non_overridable_arguments,
        connections,
        max_retries,
        allocated_capacity,
        timeout,
        max_capacity,
        security_configuration,
        tags,
        notification_property,
        glue_version,
        number_of_workers,
        worker_type,
    ):
        self.jobs[name] = FakeJob(
            name,
            role,
            command,
            description,
            log_uri,
            execution_property,
            default_arguments,
            non_overridable_arguments,
            connections,
            max_retries,
            allocated_capacity,
            timeout,
            max_capacity,
            security_configuration,
            tags,
            notification_property,
            glue_version,
            number_of_workers,
            worker_type,
            backend=self,
        )
        return name

    def get_job(self, name):
        try:
            return self.jobs[name]
        except KeyError:
            raise JobNotFoundException(name)

    def start_job_run(self, name):
        job = self.get_job(name)
        return job.start_job_run()

    def get_job_run(self, name, run_id):
        job = self.get_job(name)
        return job.get_job_run(run_id)

    @paginate(pagination_model=PAGINATION_MODEL)
    def list_jobs(self):
        return [job for _, job in self.jobs.items()]

    def get_tags(self, resource_id):
        return self.tagger.get_tag_dict_for_resource(resource_id)

    def tag_resource(self, resource_arn, tags):
        tags = TaggingService.convert_dict_to_tags_input(tags or {})
        self.tagger.tag_resource(resource_arn, tags)

    def untag_resource(self, resource_arn, tag_keys):
        self.tagger.untag_resource_using_names(resource_arn, tag_keys)

    # TODO: @Himani. Will Refactor validation logic as I find the common validation required for other APIs
    def create_registry(self, registry_name, description, tags):
        operation_name = "CreateRegistry"

        registry_name_pattern = re.compile(r"^[a-zA-Z0-9-_$#.]+$")
        registry_description_pattern = re.compile(
            r"[\\u0020-\\uD7FF\\uE000-\\uFFFD\\uD800\\uDC00-\\uDBFF\\uDFFF\\r\\n\\t]*"
        )

        max_registry_name_length = 255
        max_registries_allowed = 10
        max_description_length = 2048
        max_tags_allowed = 50

        if len(self.registries) >= max_registries_allowed:
            raise ResourceNumberLimitExceededException(
                operation_name, resource="registries"
            )

        if (
            registry_name == ""
            or len(registry_name.encode("utf-8")) > max_registry_name_length
        ):
            param_name = "registryName"
            raise ResourceNameTooLongException(operation_name, param_name)

        if re.match(registry_name_pattern, registry_name) is None:
            param_name = "registryName"
            raise ParamValueContainsInvalidCharactersException(
                operation_name, param_name
            )

        if registry_name in self.registries:
            raise GSRAlreadyExistsException(
                operation_name,
                resource="Registry",
                param_name="RegistryName",
                param_value=registry_name,
            )

        if description and len(description.encode("utf-8")) > max_description_length:
            param_name = "description"
            raise ResourceNameTooLongException(operation_name, param_name)

        if description and re.match(registry_description_pattern, description) is None:
            param_name = "description"
            raise ParamValueContainsInvalidCharactersException(
                operation_name, param_name
            )

        if tags and len(tags) > max_tags_allowed:
            raise InvalidNumberOfTagsException(operation_name)

        registry = FakeRegistry(registry_name, description, tags)
        self.registries[registry_name] = registry
        return registry


class FakeDatabase(BaseModel):
    def __init__(self, database_name, database_input):
        self.name = database_name
        self.input = database_input
        self.created_time = datetime.utcnow()
        self.tables = OrderedDict()

    def as_dict(self):
        return {
            "Name": self.name,
            "Description": self.input.get("Description"),
            "LocationUri": self.input.get("LocationUri"),
            "Parameters": self.input.get("Parameters"),
            "CreateTime": self.created_time.isoformat(),
            "CreateTableDefaultPermissions": self.input.get(
                "CreateTableDefaultPermissions"
            ),
            "TargetDatabase": self.input.get("TargetDatabase"),
            "CatalogId": self.input.get("CatalogId"),
        }


class FakeTable(BaseModel):
    def __init__(self, database_name, table_name, table_input):
        self.database_name = database_name
        self.name = table_name
        self.partitions = OrderedDict()
        self.created_time = datetime.utcnow()
        self.versions = []
        self.update(table_input)

    def update(self, table_input):
        self.versions.append(table_input)

    def get_version(self, ver):
        try:
            if not isinstance(ver, int):
                # "1" goes to [0]
                ver = int(ver) - 1
        except ValueError as e:
            raise JsonRESTError("InvalidInputException", str(e))

        try:
            return self.versions[ver]
        except IndexError:
            raise VersionNotFoundException()

    def as_dict(self, version=-1):
        obj = {
            "DatabaseName": self.database_name,
            "Name": self.name,
            "CreateTime": self.created_time.isoformat(),
        }
        obj.update(self.get_version(version))
        return obj

    def create_partition(self, partiton_input):
        partition = FakePartition(self.database_name, self.name, partiton_input)
        key = str(partition.values)
        if key in self.partitions:
            raise PartitionAlreadyExistsException()
        self.partitions[str(partition.values)] = partition

    def get_partitions(self, expression):
        """See https://docs.aws.amazon.com/glue/latest/webapi/API_GetPartitions.html
        for supported expressions.

        Expression caveats:

        - Column names must consist of UPPERCASE, lowercase, dots and underscores only.
        - Nanosecond expressions on timestamp columns are rounded to microseconds.
        - Literal dates and timestamps must be valid, i.e. no support for February 31st.
        - LIKE expressions are converted to Python regexes, escaping special characters.
          Only % and _ wildcards are supported, and SQL escaping using [] does not work.
        """
        return list(filter(PartitionFilter(expression, self), self.partitions.values()))

    def get_partition(self, values):
        try:
            return self.partitions[str(values)]
        except KeyError:
            raise PartitionNotFoundException()

    def update_partition(self, old_values, partiton_input):
        partition = FakePartition(self.database_name, self.name, partiton_input)
        key = str(partition.values)
        if old_values == partiton_input["Values"]:
            # Altering a partition in place. Don't remove it so the order of
            # returned partitions doesn't change
            if key not in self.partitions:
                raise PartitionNotFoundException()
        else:
            removed = self.partitions.pop(str(old_values), None)
            if removed is None:
                raise PartitionNotFoundException()
            if key in self.partitions:
                # Trying to update to overwrite a partition that exists
                raise PartitionAlreadyExistsException()
        self.partitions[key] = partition

    def delete_partition(self, values):
        try:
            del self.partitions[str(values)]
        except KeyError:
            raise PartitionNotFoundException()


class FakePartition(BaseModel):
    def __init__(self, database_name, table_name, partiton_input):
        self.creation_time = time.time()
        self.database_name = database_name
        self.table_name = table_name
        self.partition_input = partiton_input
        self.values = self.partition_input.get("Values", [])

    def as_dict(self):
        obj = {
            "DatabaseName": self.database_name,
            "TableName": self.table_name,
            "CreationTime": self.creation_time,
        }
        obj.update(self.partition_input)
        return obj


class FakeCrawler(BaseModel):
    def __init__(
        self,
        name,
        role,
        database_name,
        description,
        targets,
        schedule,
        classifiers,
        table_prefix,
        schema_change_policy,
        recrawl_policy,
        lineage_configuration,
        configuration,
        crawler_security_configuration,
        tags,
        backend,
    ):
        self.name = name
        self.role = role
        self.database_name = database_name
        self.description = description
        self.targets = targets
        self.schedule = schedule
        self.classifiers = classifiers
        self.table_prefix = table_prefix
        self.schema_change_policy = schema_change_policy
        self.recrawl_policy = recrawl_policy
        self.lineage_configuration = lineage_configuration
        self.configuration = configuration
        self.crawler_security_configuration = crawler_security_configuration
        self.state = "READY"
        self.creation_time = datetime.utcnow()
        self.last_updated = self.creation_time
        self.version = 1
        self.crawl_elapsed_time = 0
        self.last_crawl_info = None
        self.arn = f"arn:aws:glue:us-east-1:{get_account_id()}:crawler/{self.name}"
        self.backend = backend
        self.backend.tag_resource(self.arn, tags)

    def get_name(self):
        return self.name

    def as_dict(self):
        last_crawl = self.last_crawl_info.as_dict() if self.last_crawl_info else None
        data = {
            "Name": self.name,
            "Role": self.role,
            "Targets": self.targets,
            "DatabaseName": self.database_name,
            "Description": self.description,
            "Classifiers": self.classifiers,
            "RecrawlPolicy": self.recrawl_policy,
            "SchemaChangePolicy": self.schema_change_policy,
            "LineageConfiguration": self.lineage_configuration,
            "State": self.state,
            "TablePrefix": self.table_prefix,
            "CrawlElapsedTime": self.crawl_elapsed_time,
            "CreationTime": self.creation_time.isoformat(),
            "LastUpdated": self.last_updated.isoformat(),
            "LastCrawl": last_crawl,
            "Version": self.version,
            "Configuration": self.configuration,
            "CrawlerSecurityConfiguration": self.crawler_security_configuration,
        }

        if self.schedule:
            data["Schedule"] = {
                "ScheduleExpression": self.schedule,
                "State": "SCHEDULED",
            }

        if self.last_crawl_info:
            data["LastCrawl"] = self.last_crawl_info.as_dict()

        return data

    def start_crawler(self):
        if self.state == "RUNNING":
            raise CrawlerRunningException(
                f"Crawler with name {self.name} has already started"
            )
        self.state = "RUNNING"

    def stop_crawler(self):
        if self.state != "RUNNING":
            raise CrawlerNotRunningException(
                f"Crawler with name {self.name} isn't running"
            )
        self.state = "STOPPING"


class LastCrawlInfo(BaseModel):
    def __init__(
        self, error_message, log_group, log_stream, message_prefix, start_time, status
    ):
        self.error_message = error_message
        self.log_group = log_group
        self.log_stream = log_stream
        self.message_prefix = message_prefix
        self.start_time = start_time
        self.status = status

    def as_dict(self):
        return {
            "ErrorMessage": self.error_message,
            "LogGroup": self.log_group,
            "LogStream": self.log_stream,
            "MessagePrefix": self.message_prefix,
            "StartTime": self.start_time,
            "Status": self.status,
        }


class FakeJob:
    def __init__(
        self,
        name,
        role,
        command,
        description=None,
        log_uri=None,
        execution_property=None,
        default_arguments=None,
        non_overridable_arguments=None,
        connections=None,
        max_retries=None,
        allocated_capacity=None,
        timeout=None,
        max_capacity=None,
        security_configuration=None,
        tags=None,
        notification_property=None,
        glue_version=None,
        number_of_workers=None,
        worker_type=None,
        backend=None,
    ):
        self.name = name
        self.description = description
        self.log_uri = log_uri
        self.role = role
        self.execution_property = execution_property
        self.command = command
        self.default_arguments = default_arguments
        self.non_overridable_arguments = non_overridable_arguments
        self.connections = connections
        self.max_retries = max_retries
        self.allocated_capacity = allocated_capacity
        self.timeout = timeout
        self.state = "READY"
        self.max_capacity = max_capacity
        self.security_configuration = security_configuration
        self.notification_property = notification_property
        self.glue_version = glue_version
        self.number_of_workers = number_of_workers
        self.worker_type = worker_type
        self.created_on = datetime.utcnow()
        self.last_modified_on = datetime.utcnow()
        self.arn = f"arn:aws:glue:us-east-1:{get_account_id()}:job/{self.name}"
        self.backend = backend
        self.backend.tag_resource(self.arn, tags)

    def get_name(self):
        return self.name

    def as_dict(self):
        return {
            "Name": self.name,
            "Description": self.description,
            "LogUri": self.log_uri,
            "Role": self.role,
            "CreatedOn": self.created_on.isoformat(),
            "LastModifiedOn": self.last_modified_on.isoformat(),
            "ExecutionProperty": self.execution_property,
            "Command": self.command,
            "DefaultArguments": self.default_arguments,
            "NonOverridableArguments": self.non_overridable_arguments,
            "Connections": self.connections,
            "MaxRetries": self.max_retries,
            "AllocatedCapacity": self.allocated_capacity,
            "Timeout": self.timeout,
            "MaxCapacity": self.max_capacity,
            "WorkerType": self.worker_type,
            "NumberOfWorkers": self.number_of_workers,
            "SecurityConfiguration": self.security_configuration,
            "NotificationProperty": self.notification_property,
            "GlueVersion": self.glue_version,
        }

    def start_job_run(self):
        if self.state == "RUNNING":
            raise ConcurrentRunsExceededException(
                f"Job with name {self.name} already running"
            )
        fake_job_run = FakeJobRun(job_name=self.name)
        self.state = "RUNNING"
        return fake_job_run.job_run_id

    def get_job_run(self, run_id):
        fake_job_run = FakeJobRun(job_name=self.name, job_run_id=run_id)
        return fake_job_run


class FakeJobRun:
    def __init__(
        self,
        job_name: int,
        job_run_id: str = "01",
        arguments: dict = None,
        allocated_capacity: int = None,
        timeout: int = None,
        worker_type: str = "Standard",
    ):
        self.job_name = job_name
        self.job_run_id = job_run_id
        self.arguments = arguments
        self.allocated_capacity = allocated_capacity
        self.timeout = timeout
        self.worker_type = worker_type
        self.started_on = datetime.utcnow()
        self.modified_on = datetime.utcnow()
        self.completed_on = datetime.utcnow()

    def get_name(self):
        return self.job_name

    def as_dict(self):
        return {
            "Id": self.job_run_id,
            "Attempt": 1,
            "PreviousRunId": "01",
            "TriggerName": "test_trigger",
            "JobName": self.job_name,
            "StartedOn": self.started_on.isoformat(),
            "LastModifiedOn": self.modified_on.isoformat(),
            "CompletedOn": self.completed_on.isoformat(),
            "JobRunState": "SUCCEEDED",
            "Arguments": self.arguments or {"runSpark": "spark -f test_file.py"},
            "ErrorMessage": "",
            "PredecessorRuns": [
                {"JobName": "string", "RunId": "string"},
            ],
            "AllocatedCapacity": self.allocated_capacity or 123,
            "ExecutionTime": 123,
            "Timeout": self.timeout or 123,
            "MaxCapacity": 123.0,
            "WorkerType": self.worker_type,
            "NumberOfWorkers": 123,
            "SecurityConfiguration": "string",
            "LogGroupName": "test/log",
            "NotificationProperty": {"NotifyDelayAfter": 123},
            "GlueVersion": "0.9",
        }


class FakeRegistry(BaseModel):
    def __init__(self, registry_name, description=None, tags=None):
        self.name = registry_name
        self.description = description
        self.tags = tags
        self.created_time = datetime.utcnow()
        self.updated_time = datetime.utcnow()
        self.registry_arn = (
            f"arn:aws:glue:us-east-1:{get_account_id()}:registry/{self.name}"
        )

    def as_dict(self):
        return {
            "RegistryArn": self.registry_arn,
            "RegistryName": self.name,
            "Description": self.description,
            "Tags": self.tags,
        }


glue_backends = BackendDict(
    GlueBackend, "glue", use_boto3_regions=False, additional_regions=["global"]
)
glue_backend = glue_backends["global"]
