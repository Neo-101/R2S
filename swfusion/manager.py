"""Manager of tropical cyclone ocean surface wind reanalysis system.

"""
from datetime import datetime
import logging
import os

import regression
import cwind
import stdmet
import sfmr
import satel
import compare_offshore
import ibtracs
import era5
import hwind
import load_configs
import utils
import ascat

def work_flow():
    """The work flow of blending several TC OSW.
    """
    load_configs.setup_logging()
    logger = logging.getLogger(__name__)
    # CONFIG
    try:
        CONFIG = load_configs.load_config()
    except Exception as msg:
        logger.exception('Exception occurred when loading config.')
    os.makedirs(CONFIG['logging']['dir'], exist_ok=True)
    # Period
    train_period = [datetime(2016, 7, 1, 0, 0, 0),
                    datetime(2016, 9, 30, 23, 59, 59)]
    logger.info(f'Period: {train_period}')
    # Region
    region = [0, 30, 98, 125]
    logger.info(f'Region: {region}')
    # MySQL Server root password
    passwd = '399710'
    # Download and read
    try:
        ascat_ = ascat.ASCATManager(CONFIG, train_period, region, passwd,
                                    save_disk=False)
        # ibtracs_ = ibtracs.IBTrACSManager(CONFIG, train_period, region, passwd)
        # cwind_ = cwind.CwindManager(CONFIG, train_period, region, passwd)
        # stdmet_ = stdmet.StdmetManager(CONFIG, train_period, region, passwd)
        # sfmr_ = sfmr.SfmrManager(CONFIG, train_period, region, passwd)
        # satel_ = satel.SatelManager(CONFIG, train_period, region, passwd,
        #                             save_disk=False)
        # compare_ = compare_offshore.CompareCCMPWithInStu(
        #     CONFIG, train_period, region, passwd)
        pass
    except Exception as msg:
        logger.exception('Exception occured when downloading and reading')

    """
    test_period = [datetime(2013, 6, 6, 0, 0, 0),
                   datetime(2013, 6, 6, 23, 0, 0)]
    try:
        regression_ = regression.Regression(CONFIG, train_period,
                                            test_period, region, passwd,
                                            save_disk=False)
        # ibtracs_ = ibtracs.IBTrACSManager(CONFIG, test_period,
        #                                   region, passwd)
        hwind_ = hwind.HWindManager(CONFIG, test_period, region, passwd)
        # era5_ = era5.ERA5Manager(CONFIG, test_period, region, passwd,
        #                          work=True, save_disk=False)
    except Exception as msg:
        logger.exception('Exception occured when downloading and reading')
    """

    logger.info('SWFusion complete.')
    # Match
    # Validate
    # Fusion

if __name__ == '__main__':
    work_flow()
