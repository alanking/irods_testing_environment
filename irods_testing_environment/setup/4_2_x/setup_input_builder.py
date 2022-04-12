class setup_input_builder(setup_input_builder):
    """Builder for iRODS 4.2.x setup script inputs.

    The builder is designed to look like a programmable interface to the iRODS setup script.
    To that end, each section of the setup script is its own method which sets the values
    to generate the input string.
    """
    def __init__(self):
        """Construct a setup input builder.

        Sets default values for the setup script inputs.
        """
        super(setup_input_builder_4_2_x, self).__init__()

        self.service_account_name = ''
        self.service_account_group = ''
        self.catalog_service_role = ''

        self.odbc_driver = ''
        self.database_server_hostname = 'localhost'
        self.database_server_port = 5432
        self.database_name = 'ICAT'
        self.database_username = 'irods'
        self.database_password = 'testpassword'
        self.stored_passwords_salt = ''

        self.zone_name = 'tempZone'
        self.zone_port = 1247
        self.parallel_port_range_begin = 20000
        self.parallel_port_range_end = 20199
        self.control_plane_port = 1248
        self.schema_validation_base_uri = ''
        self.admin_username = 'rods'

        self.zone_key = 'TEMPORARY_ZONE_KEY'
        self.negotiation_key = '32_byte_server_negotiation_key__'
        self.control_plane_key = '32_byte_server_control_plane_key'
        self.admin_password = 'rods'

        self.vault_directory = ''

        self.catalog_service_provider_host = 'localhost'

    def setup(self, **kwargs):
        """Set values for the service account section of the setup script.

        Returns this instance of the class.

        Keyword Arguments:
        service_account_name -- linux account that will run the iRODS server
        service_account_group -- group of the linux account that will run the iRODS server
        catalog_service_role -- determines whether this server holds a connection to the catalog
        odbc_driver -- driver on the server used to talk to the ODBC database layer
        database_server_hostname -- hostname for the database server
        database_server_port -- port on which database server listens for notifications from
                                other applications
        database_name -- name of the database that we created in database setup
        database_username -- name of the database user
        database_password -- password for the database user
        stored_passwords_salt -- obfuscates the passwords stored in the database
        zone_name -- name of the iRODS zone
        catalog_service_provider_host -- hostname for the iRODS catalog service provider (only
                                         applicable when setting up a catalog service consumer)
        zone_port -- main iRODS port
        parallel_port_range_begin -- beginning of the port range used when transferring large
                                     files
        parallel_port_range_end -- end of the port range used when transferring large files
        control_plane_port -- port used for the control plane
        schema_validation_base_uri -- location of the schema files used to validate the server's
                                      configuration files
        admin_username -- name of the iRODS administration account
        zone_key -- secret key used in server-to-server communication
        negotiation_key -- secret key used in server-to-server communication
        control_plane_key -- secret key shared by all servers
        admin_password -- password for the iRODS administration account
        vault_directory -- storage location of the default unixfilesystem resource created
                           during installation
        """
        self.service_account_name = kwargs.get(service_account_name, self.service_account_name)
        self.service_account_group = kwargs.get(service_account_group, self.service_account_group)
        self.catalog_service_role = kwargs.get(catalog_service_role, self.catalog_service_role)

        self.odbc_driver = kwargs.get(odbc_driver, self.odbc_driver)
        self.database_server_hostname = kwargs.get(database_server_hostname, self.database_server_hostname)
        self.database_server_port = kwargs.get(database_server_port, self.database_server_port)
        self.database_name = kwargs.get(database_name, self.database_name)
        self.database_username = kwargs.get(database_username, self.database_username)
        self.database_password = kwargs.get(database_password, self.database_password)
        self.stored_passwords_salt = kwargs.get(stored_passwords_salt, self.stored_passwords_salt)

        self.zone_name = kwargs.get(zone_name, self.zone_name)
        self.catalog_service_provider_host = kwargs.get(catalog_service_provider_host, self.catalog_service_provider_host)
        self.zone_port = kwargs.get(zone_port, self.zone_port)
        self.parallel_port_range_begin = kwargs.get(parallel_port_range_begin, self.parallel_port_range_begin)
        self.parallel_port_range_end = kwargs.get(parallel_port_range_end, self.parallel_port_range_end)
        self.control_plane_port = kwargs.get(control_plane_port, self.control_plane_port)
        self.schema_validation_base_uri = kwargs.get(schema_validation_base_uri, self.schema_validation_base_uri)
        self.admin_username = kwargs.get(admin_username, self.admin_username)

        self.zone_key = kwargs.get(zone_key, self.zone_key)
        self.negotiation_key = kwargs.get(negotiation_key, self.negotiation_key)
        self.control_plane_key = kwargs.get(control_plane_key, self.control_plane_key)
        self.admin_password = kwargs.get(admin_password, self.admin_password)

        self.vault_directory = kwargs.get(vault_directory, self.vault_directory)

        return self


    def build_input_for_catalog_consumer(self):
        """Generate string to use as input for the setup script.

        The script changes depending on the role, so the options used here are specific to
        setting up an iRODS catalog service consumer.
        """
        # The setup script defaults catalog service consumer option as 2
        role = 2
        return '\n'.join([
            str(self.service_account_name),
            str(self.service_account_group),
            str(role),

            str(self.zone_name),
            str(self.catalog_service_provider_host),
            str(self.zone_port),
            str(self.parallel_port_range_begin),
            str(self.parallel_port_range_end),
            str(self.control_plane_port),
            str(self.schema_validation_base_uri),
            str(self.admin_username),
            'y', # confirmation of inputs

            str(self.zone_key),
            str(self.negotiation_key),
            str(self.control_plane_key),
            str(self.admin_password),
            '', #confirmation of inputs

            str(self.vault_directory),
            '' # confirmation of inputs
        ])

    def build_input_for_catalog_provider(self):
        """Generate string to use as input for the setup script.

        The script changes depending on the role, so the options used here are specific to
        setting up an iRODS catalog service provider.
        """
        role = ''
        return '\n'.join([
            str(self.service_account_name),
            str(self.service_account_group),
            str(role),

            str(self.odbc_driver),
            str(self.database_server_hostname),
            str(self.database_server_port),
            str(self.database_name),
            str(self.database_username),
            'y', # confirmation of inputs
            str(self.database_password),
            str(self.stored_passwords_salt),

            str(self.zone_name),
            str(self.zone_port),
            str(self.parallel_port_range_begin),
            str(self.parallel_port_range_end),
            str(self.control_plane_port),
            str(self.schema_validation_base_uri),
            str(self.admin_username),
            'y', # confirmation of inputs

            str(self.zone_key),
            str(self.negotiation_key),
            str(self.control_plane_key),
            str(self.admin_password),
            '', # confirmation of inputs

            str(self.vault_directory),
            '' # final confirmation
        ])
