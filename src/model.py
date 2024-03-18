import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import h5py  # save model

class Linear_QNet(nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super().__init__()
        # Neural network
        self.linear1 = nn.Linear(input_size, hidden_size)
        self.linear2 = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        x = F.relu(self.linear1(x))
        x = self.linear2(x)
        return x

    def save(self):
        h5py.File('src/models/model.hdf5', 'w')


class QTrainer:
    def __init__(self, model, lr, gamma):
        self.lr = lr
        self.gamma = gamma
        self.model = model
        self.optimizer = optim.Adam(model.parameters(), lr=self.lr)
        self.criterion = nn.MSELoss()  # Mean Squarred Error

    def train_step(self, state, action, reward, next_state, done):
        # Convert inputs to PyTorch tensors
        state = torch.tensor(state, dtype=torch.float)
        next_state = torch.tensor(next_state, dtype=torch.float)
        action = torch.tensor(action, dtype=torch.long)
        reward = torch.tensor(reward, dtype=torch.float)
        # (n, x)

        if len(state.shape) == 1:
            # If state is a vector, add a batch dimension
            # torch.unsqueeze(input, dimension)
            state = torch.unsqueeze(state, 0)
            next_state = torch.unsqueeze(next_state, 0)
            action = torch.unsqueeze(action, 0)
            reward = torch.unsqueeze(reward, 0)
            done = (done,)

        # Predicted Q values with current state
        pred = self.model(state)

        # Create a copy of predicted values for target values
        target = pred.clone()
        for i in range(len(done)):
            Q_new = reward[i]
            if not done[i]:
                # Update Q-value using Bellman equation: Q(s,a)=r+γ.max Q(s',a')
                Q_new = reward[i] + self.gamma * torch.max(self.model(next_state[i]))

            # Update the target Q-value for the action taken
            target[i][torch.argmax(action[i]).item()] = Q_new

        # Zero gradients, perform a backward pass, and update the weights
        self.optimizer.zero_grad()
        # Calculate the loss between predicted Q-values and target Q-values
        loss = self.criterion(target, pred)
        loss.backward()

        self.optimizer.step()
