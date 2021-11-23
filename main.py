import random

import torch
import torch.nn.functional as F
import os
import pickle

import numpy as np
import pandas as pd
import torch
import torch.utils.data

from torch_geometric.data import Data
from preprocess import CompDataset
from preprocess import get_user_data

from learning_model import FocalLoss


class Worker(object):
    def __init__(self, user_idx):
        self.user_idx = user_idx
        self.data, self.edges = get_user_data(self.user_idx)  # The worker can only access its own data
        self.ps_info = {}

        self.sample_ids = None
        self.positive_ids = None
        self.negative_ids = None

    def preprocess_worker_data(self):
        self.sample_ids = self.data[self.data['class'] != 2]['txId'].to_numpy()
        self.positive_ids = self.data[self.data['class'] == 1]['txId'].to_numpy()
        self.negative_ids = self.data[self.data['class'] == 0]['txId'].to_numpy()

        x = self.data.iloc[:, 2:]
        x = x.reset_index(drop=True)
        x = x.to_numpy().astype(np.float32)
        y = self.data['class']
        y = y.reset_index(drop=True)
        x[x == np.inf] = 1.
        x[np.isnan(x)] = 0.

        us = np.append(
            self.edges.iloc[:, 0].to_numpy(),
            self.edges.iloc[:, 1].to_numpy()
        )
        vs = np.append(
            self.edges.iloc[:, 1].to_numpy(),
            self.edges.iloc[:, 0].to_numpy()
        )
        edge_index = [
            us, vs
        ]
        self.data = (x, edge_index, y)

    def round_data(self, n_round, n_round_samples=-1):
        """Generate data for user of user_idx at round n_round.

        Args:
            n_round: int, round number
            n_round_samples: int, the number of samples this round
        """

        if n_round_samples == -1:
            return self.data

        n_samples = len(self.data[1])
        choices = np.random.choice(n_samples, min(n_samples, n_round_samples))

        return (self.data[0][0][choices], self.data[0][1]), self.data[1][choices]

    def receive_server_info(self, info):  # receive info from PS
        self.ps_info = info

    def process_mean_round_train_acc(self):  # process the "mean_round_train_acc" info from server
        mean_round_train_acc = self.ps_info["mean_round_train_acc"]
        # You can go on to do more processing if needed

    def _random_sample(self, batch_size: int) -> torch.Tensor:
        """
        随机采样，0表示没选中，1表示被采样选中
        :param batch_size: 采样个数
        :return: 采样向量
        """
        sample = list()
        for _ in range(batch_size):
            idx = random.choice(self.sample_ids)
            sample.append(idx)
        return torch.tensor(sample)

    def _bias_sample(self, batch_size: int, pos_rate: float = 0.5) -> torch.Tensor:
        """
        有偏采样，0表示没选中，1表示被采样选中
        :param batch_size: 采样个数
        :param pos_rate: 正例采样比例
        :return: 采样向量
        """
        sample = list()
        pos_sample_cnt = int(batch_size * pos_rate)
        for _ in range(pos_sample_cnt):
            idx = random.choice(self.positive_ids)
            sample.append(idx)
        for _ in range(batch_size - pos_sample_cnt):
            idx = random.choice(self.negative_ids)
            sample.append(idx)
        return torch.tensor(sample)

    def user_round_train(self, model, device, n_round, batch_size, n_round_samples=-1, debug=False):

        data = Data(
            x=torch.tensor(self.data[0]),
            edge_index=torch.tensor(self.data[1]),
            y=torch.tensor(self.data[2])
        )

        model.train()

        correct = 0
        prediction = []
        real = []
        total_loss = 0
        model = model.to(device)
        for batch_idx in range(n_round_samples // batch_size):
            # 前向传播
            data = data.to(device)
            output = model(data)

            # 采样
            sample = self._random_sample(batch_size)
            output = output.index_select(0, sample)
            target = data.y.index_select(0, sample)

            # 反向传播
            # loss = FocalLoss(
            #    class_num=2,
            #    gamma=2
            # )(output, target)
            loss = F.nll_loss(output, target)
            total_loss += loss
            loss.backward()
            pred = output.argmax(
                dim=1, keepdim=True
            )  # get the index of the max log-probability
            correct += pred.eq(target.view_as(pred)).sum().item()
            prediction.extend(pred.reshape(-1).tolist())
            real.extend(target.reshape(-1).tolist())

        grads = {'n_samples': n_round_samples, 'named_grads': {}}
        for name, param in model.named_parameters():
            grads['named_grads'][name] = param.grad.detach().cpu().numpy()

        worker_info = {}
        worker_info["train_acc"] = correct / n_round_samples

        if debug:
            print('Training Loss: {:<10.2f}, accuracy: {:<8.2f}'.format(
                total_loss, 100. * correct / n_round_samples
            ))

        return grads, worker_info
