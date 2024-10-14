import numpy as np
from utils.metric import evaluate
from utils.load_config import get_attribute
from train.train_main import create_model
import torch
from utils.data_container import get_data_loaders
from tqdm import tqdm
from utils.util import convert_train_truth_to_gpu
from utils.util import convert_to_gpu
import warnings

if __name__ == '__main__':
    warnings.filterwarnings('ignore')

    model_path = f"../saves/SATGCN/model_0.pkl"
    print(f'model path -> {model_path}')
    model = create_model()
    model.load_state_dict(torch.load(model_path)["model_state_dict"])
    print(f'model epoch -> {torch.load(model_path)["epoch"]}')
    model = convert_to_gpu(model)
    print(model)

    data_loaders = get_data_loaders(get_attribute('K_hop'), get_attribute('batch_size'))
    phase = "test"

    model.eval()
    tqdm_loader = tqdm(data_loaders[phase])
    predictions, targets = list(), list()
    for g, spatial_features, temporal_features, external_features, truth_data in tqdm_loader:

        features, truth_data = convert_train_truth_to_gpu(
            [spatial_features, temporal_features, external_features], truth_data)
        g = convert_to_gpu(g)

        outputs = model(g, *features)
        outputs = torch.squeeze(outputs)  # squeeze [batch-size, 1] to [batch-size]

        with torch.no_grad():
            predictions.append(outputs.cpu().numpy())
        targets.append(truth_data.cpu().numpy())

    scores = evaluate(np.concatenate(predictions), np.concatenate(targets))

    print('===== Test predict result =====')

    print(f'scores -> {scores}')
