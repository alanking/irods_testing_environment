# local modules
from . import 4_2_x
from . import 4_3_x
from .. import irods_config

def make_setup_builder(container):
    """Return the appropriate setup_input_builder based on the installed iRODS version.

    Arguments:
    container -- the container on which iRODS is installed
    """
    major, minor, patch = irods_config.get_irods_version(container)

    if major != 4:
        raise NotImplementedError('only 4.x is supported right now')

    if minor < 2 or minor > 3:
        raise NotImplementedError('only 4.2.x and 4.3.x are supported right now')

    if minor == 2:
        return 4_2_x.setup_input_builder.setup_input_builder

    else:
        return 4_3_x.setup_input_builder.setup_input_builder
