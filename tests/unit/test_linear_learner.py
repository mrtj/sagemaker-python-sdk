# Copyright 2017-2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
from __future__ import absolute_import

import pytest
from mock import Mock, patch

from sagemaker.amazon.linear_learner import LinearLearner, LinearLearnerPredictor
from sagemaker.amazon.amazon_estimator import registry, RecordSet

ROLE = 'myrole'
TRAIN_INSTANCE_COUNT = 1
TRAIN_INSTANCE_TYPE = 'ml.c4.xlarge'

PREDICTOR_TYPE = 'binary_classifier'

COMMON_TRAIN_ARGS = {'role': ROLE, 'train_instance_count': TRAIN_INSTANCE_COUNT,
                     'train_instance_type': TRAIN_INSTANCE_TYPE}
ALL_REQ_ARGS = dict({'predictor_type': PREDICTOR_TYPE}, **COMMON_TRAIN_ARGS)

REGION = 'us-west-2'
BUCKET_NAME = 'Some-Bucket'

DESCRIBE_TRAINING_JOB_RESULT = {
    'ModelArtifacts': {
        'S3ModelArtifacts': 's3://bucket/model.tar.gz'
    }
}


@pytest.fixture()
def sagemaker_session():
    boto_mock = Mock(name='boto_session', region_name=REGION)
    sms = Mock(name='sagemaker_session', boto_session=boto_mock,
               region_name=REGION, config=None, local_mode=False)
    sms.boto_region_name = REGION
    sms.default_bucket = Mock(name='default_bucket', return_value=BUCKET_NAME)
    sms.sagemaker_client.describe_training_job = Mock(name='describe_training_job',
                                                      return_value=DESCRIBE_TRAINING_JOB_RESULT)

    return sms


def test_init_required_positional(sagemaker_session):
    lr = LinearLearner(ROLE, TRAIN_INSTANCE_COUNT, TRAIN_INSTANCE_TYPE, PREDICTOR_TYPE,
                       sagemaker_session=sagemaker_session)
    assert lr.role == ROLE
    assert lr.train_instance_count == TRAIN_INSTANCE_COUNT
    assert lr.train_instance_type == TRAIN_INSTANCE_TYPE
    assert lr.predictor_type == PREDICTOR_TYPE


def test_init_required_named(sagemaker_session):
    lr = LinearLearner(sagemaker_session=sagemaker_session, **ALL_REQ_ARGS)

    assert lr.role == ALL_REQ_ARGS['role']
    assert lr.train_instance_count == ALL_REQ_ARGS['train_instance_count']
    assert lr.train_instance_type == ALL_REQ_ARGS['train_instance_type']
    assert lr.predictor_type == ALL_REQ_ARGS['predictor_type']


def test_all_hyperparameters(sagemaker_session):
    lr = LinearLearner(sagemaker_session=sagemaker_session,
                       binary_classifier_model_selection_criteria='accuracy',
                       target_recall=0.5, target_precision=0.6,
                       positive_example_weight_mult=0.1, epochs=1, use_bias=True, num_models=5,
                       num_calibration_samples=6, init_method='uniform', init_scale=0.1, init_sigma=0.001,
                       init_bias=0, optimizer='sgd', loss='logistic', wd=0.4, l1=0.04, momentum=0.1,
                       learning_rate=0.001, beta_1=0.2, beta_2=0.03, bias_lr_mult=5.5, bias_wd_mult=6.6,
                       use_lr_scheduler=False, lr_scheduler_step=2, lr_scheduler_factor=0.03,
                       lr_scheduler_minimum_lr=0.001, normalize_data=False, normalize_label=True,
                       unbias_data=True, unbias_label=False, num_point_for_scaler=3, margin=1.0,
                       quantile=0.5, loss_insensitivity=0.1, huber_delta=0.1, early_stopping_patience=3,
                       early_stopping_tolerance=0.001, **ALL_REQ_ARGS)

    assert lr.hyperparameters() == dict(
        predictor_type='binary_classifier', binary_classifier_model_selection_criteria='accuracy',
        target_recall='0.5', target_precision='0.6', positive_example_weight_mult='0.1', epochs='1',
        use_bias='True', num_models='5', num_calibration_samples='6', init_method='uniform',
        init_scale='0.1', init_sigma='0.001', init_bias='0.0', optimizer='sgd', loss='logistic',
        wd='0.4', l1='0.04', momentum='0.1', learning_rate='0.001', beta_1='0.2', beta_2='0.03',
        bias_lr_mult='5.5', bias_wd_mult='6.6', use_lr_scheduler='False', lr_scheduler_step='2',
        lr_scheduler_factor='0.03', lr_scheduler_minimum_lr='0.001', normalize_data='False',
        normalize_label='True', unbias_data='True', unbias_label='False', num_point_for_scaler='3', margin='1.0',
        quantile='0.5', loss_insensitivity='0.1', huber_delta='0.1', early_stopping_patience='3',
        early_stopping_tolerance='0.001',
    )


