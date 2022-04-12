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
from . import setup.setup_builder

def setup_irods_server(container, setup_input):
    """Set up iRODS server on the given container with the provided input.

    After setup completes, the server is restarted in order to guarantee that the iRODS server
    is running and available for immediate use after setting it up.

    Arguments:
    container -- docker.client.container on which the iRODS packages are installed
    setup_input -- string which will be provided as input to the iRODS setup script
    """
    from . import container_info
    irodsctl = os.path.join(context.irods_home(), 'irodsctl')
    ec = execute.execute_command(container, '{} stop'.format(irodsctl), user='irods')
    if ec is not 0:
        logging.debug('failed to stop iRODS server before setup [{}]'.format(container.name))

    ec = execute.execute_command(container, 'bash -c \'echo "{}" > /input\''.format(setup_input))
    if ec is not 0:
        raise RuntimeError('failed to create setup script input file [{}]'.format(container.name))

    execute.execute_command(container, 'cat /input')

    path_to_setup_script = os.path.join(context.irods_home(), 'scripts', 'setup_irods.py')
    run_setup_script = 'bash -c \'{} {} < /input\''.format(container_info.python(container),
                                                           path_to_setup_script)
    ec = execute.execute_command(container, run_setup_script)
    if ec is not 0:
        raise RuntimeError('failed to set up iRODS server [{}]'.format(container.name))

    ec = execute.execute_command(container, '{} restart'.format(irodsctl), user='irods')
    if ec is not 0:
        raise RuntimeError('failed to start iRODS server after setup [{}]'.format(container.name))


def setup_irods_catalog_provider(ctx,
                                 database_service_instance=1,
                                 provider_service_instance=1,
                                 odbc_driver=None,
                                 **kwargs):
    """Set up iRODS catalog service provider in a docker-compose project.

    Arguments:
    database_service_instance -- the service instance number of the container running the
                                 database server
    provider_service_instance -- the service instance number of the container being targeted
                                 to run the iRODS catalog service provider
    odbc_driver -- path to the local archive file containing the ODBC driver
    """
    csp_container = ctx.docker_client.containers.get(
        context.irods_catalog_provider_container(
            ctx.compose_project.name, provider_service_instance
        )
    )

    odbc_setup.configure_odbc_driver(ctx.platform(), ctx.database(), csp_container, odbc_driver)

    db_container = ctx.docker_client.containers.get(
        context.irods_catalog_database_container(
            ctx.compose_project.name, provider_service_instance
        )
    )

    setup_input = (setup.setup_builder.make_setup_builder(csp_container)()
        .setup(catalog_service_role='provider',
               database_server_hostname=context.container_hostname(db_container),
               database_server_port=database_setup.database_server_port(ctx.database()),
               **kwargs
        )
        .build()
    )

    logging.debug('input to setup script [{}]'.format(setup_input))

    logging.warning('setting up iRODS catalog provider [{}]'.format(csp_container.name))

    setup_irods_server(csp_container, setup_input)


def setup_irods_catalog_consumer(ctx,
                                 provider_service_instance=1,
                                 consumer_service_instance=1,
                                 **kwargs):
    """Set up iRODS catalog service consumer in a docker-compose project.

    Arguments:
    provider_service_instance -- the service instance number of the container running the iRODS
                                 catalog service provider
    consumer_service_instance -- the service instance number of the containers being targeted
                                 to run the iRODS catalog service consumer
    """
    csp_container = ctx.docker_client.containers.get(
        context.irods_catalog_provider_container(
            ctx.compose_project.name, provider_service_instance
        )
    )

    csc_container = ctx.docker_client.containers.get(
        context.irods_catalog_consumer_container(
            ctx.compose_project.name, consumer_service_instance
        )
    )

    setup_input = (setup.setup_builder.make_setup_builder(csc_container)()
        .setup(catalog_service_role='consumer',
               catalog_service_provider_host=context.container_hostname(csp_container),
               **kwargs)
        .build()
    )

    logging.debug('input to setup script [{}]'.format(setup_input))

    logging.warning('setting up iRODS catalog consumer [{}]'
                    .format(csc_container.name))

    setup_irods_server(csc_container, setup_input)

