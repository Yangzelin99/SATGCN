import os
import shutil

from torch import optim, nn
import numpy as np
import json
import sys
import warnings

from model.SATGCN import SATGCN
from train.train_model import train_model
from utils.data_container import get_data_loaders
from utils.load_config import get_attribute
from utils.loss import MSELoss, BCELoss


def create_model() -> nn.Module:
    return SATGCN(get_attribute('poi_features_number'), get_attribute('temporal_features_number'),
                  get_attribute('weather_features_number') + get_attribute('external_temporal_features_number'))


def create_loss(loss_type):
    if loss_type == 'mse_loss':
        return MSELoss()
    elif loss_type == 'bce_loss':
        return BCELoss()
    else:
        raise ValueError("Unknown loss function.")


if __name__ == '__main__':
    warnings.filterwarnings('ignore')

    # create data_loader
    data_loaders = get_data_loaders(get_attribute('K_hop'), get_attribute('batch_size'))

    test_metrics = []

    for train_time in range(get_attribute("train_repeat_times")):

        print(f"train SATGCN model for the {train_time + 1}-th time ...")

        model = create_model()
        loss_func = create_loss(loss_type=get_attribute('loss_function'))

        model_folder = f"../saves/{get_attribute('model_name')}"
        tensorboard_folder = f"../runs/{get_attribute('model_name')}"

        shutil.rmtree(model_folder, ignore_errors=True)
        os.makedirs(model_folder, exist_ok=True)
        shutil.rmtree(tensorboard_folder, ignore_errors=True)
        os.makedirs(tensorboard_folder, exist_ok=True)

        if get_attribute("optim") == "Adam":
            optimizer = optim.Adam(model.parameters(),
                                   lr=get_attribute("learning_rate"),
                                   weight_decay=get_attribute("weight_decay"))
        elif get_attribute("optim") == "SGD":
            optimizer = optim.SGD(model.parameters(),
                                  lr=get_attribute("learning_rate"),
                                  momentum=0.9)
        else:
            raise NotImplementedError()

        test_metric = train_model(model=model,
                                  data_loaders=data_loaders,
                                  loss_func=loss_func,
                                  optimizer=optimizer,
                                  model_folder=model_folder,
                                  tensorboard_folder=tensorboard_folder)
        print(f'final test metric {test_metric}')
        test_metrics.append(test_metric)

    metrics = {}
    for key in test_metrics[0].keys():
        metric_list = [metric[key] for metric in test_metrics]
        mean_value = np.mean(metric_list)
        if key in ["MSE", "RMSE", "MAE"]:
            best_value = np.min(metric_list)
        else:
            best_value = np.max(metric_list)
        std_value = np.std(metric_list, ddof=1)
        metrics[f"mean_{key}"] = float(mean_value)
        metrics[f"best_{key}"] = float(best_value)
        metrics[f"std_{key}"] = float(std_value)

    scores = sorted(metrics.items(), key=lambda item: item[0], reverse=False)
    scores = {item[0]: item[1] for item in scores}

    scores_str = json.dumps(scores, indent=4)

    results_folder = f"../results"
    if not os.path.exists(results_folder):
        os.makedirs(results_folder, exist_ok=True)

    save_path = f"{results_folder}/{get_attribute('model_name')}_result.json"
    with open(save_path, 'w') as file:
        file.write(scores_str)
    print(f'save path is {save_path}')
    print(f"metric -> {scores_str}")

    # sys.exit()
