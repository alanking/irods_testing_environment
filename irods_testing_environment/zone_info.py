# grown-up modules
import compose
import docker
import logging
import os

# local modules
from . import context
from . import database_setup
from . import odbc_setup
from . import execute

class zone_info(object):
    """Class to hold information about an iRODS Zone and the containers running the servers."""
    def __init__(self,
                 zone_name='tempZone',
                 zone_key='TEMPORARY_ZONE_KEY',
                 negotiation_key='32_byte_server_negotiation_key__',
                 zone_port=1247,
                 database_service_instance=1,
                 provider_service_instance=1,
                 consumer_service_instances=None):
        """Construct a zone_info object.

        Arguments:
        zone_name -- name of the iRODS Zone
        zone_key -- zone_key for the iRODS Zone
        negotiation_key -- 32-byte negotiation_key for the iRODS Zone
        zone_port -- zone_port for the iRODS Zone
        database_service_instance -- service instance for the database container for this Zone
        provider_service_instance -- service instance for the iRODS CSP container for this Zone
        consumer_service_instances -- service instances for the iRODS Catalog Service Consumer
                                      containers for this Zone (if None is provided, all running
                                      iRODS Catalog Service Consumer service instances are
                                      determined to be part of this Zone, per the irods_setup
                                      interfaces. list() indicates that no iRODS Catalog
                                      Service Consumers are in this zone.
        """
        self.zone_name = zone_name
        self.zone_key = zone_key
        self.negotiation_key = negotiation_key
        self.zone_port = zone_port
        self.database_service_instance = database_service_instance
        self.provider_service_instance = provider_service_instance
        self.consumer_service_instances = consumer_service_instances

    def provider_hostname(self, ctx):
        """Return hostname for the container running the iRODS CSP."""
        return context.container_hostname(
            ctx.docker_client.containers.get(
                context.irods_catalog_provider_container(
                    ctx.compose_project.name,
                    service_instance=self.provider_service_instance)
            )
        )


def make_negotiation_key(local_zone_name, remote_zone_name=''):
    negotation_key_size_in_bytes = 32
    filler = '_' * negotation_key_size_in_bytes
    # TODO: need predictable way to generate unique keys
    #prefix = '_'.join([local_zone_name, remote_zone_name])
    #return prefix + filler[:negotation_key_size_in_bytes - len(prefix)]
    return filler


def make_zone_key(zone_name):
    zone_key_prefix = 'ZONE_KEY_FOR'
    return '_'.join([zone_key_prefix, zone_name])


def get_info_for_zones(ctx, zone_names, consumer_service_instances_per_zone=0):
    zone_info_list = list()

    for i, zn in enumerate(zone_names):
        # Divide up the consumers evenly amongst the Zones
        consumer_service_instances = [
            context.service_instance(c.name)
            for c in ctx.compose_project.containers()
            if context.is_irods_catalog_consumer_container(c)
            and context.service_instance(c.name) > i * consumer_service_instances_per_zone
            and context.service_instance(c.name) <= (i + 1) * consumer_service_instances_per_zone
        ]

        logging.info('consumer service instances for [{}] [{}] (expected: [{}])'
                     .format(zn, consumer_service_instances,
                             list(range((i*consumer_service_instances_per_zone)+1,
                                        ((i+1)*consumer_service_instances_per_zone)+1))
                     ))

        zone_info_list.append(
            zone_info(database_service_instance=i + 1,
                      provider_service_instance=i + 1,
                      consumer_service_instances=consumer_service_instances,
                      zone_name=zn,
                      zone_key=make_zone_key(zn),
                      negotiation_key=make_negotiation_key(zn))
        )

    return zone_info_list
