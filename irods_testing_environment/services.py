# grown-up modules
import logging
import os

# local modules
from . import context
from . import irods_setup
from .install import install

#def force_recreate_services(compose_project, zone_count, consumer_count=0):
#    import compose.service
#    compose_project.build()
#    compose_project.up(scale_override={
#        context.irods_catalog_database_service(): zone_count,
#        context.irods_catalog_provider_service(): zone_count,
#        context.irods_catalog_consumer_service(): consumer_count * zone_count
#        },
#        strategy=compose.service.ConvergenceStrategy.always
#    )

def irods_server_is_ready(container,
                          command='ils',
                          repeat_attempts=0,
                          time_between_retries_in_seconds=0):
    """Run `command` on `container` as user irods to see if iRODS is ready.

    Arguments:
    container -- Docker container to check
    command -- command to run as user irods in the container
    repeat_attempts -- number of times the command must succeed in order to be considered ready
    time_between_retries_in_seconds -- time between retries in seconds
    """
    if repeat_attempts < 0:
        raise ValueError('repeat_attempts must be positive or 0')

    import time
    from . import execute

    attempt = 0
    while execute.execute_command(container, command, user='irods') == 0:
        if attempt == repeat_attempts:
            return True
        attempt = attempt + 1
        time.sleep(time_between_retries_in_seconds)

    return False

def wait_for_topology_setup(ctx,
                            zone_count,
                            consumer_count=0,
                            retries=0,
                            time_between_retries_in_seconds=0):
    """Waits for response on port 1247 for each iRODS server in each zone in the project.

    Arguments:
    ctx -- context object which holds the Docker client and Compose project information
    zone_count -- number of Zones stood up in this project
    consumer_count -- number of iRODS Catalog Service Consumers to check in each Zone
    retries -- number of times to retry for a response on port 1247 for each service instance
    time_between_retries_in_seconds -- time between retries in seconds
    """
    import time
    # TODO: parallel!
    for s in range(zone_count):
        # reset retry_count between instances because it reflects the number of retries per
        # service, not overall
        retry_count = 0

        csp_container = ctx.docker_client.containers.get(
            context.irods_catalog_provider_container(
                ctx.compose_project.name, s + 1
            )
        )

        logging.debug(f'checking to see if csp is ready on [{csp_container.name}]')

        while not irods_server_is_ready(csp_container, repeat_attempts=4, time_between_retries_in_seconds=1):
            if retry_count >= retries:
                break

            logging.debug(f'csp is not ready on [{csp_container.name}], sleeping...')
            time.sleep(time_between_retries_in_seconds)
            retry_count = retry_count + 1

        for c in range(consumer_count):
            # reset retry_count between instances because it reflects the number of retries
            # per service, not overall
            retry_count = 0

            csc_container = ctx.docker_client.containers.get(
                context.irods_catalog_consumer_container(
                    ctx.compose_project.name, c + 1
                )
            )

            logging.debug(f'checking to see if csc is ready on [{csc_container.name}]')

            while not irods_server_is_ready(csc_container):
                if retry_count >= retries:
                    break

                logging.debug(f'csc is not ready on [{csc_container.name}], sleeping...')
                time.sleep(time_between_retries_in_seconds)
                retry_count = retry_count + 1


def create_topologies(ctx,
                      zone_count,
                      externals_directory=None,
                      package_directory=None,
                      package_version=None,
                      odbc_driver=None,
                      zone_name='tempZone',
                      consumer_count=0):
    """Create several generic topologies of iRODS servers with the given inputs.

    This is a convenience function for standing up multiple, identical iRODS Zones with the
    default setup parameters.

    Arguments:
    ctx -- context object which holds the Docker client and Compose project information
    zone_count -- number of identical zones to scale up to
    externals_directory -- path to directory in which iRODS externals packages are housed
    package_directory -- path to directory in which iRODS packages are housed
    package_version -- version tag for official iRODS packages to download and install
    odbc_driver -- path to archive file containing an ODBC driver to use with iRODS CSP
    consumer_count -- number of iRODS Catalog Service Consumers to create and set up for each
                      Zone
    """
    ctx.compose_project.build()
    ctx.compose_project.up(scale_override={
        context.irods_catalog_database_service(): zone_count,
        context.irods_catalog_provider_service(): zone_count,
        context.irods_catalog_consumer_service(): consumer_count * zone_count
    })

    install.make_installer(ctx.platform_name()).install_irods_packages(
            ctx,
            externals_directory=externals_directory,
            package_directory=package_directory,
            package_version=package_version)

    zone_names = [zone_name for i in range(zone_count)]

    # This should generate a list of identical zone infos
    zone_info_list = irods_setup.get_info_for_zones(ctx, zone_names, consumer_count)

    irods_setup.setup_irods_zones(ctx, zone_info_list, odbc_driver=odbc_driver)


def create_topology(ctx,
                    externals_directory=None,
                    package_directory=None,
                    package_version=None,
                    odbc_driver=None,
                    consumer_count=0):
    """Create a generic topology of iRODS servers with the given inputs.

    This is a convenience function for standing up an iRODS Zone with the default
    setup parameters.

    Arguments:
    ctx -- context object which holds the Docker client and Compose project information
    externals_directory -- path to directory in which iRODS externals packages are housed
    package_directory -- path to directory in which iRODS packages are housed
    package_version -- version tag for official iRODS packages to download and install
    odbc_driver -- path to archive file containing an ODBC driver to use with iRODS CSP
    consumer_count -- number of iRODS Catalog Service Consumers to create and set up for the
                      Zone
    """
    return create_topologies(ctx,
                             zone_count=1,
                             externals_directory=externals_directory,
                             package_directory=package_directory,
                             package_version=package_version,
                             odbc_driver=odbc_driver,
                             consumer_count=consumer_count)


def clone_repository_to_container(container,
                                  repo_name,
                                  url_base='https://github.com/irods',
                                  branch=None,
                                  destination_directory=None):
    """Clone the specified git repository to the specified container.

    Arguments:
    container -- target container on which the test script will run
    repo_name -- name of the git repo
    url_base -- base of the git URL from which the repository will be cloned
    branch -- branch name to checkout in the cloned repository
    destination_directory -- path on local filesystem to which git repository will be cloned
    """
    import tempfile
    from git import Repo

    from . import archive

    url = os.path.join(url_base, '.'.join([repo_name, 'git']))

    repo_path = os.path.abspath(os.path.join(
                    destination_directory or tempfile.mkdtemp(),
                    repo_name))

    Repo().clone_from(url=url, to_path=repo_path, branch=branch)

    archive.copy_archive_to_container(container,
                                      archive.create_archive(
                                            [os.path.abspath(repo_path)], repo_name))

    return repo_path
