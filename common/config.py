import argparse, logging, logging.config, json, os, configparser
from common.utils import classproperty
from common.session import Session

class Configuration:
    args = None
    _project_name = None
    _config = None
    _profile_name = None
    _region_name = None
    _setup_already = False
    _parser = None

    def reloadconfig(config_file_name: str = 'config.ini'): 
        Configuration._config = configparser.ConfigParser(inline_comment_prefixes="#;")
        Configuration._config.read(filenames=config_file_name)

    def getArgParser(project_description: str, config_file_name: str = 'config.ini') -> argparse.ArgumentParser:
        if Configuration._parser != None: return Configuration._parser

        Configuration._parser = argparse.ArgumentParser(
            description=project_description, 
            epilog="NOTE: these default values are specified in 'config.ini'", 
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        Configuration.reloadconfig(config_file_name)
        default_profile_name    = Configuration._config.get('AWSCli', 'default.profile.name')
        default_region_name     = Configuration._config.get('AWSCli','default.region.name')
        Configuration._parser.add_argument('--profile-name', '-pn', help=f"AWS Config profile to use.", default=default_profile_name, required=False, type=str)
        Configuration._parser.add_argument('--region-name', '-rn', help=f"Region to use.", default=default_region_name, required=False, type=str)
        return Configuration._parser
    
    def getCmdLineArgs(project_description: str, config_file_name: str = 'config.ini') -> object:
        if Configuration.args: return Configuration.args

        Configuration.getArgParser(project_description=project_description, config_file_name=config_file_name)
        Configuration._parser.add_argument('--cleanup', '-c', help=f"Find and delete AWS resources created by this script.", action=argparse.BooleanOptionalAction, default=False)
        Configuration.args = Configuration._parser.parse_args()
        return Configuration.args
        
    def setup(project_name: str, project_description: str, config_file_name: str = 'config.ini'):
        if Configuration._setup_already: return
        
        Configuration._project_name = project_name
        Configuration.getCmdLineArgs(project_description, config_file_name)

        Configuration._profile_name = Configuration.args.profile_name
        Configuration._region_name = Configuration.args.region_name
        
        if os.path.exists('logging.json'):
            with open('logging.json', "rt") as f:
                config = json.load(f)
            logging.config.dictConfig(config)

        logheader = f"\n\nProject Name: {project_name}"
        logheader += f"\n\nProject Description: {project_description}\n"
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
        Session.connect(Configuration._profile_name, Configuration._region_name)
        Configuration._setup_already = True

    @classproperty
    def project_name(cls) -> str:
        return cls._project_name
    
    @classproperty
    def profile_name(cls) -> str:
        return cls._profile_name
    
    @classproperty
    def region_name(cls) -> str:
        return cls._region_name
    
    @classproperty
    def default_ami_id(cls) -> str:
        return cls._config.get('Default', 'ami_id')

    @classproperty
    def default_root_volume_device_name(cls) -> str:
        return cls._config.get('Default', 'root.volume.device.name')

    @classproperty
    def default_instance_type(cls) -> str:
        return cls._config.get('Default', 'instance.type')
    
    @classproperty
    def default_ebs_volume_size(cls) -> int:
        return cls._config.getint('Default', 'default.ebs.volume.size')

    @classproperty
    def ownCloud_ami_id(cls) -> str:
        return cls._config.get('ownCloud', 'ami_id')

    @classproperty
    def ownCloud_root_volume_device_name(cls) -> str:
        return cls._config.get('ownCloud', 'root.volume.device.name')

    @classproperty
    def ownCloud_instance_type(cls) -> str:
        return cls._config.get('ownCloud', 'instance.type')

    @classproperty
    def ownCloud_ebs_volume_size(cls) -> int:
        return cls._config.getint('ownCloud', 'ebs.volume.size')

    @classproperty
    def matterMost_ami_id(cls) -> str:
        return cls._config.get('matterMost', 'ami_id')

    @classproperty
    def matterMost_root_volume_device_name(cls) -> str:
        return cls._config.get('matterMost', 'root.volume.device.name')

    @classproperty
    def matterMost_instance_type(cls) -> str:
        return cls._config.get('matterMost', 'instance.type')

    @classproperty
    def matterMost_ebs_volume_size(cls) -> str:
        return cls._config.getint('matterMost', 'ebs.volume.size')
