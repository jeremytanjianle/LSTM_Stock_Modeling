"""

referenced source: https://towardsdatascience.com/linear-regression-with-pytorch-eb6dedead817
"""
import torch
from torch.autograd import Variable
from src.CustomLoss import *
from src.Handler import *

class Linear(torch.nn.Module):
    """
    The simplest example, a linear classifier.
    """

    def __init__(self, input_size, output_size):
        """
        Default consructor for the Linear classifier
        :param input_size: the input shape to intantiate the model with
        :param the output shape for the model
        :param epochs: the number of iterations to pass over the training data
        """
        super(Linear, self).__init__()
        self.linear = torch.nn.Linear(input_size, output_size)

    def forward(self, x):
        out = self.linear(x)
        return out


class LinearHandler(Handler):
    def __init__(self, epochs, loss_method, regularization_method, learning_rate, batch_size):
        super(LinearHandler, self).__init__(epochs, loss_method, regularization_method, learning_rate, batch_size)

    def create_model(self, input_shape, output_shape):
        self.model = Linear(input_shape, output_shape)

    def train(self, x, y):
        if self.loss_method == "MSE":
            criterion = torch.nn.MSELoss()
        elif self.loss_method == "Custom_Sharpe":
            criterion = MyCustomLoss(method="sharpe")
        else:
            print("Loss method not recognized, defaulting to MSE")
            criterion = torch.nn.MSELoss()
        optimizer = torch.optim.Adam(self.model.parameters(), self.learning_rate)
        # inputs = Variable(torch.from_numpy(x))
        # labels = Variable(torch.from_numpy(y))
        avg_losses = []
        for epoch in range(self.epochs):
            total_loss = 0
            for i in range(0, x.shape[0], self.batch_size):
                inputs = Variable(torch.from_numpy(x[i:i+self.batch_size]))
                labels = Variable(torch.from_numpy(y[i:i+self.batch_size]))
                outputs = self.model(inputs)
                loss = criterion(outputs, labels)
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                total_loss += loss.item()
            avg_losses.append(total_loss / x.size)
            print('epoch {}:\t loss {}'.format(epoch, total_loss / x.size))
        return avg_losses

    def test(self, x, y):
        if self.loss_method == "MSE":
            criterion = torch.nn.MSELoss()
        elif self.loss_method == "Custom_Sharpe":
            criterion = MyCustomLoss("sharpe_loss")
        else:
            print("Loss method not recognized, defaulting to MSE")
            criterion = torch.nn.MSELoss()
        inputs = Variable(torch.from_numpy(x))
        labels = Variable(torch.from_numpy(y))
        outputs = self.model(inputs)
        loss = criterion(outputs, labels)
        return loss, outputs