def test_image(sagemaker_session):
    lr = LinearLearner(sagemaker_session=sagemaker_session, **ALL_REQ_ARGS)
    assert lr.train_image() == registry(REGION, 'linear-learner') + '/linear-learner:1'


@pytest.mark.parametrize('required_hyper_parameters, value', [
    ('predictor_type', 0)
])
def test_required_hyper_parameters_type(sagemaker_session, required_hyper_parameters, value):
    with pytest.raises(ValueError):
        test_params = ALL_REQ_ARGS.copy()
        test_params[required_hyper_parameters] = value
        LinearLearner(sagemaker_session=sagemaker_session, **test_params)


@pytest.mark.parametrize('required_hyper_parameters, value', [
    ('predictor_type', 'string')
])
def test_required_hyper_parameters_value(sagemaker_session, required_hyper_parameters, value):
    with pytest.raises(ValueError):
        test_params = ALL_REQ_ARGS.copy()
        test_params[required_hyper_parameters] = value
        LinearLearner(sagemaker_session=sagemaker_session, **test_params)


@pytest.mark.parametrize('iterable_hyper_parameters, value', [
    ('eval_metrics', 0)
])
def test_iterable_hyper_parameters_type(sagemaker_session, iterable_hyper_parameters, value):
    with pytest.raises(TypeError):
        test_params = ALL_REQ_ARGS.copy()
        test_params.update({iterable_hyper_parameters: value})
        LinearLearner(sagemaker_session=sagemaker_session, **test_params)


@pytest.mark.parametrize('optional_hyper_parameters, value', [
    ('binary_classifier_model_selection_criteria', 0),
    ('target_recall', 'string'),
    ('target_precision', 'string'),
    ('epochs', 'string'),
    ('num_models', 'string'),
    ('num_calibration_samples', 'string'),
    ('init_method', 0),
    ('init_scale', 'string'),
    ('init_sigma', 'string'),
    ('init_bias', 'string'),
    ('optimizer', 0),
    ('loss', 0),
    ('wd', 'string'),
    ('l1', 'string'),
    ('momentum', 'string'),
    ('learning_rate', 'string'),
    ('beta_1', 'string'),
    ('beta_2', 'string'),
    ('bias_lr_mult', 'string'),
    ('bias_wd_mult', 'string'),
    ('lr_scheduler_step', 'string'),
    ('lr_scheduler_factor', 'string'),
    ('lr_scheduler_minimum_lr', 'string'),
    ('num_point_for_scaler', 'string'),
    ('margin', 'string'),
    ('quantile', 'string'),
    ('loss_insensitivity', 'string'),
    ('huber_delta', 'string'),
    ('early_stopping_patience', 'string'),
    ('early_stopping_tolerance', 'string')
])
def test_optional_hyper_parameters_type(sagemaker_session, optional_hyper_parameters, value):
    with pytest.raises(ValueError):
        test_params = ALL_REQ_ARGS.copy()
        test_params.update({optional_hyper_parameters: value})
        LinearLearner(sagemaker_session=sagemaker_session, **test_params)


