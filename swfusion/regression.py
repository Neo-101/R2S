import logging
import os
import warnings
warnings.filterwarnings('ignore')
warnings.filterwarnings('ignore', category=DeprecationWarning)

import numpy as np
import pandas as pd
from sqlalchemy.orm import mapper
from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
import seaborn as sb
from keras.models import Sequential
from keras.callbacks import ModelCheckpoint
from keras.layers import Dense, Activation, Flatten
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from xgboost import XGBRegressor

import utils

Base = declarative_base()

class Regression(object):

    def __init__(self, CONFIG, period, region, passwd):
        self.logger = logging.getLogger(__name__)
        self.CONFIG = CONFIG
        self.period = period
        self.region = region
        self.db_root_passwd = passwd
        self.engine = None
        self.session = None

        self.smap_columns = ['x', 'y', 'lon', 'lat', 'windspd']
        self.era5_columns = ['divergence', 'fraction_of_cloud_cover',
                             'geopotential', 'ozone_mass_mixing_ratio',
                             'potential_vorticity', 'relative_humidity',
                             'specific_cloud_ice_water_content',
                             'specific_cloud_liquid_water_content',
                             'specific_humidity',
                             'specific_rain_water_content',
                             'specific_snow_water_content', 'temperature',
                             'u_component_of_wind', 'v_component_of_wind',
                             'vertical_velocity', 'vorticity_relative']
        self.useless_columns = ['key', 'match_sid',
                                'temporal_window_mins',
                                'satel_tc_diff_mins', 'tc_datetime',
                                'satel_datetime', 'era5_datetime',
                                'satel_datetime_lon_lat',
                                'satel_era5_diff_mins']
        self.epochs = 500
        self.batch_size = 32
        self.validation_split = 0.2

        utils.setup_database(self, Base)

        self.read_era5_smap()
        self.make_DNN()
        self.train_DNN()

    def _get_table_class_by_name(self, table_name):

        class Target(object):
            pass

        if self.engine.dialect.has_table(self.engine, table_name):
            metadata = MetaData(bind=self.engine, reflect=True)
            t = metadata.tables[table_name]
            mapper(Target, t)

            return Target

    def train_DNN(self):
        # self.NN_model.fit(self.train, self.target, epochs=self.epochs,
        #                   batch_size=self.batch_size,
        #                   validation_split=self.validation_split,
        #                   callbacks=self.callbacks_list)

        # Load weights file of the best model:
        # choose the best checkpoint
        weights_file = 'Weights-438--1.16947.hdf5'
        # load it
        self.NN_model.load_weights(weights_file)
        self.NN_model.compile(loss='mean_absolute_error',
                              optimizer='adam',
                              metrics=['mean_absolute_error'])
        score = self.NN_model.evaluate(self.train, self.target,
                                       verbose=0)
        metrics_names = self.NN_model.metrics_names
        for i in range(len(metrics_names)):
            print(f'{metrics_names[i]}: {score[i]}')

    def make_DNN(self):
        self.NN_model = Sequential()
        self.NN_model.add(Dense(128, kernel_initializer='normal',
                                input_dim = self.train.shape[1],
                                activation='relu'))
        for i in range(3):
            self.NN_model.add(Dense(256, kernel_initializer='normal',
                                    activation='relu'))
        self.NN_model.add(Dense(1, kernel_initializer='normal',
                                activation='linear'))
        self.NN_model.compile(loss='mean_absolute_error',
                              optimizer='adam',
                              metrics=['mean_absolute_error'])

        self.NN_model.summary()

        checkpoint_name = 'Weights-{epoch:03d}--{val_loss:.5f}.hdf5'
        checkpoint = ModelCheckpoint(checkpoint_name,
                                     monitor='val_loss',
                                     verbose=1, save_best_only=True,
                                     mode ='auto')
        self.callbacks_list = [checkpoint]

    def read_era5_smap(self):
        train_data, test_data = self._get_train_test()
        combined, target, train_length = self.get_combined_data()

        num_cols = self.get_cols_with_no_nans(combined, 'num')
        # print ('Number of numerical columns with no nan values :',
        #        len(num_cols))

        # train_data['Target'] = target

        # C_mat = train_data.corr()
        # fig = plt.figure(figsize=(15, 15))
        # sb.heatmap(C_mat, vmax=.8, square=True)
        # plt.show()

        self.train, self.test = self.split_combined(combined,
                                                    train_length)
        self.target = target

    def split_combined(self, combined, train_length):
        train = combined[:train_length]
        test = combined[train_length:]

        return train , test

    def get_combined_data(self):
        train, test = self._get_train_test()
        train_length = len(train)

        target = train.windspd
        train.drop(['windspd'], axis=1, inplace=True)
        test.drop(['windspd'], axis=1, inplace=True)

        combined = train.append(test)
        combined.reset_index(inplace=True)
        combined.drop(['index'], axis=1, inplace=True)

        return combined, target, train_length

    def _get_train_test(self):
        table_name = 'smap_2015'
        df = pd.read_sql('SELECT * FROM smap_2018', self.engine)
        df.drop(self.useless_columns, axis=1, inplace=True)
        train, test = train_test_split(df, test_size=0.2)

        return train, test

    def get_cols_with_no_nans(self, df, col_type):
        '''
        Arguments :
        df : The dataframe to process
        col_type : 
              num : to only get numerical columns with no nans
              no_num : to only get nun-numerical columns with no nans
              all : to get any columns with no nans    
        '''
        if (col_type == 'num'):
            predictors = df.select_dtypes(exclude=['object'])
        elif (col_type == 'no_num'):
            predictors = df.select_dtypes(include=['object'])
        elif (col_type == 'all'):
            predictors = df
        else :
            print('Error : choose a type (num, no_num, all)')
            return 0
        cols_with_no_nans = []
        for col in predictors.columns:
            if not df[col].isnull().any():
                cols_with_no_nans.append(col)

        return cols_with_no_nans

    def _show_dataframe(self, df):
        df.hist(column=self.era5_columns, figsize = (12,10))
        plt.show()

