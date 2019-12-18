from typing import List, Tuple

import pandas as pd
import torch
from pytorch_lightning import LightningModule, Trainer, data_loader
from pytorch_lightning.logging import TestTubeLogger
from torch.nn import Linear, functional
from torch.optim import Adam
from torch.utils.data import TensorDataset, DataLoader


class AttributeModel(LightningModule):
    TRAIN_DATA_PATH = '../data/iMaterialist/pairs_train.csv'
    TEST_DATA_PATH = '../data/iMaterialist/pairs_test.csv'

    BATCH_SIZE = 10

    NUM_CATEGORIES = 46 - 34
    NUM_ATTRIBUTES = 92 - 53

    def __init__(self):
        super(AttributeModel, self).__init__()

        self.classes = None

        num_inputs = 51
        num_outputs = num_inputs

        fc1_size = 512
        fc2_size = 512
        fc3_size = 256
        fc4_size = 256

        self.fc1 = Linear(num_inputs, fc1_size)
        self.fc2 = Linear(fc1_size, fc2_size)
        self.fc3 = Linear(fc2_size, fc3_size)
        self.fc4 = Linear(fc3_size, fc4_size)
        self.fc_out = Linear(fc4_size, num_outputs)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = torch.relu(self.fc3(x))
        x = torch.relu(self.fc4(x))
        return self.fc_out(x)

    def training_step(self, batch, batch_nb):
        x, y = batch
        y_hat = self.forward(x)

        loss = functional.binary_cross_entropy_with_logits(y_hat, y)
        return {
            'loss': loss
        }

    def validation_step(self, batch, batch_nb):
        x, y = batch
        y_hat = self.forward(x)

        loss = functional.binary_cross_entropy_with_logits(y_hat, y)

        category_y = y[:, :AttributeModel.NUM_CATEGORIES].argmax(dim=1)
        category_y_hat = y_hat[:, :AttributeModel.NUM_CATEGORIES]
        category_pred = category_y_hat.argmax(dim=1)

        category_accuracy = torch.sum(category_y == category_pred, dtype=torch.float) / AttributeModel.BATCH_SIZE

        attribute_y = y[:, AttributeModel.NUM_CATEGORIES:].argmax(dim=1)
        attribute_y_hat = y_hat[:, AttributeModel.NUM_CATEGORIES:]
        attribute_pred = attribute_y_hat.argmax(dim=1)

        attribute_accuracy = torch.sum(attribute_y == attribute_pred, dtype=torch.float) / AttributeModel.BATCH_SIZE

        category_x = x[:, :AttributeModel.NUM_CATEGORIES].argmax(dim=1)

        # Log category predictions to TensorBoard
        category_output = ''
        for i in range(x.shape[0]):
            category_output += 'x: {:30} \ny: {:30} \np: {:30}\n\n'.format(
                self.classes[category_x[i]],
                self.classes[category_y[i]],
                self.classes[category_pred[i]]
            )

        self.logger: TestTubeLogger
        self.logger.experiment.add_text('category_output', category_output, global_step=self.global_step)

        return {
            'val_loss': loss,
            'val_category_acc': category_accuracy,
            'val_attribute_acc': attribute_accuracy
        }

    def validation_end(self, outputs):
        def get_mean(k: str) -> torch.Tensor:
            return torch.mean(torch.tensor(
                [o[k] for o in outputs],
                dtype=torch.float
            ))

        val_loss = get_mean('val_loss')
        val_category_acc = get_mean('val_category_acc')
        val_attribute_acc = get_mean('val_attribute_acc')

        log_dict = {
            'val_loss': val_loss,
            'val_category_acc': val_category_acc,
            'val_attribute_acc': val_attribute_acc
        }

        return {
            'val_loss': val_loss,
            'progress_bar': log_dict,
            'log': log_dict
        }

    def configure_optimizers(self):
        return Adam(self.parameters(), lr=1e-3)

    @staticmethod
    def __make_dataloader(data_path: str) -> Tuple[DataLoader, List[str]]:
        data = pd.read_csv(data_path)
        data.drop(columns=['0_image_id', '1_image_id'], inplace=True)

        n_cols = len(data.columns) // 2
        classes: List[str] = data.columns.values[1:n_cols + 1]
        classes = [c[2:] for c in classes]

        data_arr = data.to_numpy()

        x_arr = data_arr[:, 1:n_cols + 1]
        y_arr = data_arr[:, n_cols + 1:]

        x = torch.tensor(x_arr, dtype=torch.float)
        y = torch.tensor(y_arr, dtype=torch.float)

        dataset = TensorDataset(x, y)
        return DataLoader(
            dataset=dataset,
            batch_size=AttributeModel.BATCH_SIZE
        ), classes

    @data_loader
    def train_dataloader(self):
        loader, classes = self.__make_dataloader(AttributeModel.TRAIN_DATA_PATH)
        self.classes = classes
        return loader

    @data_loader
    def val_dataloader(self):
        return self.__make_dataloader(AttributeModel.TEST_DATA_PATH)[0]


if __name__ == '__main__':
    model = AttributeModel()

    trainer = Trainer(min_nb_epochs=100, check_val_every_n_epoch=1)
    trainer.fit(model)