@pytest.mark.parametrize('optional_hyper_parameters, value', [
    ('binary_classifier_model_selection_criteria', 'string'),
    ('target_recall', 0),
    ('target_recall', 1),
    ('target_precision', 0),
    ('target_precision', 1),
    ('epochs', 0),
    ('num_models', 0),
    ('num_calibration_samples', 0),
    ('init_method', 'string'),
    ('init_scale', 0),
    ('init_sigma', 0),
    ('optimizer', 'string'),
    ('loss', 'string'),
    ('wd', -1),
    ('l1', -1),
    ('momentum', 1),
    ('learning_rate', 0),
    ('beta_1', 1),
    ('beta_2', 1),
    ('bias_lr_mult', 0),
    ('bias_wd_mult', -1),
    ('lr_scheduler_step', 0),
    ('lr_scheduler_factor', 0),
    ('lr_scheduler_factor', 1),
    ('lr_scheduler_minimum_lr', 0),
    ('num_point_for_scaler', 0),
    ('margin', -1),
    ('quantile', 0),
    ('quantile', 1),
    ('loss_insensitivity', 0),
    ('huber_delta', -1),
    ('early_stopping_patience', 0),
    ('early_stopping_tolerance', 0)
])
def test_optional_hyper_parameters_value(sagemaker_session, optional_hyper_parameters, value):
    with pytest.raises(ValueError):
        test_params = ALL_REQ_ARGS.copy()
        test_params.update({optional_hyper_parameters: value})
        LinearLearner(sagemaker_session=sagemaker_session, **test_params)


PREFIX = 'prefix'
FEATURE_DIM = 10
DEFAULT_MINI_BATCH_SIZE = 1000


@patch('sagemaker.amazon.amazon_estimator.AmazonAlgorithmEstimatorBase.fit')
def test_call_fit_calculate_batch_size_1(base_fit, sagemaker_session):
    lr = LinearLearner(base_job_name='lr', sagemaker_session=sagemaker_session, **ALL_REQ_ARGS)

    data = RecordSet('s3://{}/{}'.format(BUCKET_NAME, PREFIX), num_records=1, feature_dim=FEATURE_DIM, channel='train')

    lr.fit(data)

    base_fit.assert_called_once()
    assert len(base_fit.call_args[0]) == 2
    assert base_fit.call_args[0][0] == data
    assert base_fit.call_args[0][1] == 1


@patch('sagemaker.amazon.amazon_estimator.AmazonAlgorithmEstimatorBase.fit')
def test_call_fit_calculate_batch_size_2(base_fit, sagemaker_session):
    lr = LinearLearner(base_job_name='lr', sagemaker_session=sagemaker_session, **ALL_REQ_ARGS)

    data = RecordSet('s3://{}/{}'.format(BUCKET_NAME, PREFIX),
                     num_records=10000,
                     feature_dim=FEATURE_DIM,
                     channel='train')

    lr.fit(data)

    base_fit.assert_called_once()
    assert len(base_fit.call_args[0]) == 2
    assert base_fit.call_args[0][0] == data
    assert base_fit.call_args[0][1] == DEFAULT_MINI_BATCH_SIZE


@patch('sagemaker.amazon.amazon_estimator.AmazonAlgorithmEstimatorBase.fit')
def test_call_fit_pass_batch_size(base_fit, sagemaker_session):
    lr = LinearLearner(base_job_name='lr', sagemaker_session=sagemaker_session, **ALL_REQ_ARGS)

    data = RecordSet('s3://{}/{}'.format(BUCKET_NAME, PREFIX),
                     num_records=10000,
                     feature_dim=FEATURE_DIM,
                     channel='train')

    lr.fit(data, 10)

    base_fit.assert_called_once()
    assert len(base_fit.call_args[0]) == 2
    assert base_fit.call_args[0][0] == data
    assert base_fit.call_args[0][1] == 10


def test_model_image(sagemaker_session):
    lr = LinearLearner(sagemaker_session=sagemaker_session, **ALL_REQ_ARGS)
    data = RecordSet('s3://{}/{}'.format(BUCKET_NAME, PREFIX), num_records=1, feature_dim=FEATURE_DIM, channel='train')
    lr.fit(data)

    model = lr.create_model()
    assert model.image == registry(REGION, 'linear-learner') + '/linear-learner:1'


def test_predictor_type(sagemaker_session):
    lr = LinearLearner(sagemaker_session=sagemaker_session, **ALL_REQ_ARGS)
    data = RecordSet('s3://{}/{}'.format(BUCKET_NAME, PREFIX), num_records=1, feature_dim=FEATURE_DIM, channel='train')
    lr.fit(data)
    model = lr.create_model()
    predictor = model.deploy(1, TRAIN_INSTANCE_TYPE)

    assert isinstance(predictor, LinearLearnerPredictor)
