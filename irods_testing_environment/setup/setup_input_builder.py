class setup_input_builder(object):
    """Builder for iRODS setup script inputs.

    The builder is designed to look like a programmable interface to the iRODS setup script.
    To that end, each section of the setup script is its own method which sets the values
    to generate the input string.
    """
    def __init__(self):
        """Construct a setup input builder.

        Sets default values for the setup script inputs.
        """
        pass

    def setup(self, **kwargs):
        """Set values for the service account section of the setup script.

        Returns this instance of the class.
        """
        raise NotImplementedError('setup_input_builder should not be instantiated directly')


    def build_input_for_catalog_consumer(self):
        """Generate string to use as input for the setup script.

        The script changes depending on the role, so the options used here are specific to
        setting up an iRODS catalog service consumer.
        """
        raise NotImplementedError('setup_input_builder should not be instantiated directly')

    def build_input_for_catalog_provider(self):
        """Generate string to use as input for the setup script.

        The script changes depending on the role, so the options used here are specific to
        setting up an iRODS catalog service provider.
        """
        raise NotImplementedError('setup_input_builder should not be instantiated directly')

    def build(self):
        """Build the string for the setup script input.

        Depending on the way the inputs were provided, either an iRODS catalog service provider
        or a catalog service consumer will be set up and the resulting input string will be
        returned.
        """
        build_for_role = {
            'provider': self.build_input_for_catalog_provider,
            'consumer': self.build_input_for_catalog_consumer
        }

        try:
            return build_for_role[self.catalog_service_role]()

        except KeyError:
            raise NotImplementedError('unsupported catalog service role [{}]'.format(self.catalog_service_role))
