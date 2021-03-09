import data.GetDataset as gd
from src import *
import torch
import numpy as np
import matplotlib.pyplot as plt


def model_trading(actual, preds, lookahead):
    # not every sample is the same size, pad the front with 0s and we'll assume that the stock hadn't existed yet at
    # the beginning of trading
    max_size = 0
    for elem in preds:
        max_size = max(elem.shape[0], max_size)
    # add one additional row to simulate no action
    true_labels = np.zeros((actual.shape[0]+1, max_size))
    true_predictions = np.zeros((actual.shape[0]+1, max_size))
    for i in range(actual.shape[0]):
        current_size = actual[i].shape[0]
        true_labels[i,max_size-current_size:] = np.squeeze(actual[i])
        true_predictions[i, max_size-current_size:] = np.squeeze(preds[i])
    trading_quantity = 1
    trading_route = [1]
    # choose the stocks with the best predictions for each day by getting the index of the highest value of each row
    best_choices = np.argmax(true_predictions, axis=0)
    # for every day in trading
    day = 0
    while day < best_choices.shape[0] and trading_quantity > 0:
        if true_predictions[best_choices[day], day] == 0:
            day += 1
        else:
            returns = true_labels[best_choices[day], day] if true_labels[best_choices[day], day] > -1 else -1
            trading_quantity += trading_quantity*returns
            day += lookahead
        trading_route.append(trading_quantity)
    return np.array(trading_route)


if __name__ == '__main__':
    blocks = ['LSTM', 'linear', 'MLP']
    method = 'by_category'
    if method == 'aggregated':
        if 'linear' in blocks or 'MLP' in blocks:
            train_features, train_targets, test_features, test_targets = gd.get_aggregated_dataset("commodities", 5, 7, 0.9)
        if 'linear' in blocks:
            batch_size = 256
            print('----- Linear -----')
            linear = LinearHandler(100, "MSE", None, 0.01, batch_size)
            linear.create_model(train_features.shape[1], 1)
            linear_losses = linear.train(train_features, train_targets)
            plt.figure(0)
            plt.title("Linear Loss")
            plt.ylabel("loss")
            plt.yscale('log')
            plt.xlabel("epoch")
            plt.plot(linear_losses)
            plt.show()
            linear_MSE, predictions = linear.test(test_features, test_targets)

        if 'MLP' in blocks:
            print('\n\n\n----- MLP -----')
            mlp = MLPHandler(100, "MSE", None, 0.01, batch_size)
            mlp.create_model(train_features.shape[1], 15, 1)
            mlp_losses = mlp.train(train_features, np.squeeze(train_targets))
            plt.figure(0)
            plt.title("MLP Loss")
            plt.ylabel("loss")
            plt.yscale('log')
            plt.xlabel("epoch")
            plt.plot(mlp_losses)
            plt.show()
            MLP_MSE, predictions = mlp.test(test_features, np.squeeze(test_targets))

        if 'LSTM' in blocks:
            train_features, train_targets, test_features, test_targets = gd.get_normal_dataset("commodities", 0.9, 7, normalize=True)
            print('\n\n\n----- LSTM -----')
            lstm = LSTMHandler(100, "return", None, 0.01, 0)
            lstm.create_model(train_features.shape[1], 15, 1, 1)
            lstm_losses = lstm.train(train_features, train_targets)
            plt.figure(0)
            plt.title("lstm Loss")
            plt.ylabel("loss")
            plt.yscale('log')
            plt.xlabel("epoch")
            plt.plot(lstm_losses)
            plt.show()
            lstm.test(test_features, test_targets)
    elif method == 'by_category':
        if 'linear' in blocks or 'MLP' in blocks:
            batch_size = 256
            train_features, train_targets, test_features, test_targets = gd.get_dataset_by_category("commodities", 0.9, aggregate_days=5, target_lookahead=2)
            train_features = np.concatenate(train_features).astype(np.float32)
            train_targets = np.concatenate(train_targets).astype(np.float32)
        if 'linear' in blocks:
            print('----- Linear -----')
            linear = LinearHandler(100, "MSE", None, 0.01, batch_size)
            linear.create_model(train_features.shape[1], 1)
            linear_losses = linear.train(train_features, train_targets)
            _predictions = []
            for i in range(test_features.shape[0]):
                _, pred = linear.test(test_features[i].astype(np.float32), test_targets[i].astype(np.float32))
                _predictions.append(pred.detach().numpy())
            linear_performance = model_trading(test_targets, _predictions, lookahead=2)

        if 'MLP' in blocks:
            print('\n\n\n----- MLP -----')
            mlp = MLPHandler(100, "MSE", None, 0.01, batch_size)
            mlp.create_model(train_features.shape[1], 15, 1)
            mlp_losses = mlp.train(train_features, np.squeeze(train_targets))
            _predictions = []
            for i in range(test_features.shape[0]):
                _, pred = mlp.test(test_features[i].astype(np.float32), np.squeeze(test_targets[i].astype(np.float32)))
                _predictions.append(pred.detach().numpy())
            mlp_performance = model_trading(test_targets, _predictions, lookahead=2)

        if 'LSTM' in blocks:
            _predictions = []
            train_features, train_targets, test_features, test_targets = gd.get_dataset_by_category("commodities", 0.9,
                                                                                                    aggregate_days=1,
                                                                                                    target_lookahead=2)
            # aggregate the training set together, no need to differentiate between the different sets during training
            print('\n\n\n----- LSTM -----')
            batch_size = 256
            lstm = LSTMHandler(100, "MSE", None, 0.01, batch_size)
            lstm.create_model(train_features[0].shape[1], 15, 1, 1)
            lstm_losses = lstm.train(train_features, train_targets)
            for i in range(test_features.shape[0]):
                _, pred = lstm.test(test_features[i].astype(np.float32), test_targets[i].astype(np.float32))
                _predictions.append(pred.detach().numpy())
            lstm_performance = model_trading(test_targets, _predictions, lookahead=2)
            best_possible_performance = model_trading(test_targets, test_targets, lookahead=2)
        max_size = max(lstm_performance.shape[0], linear_performance.shape[0], mlp_performance.shape[0])
        lstm_key = np.linspace(0, lstm_performance.shape[0], max_size)
        # lstm_performance = np.interp(lstm_performance, lstm_key)
        lstm_performance = np.interp(lstm_key, np.arange(lstm_performance.shape[0]), lstm_performance)
        linear_key = np.linspace(0, linear_performance.shape[0], max_size)
        linear_performance = np.interp(linear_key, np.arange(linear_performance.shape[0]), linear_performance)
        mlp_key = np.linspace(0, mlp_performance.shape[0], max_size)
        mlp_performance = np.interp(mlp_key, np.arange(mlp_performance.shape[0]), mlp_performance)

        plt.plot(lstm_performance, c='r', label='LSTM')
        plt.plot(linear_performance, c='b', label='Linear')
        plt.plot(mlp_performance, c='g', label='MLP')
        plt.legend()
        plt.xlabel('Time')
        plt.ylabel('Growth Ratio')
        plt.title('Cumulative Returns - Sharpe Loss')
        plt.show()