def setup_irods_catalog_consumers(ctx,
                                  provider_service_instance=1,
                                  consumer_service_instances=None,
                                  **kwargs):
    """Set up all iRODS catalog service consumers in a docker-compose project in parallel.

    Arguments:
    provider_service_instance -- the service instance for the iRODS catalog service provider
                                 running in this docker-compose project
    consumer_service_instances -- the service instance number of the containers being targeted
                                  to run the iRODS catalog service consumer. If None is
                                  provided, all containers with the iRODS catalog service
                                  consumer service name in the Compose project will be
                                  targeted. If an empty list is provided, nothing happens.
    """
    import concurrent.futures

    catalog_consumer_containers = ctx.compose_project.containers(
        service_names=[context.irods_catalog_consumer_service()])

    if consumer_service_instances:
        if len(consumer_service_instances) is 0:
            logging.warning('empty list of iRODS catalog service consumers to set up')
            return

        consumer_service_instances = [
            context.service_instance(c.name)
            for c in catalog_consumer_containers
            if context.service_instance(c.name) in consumer_service_instances
        ]
    else:
        consumer_service_instances = [
            context.service_instance(c.name) for c in catalog_consumer_containers
        ]

    rc = 0

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures_to_catalog_consumer_instances = {
            executor.submit(
                setup_irods_catalog_consumer,
                ctx, provider_service_instance, instance, **kwargs
            ): instance for instance in consumer_service_instances
        }

        logging.debug(futures_to_catalog_consumer_instances)

        for f in concurrent.futures.as_completed(futures_to_catalog_consumer_instances):
            i = futures_to_catalog_consumer_instances[f]
            container_name = context.irods_catalog_consumer_container(ctx.compose_project.name,
                                                                      i + 1)
            try:
                f.result()
                logging.debug('setup completed successfully [{}]'.format(container_name))

            except Exception as e:
                logging.error('exception raised while setting up iRODS [{}]'
                              .format(container_name))
                logging.error(e)
                rc = 1

    if rc is not 0:
        raise RuntimeError('failed to set up one or more catalog service consumers, ec=[{}]'
                           .format(rc))

def setup_irods_zone(ctx,
                     force_recreate=False,
                     provider_service_instance=1,
                     database_service_instance=1,
                     consumer_service_instances=None,
                     odbc_driver=None,
                     **kwargs):
    """Set up an iRODS Zone with the specified settings on the specified service instances.

    Arguments:
    provider_service_instance -- the service instance for the iRODS catalog service provider
                                 running in this docker-compose project
    database_service_instance -- the service instance number of the container running the
                                 database server
    consumer_service_instances -- the service instance number of the containers being targeted
                                  to run the iRODS catalog service consumer. If None is
                                  provided, all containers with the iRODS catalog service
                                  consumer service name in the Compose project will be
                                  targeted. If an empty list is provided, nothing happens.
    odbc_driver -- path to the local archive file containing the ODBC driver
    """
    logging.info('setting up catalog database [{}]'.format(database_service_instance))
    database_setup.setup_catalog(ctx,
                                 force_recreate=force_recreate,
                                 service_instance=database_service_instance)

    logging.info('setting up catalog provider [{}] [{}]'.format(provider_service_instance,
                                                                database_service_instance))
    setup_irods_catalog_provider(ctx,
                                 database_service_instance=database_service_instance,
                                 provider_service_instance=provider_service_instance,
                                 odbc_driver=odbc_driver,
                                 **kwargs)

    logging.info('setting up catalog consumers [{}] [{}]'.format(provider_service_instance,
                                                                 consumer_service_instances))
    setup_irods_catalog_consumers(ctx,
                                  provider_service_instance=provider_service_instance,
                                  consumer_service_instances=consumer_service_instances,
                                  **kwargs)

def setup_irods_zones(ctx,
                      zone_info_list,
                      odbc_driver=None):
    import concurrent.futures

    rc = 0

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures_to_containers = {
            executor.submit(setup_irods_zone,
                            ctx,
                            provider_service_instance=z.provider_service_instance,
                            database_service_instance=z.database_service_instance,
                            consumer_service_instances=z.consumer_service_instances,
                            odbc_driver=odbc_driver,
                            zone_name=z.zone_name,
                            zone_key=z.zone_key,
                            negotiation_key=z.negotiation_key,
            ): z for i, z in enumerate(zone_info_list)
        }

        for f in concurrent.futures.as_completed(futures_to_containers):
            zone = futures_to_containers[f]
            try:
                f.result()
                logging.debug('iRODS Zone setup completed successfully [{}]'.format(zone))

            except Exception as e:
                logging.error('exception raised while setting up iRODS Zone [{}]'.format(zone))
                logging.error(e)
                rc = 1

    if rc is not 0:
        raise RuntimeError('failed to set up one or more iRODS Zones, ec=[{}]'.format(rc))
