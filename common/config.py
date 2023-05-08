import argparse, logging, logging.config, json, os, configparser
from common.session import Session
from common.utils import classproperty

class classproperty(property):
    def __get__(self, cls, owner):
        return classmethod(self.fget).__get__(None, owner)()
    
class Configuration:
    args = None
    _config = None
    _profile_name = None
    _region_name = None
    _setup_already = False
    _session = None
    _public_availability_zone = None
    _private_availability_zone = None

    def reloadconfig(): 
        Configuration._config = configparser.ConfigParser(inline_comment_prefixes="#;")
        Configuration._config.read(filenames='config.ini')

    def setup(description: str):
        if Configuration._setup_already: return

        Configuration.reloadconfig()
        default_profile_name                = Configuration._config.get('AWSCli', 'default.profile.name')
        default_region_name                 = Configuration._config.get('AWSCli','default.region.name')
        default_public_availability_zone    = Configuration._config.get('PublicSubnet','availability.zone')
        default_private_availability_zone   = Configuration._config.get('PrivateSubnet','availability.zone')

        parser = argparse.ArgumentParser(description=description, epilog="NOTE: these arguments default values are specified in 'config.ini'")
        parser.add_argument('--profile', '-p', help=f"AWS Config profile to use. Default is '{default_profile_name}'", default=default_profile_name, required=False, type=str)
        parser.add_argument('--region', '-r', help=f"Region to use. Default is '{default_region_name}'", default=default_region_name, required=False, type=str)
        parser.add_argument('--public-zone', help=f"Availability zone used for the public subnet. Default is '{default_public_availability_zone}'", default=default_public_availability_zone, required=False, type=str)
        parser.add_argument('--private-zone', help=f"Availability zone used for the private subnet. Default is '{default_private_availability_zone}'", default=default_private_availability_zone, required=False, type=str)
        parser.add_argument('--cleanup', '-c', help=f"Find and delete AWS resources created by this script (default is --no-cleanup).", action=argparse.BooleanOptionalAction, default=False)
        Configuration.args = parser.parse_args()
        Configuration._profile_name = Configuration.args.profile
        Configuration._region_name = Configuration.args.region
        
        if os.path.exists('logging.json'):
            with open('logging.json', "rt") as f:
                config = json.load(f)
            logging.config.dictConfig(config)

        logheader = f"\n\n{description}\n"
        logheader += "\n\t* Using the following configurations from command line arguments (default values are set in config.ini file):\n"
        for key, value in vars(Configuration.args).items():
            logheader += (f"\t\t** {key:27}: {value}\n")
        logheader += "\n\t* The following defaults are set in config.ini\n"
        for section in Configuration._config.sections():
            logheader += (f"\t\t** {section}:\n")
            for key, value in Configuration._config.items(section):
                logheader += (f"\t\t***  {key:25}: {value}\n")
        logheader += ("\t**")
        logging.info(logheader)

        Configuration._session = Session(profile_name=Configuration.profile_name, region_name=Configuration.region_name)
        Configuration._setup_already = True

    @classproperty
    def session(cls):
        return cls._session

    @classproperty
    def profile_name(cls):
        return cls._profile_name
    
    @classproperty
    def region_name(cls):
        return cls._region_name
    
    @classproperty
    def instances_ami_id(cls):
        return cls._config.get('Instances', 'ami_id')

    @classproperty
    def instances_type(cls):
        return cls._config.get('Instances', 'type')
    
    @classproperty
    def instances_root_volume_device_name(cls):
        return cls._config.get('Instances', 'root.volume.device.name')

    @classproperty
    def instances_default_volume_size(cls):
        return cls._config.get('Instances', 'default.volume.size')

    @classproperty 
    def connectivity_keypair_name(cls):
        return cls._config.get('Connectivity', 'keypair.name')

    @classproperty
    def vpc_cidr_block(cls):
        return cls._config.get('VPC', 'cidr.block')
    
    @classproperty
    def public_subnet_availability_zone(cls):
        return cls._config.get('PublicSubnet', 'availability.zone')
    
    @classproperty
    def public_subnet_cidr_blck(cls):
        return cls._config.get('PublicSubnet', 'cidr.block')
    
    @classproperty
    def private_subnet_availability_zone(cls):
        return cls._config.get('PrivateSubnet', 'availability.zone')
    
    @classproperty
    def private_subnet_cidr_blck(cls):
        return cls._config.get('PrivateSubnet', 'cidr.block')
    
    @classproperty
    def ownCloudInstance_ebs_volume_size(cls):
        return cls._config.getint('ownCloudInstance', 'ebs.volume.size')

    @classproperty
    def mySQLInstance_ebs_volume_size(cls):
        return cls._config.getint('mySQLInstance', 'ebs.volume.size')
