import torch
import torch.nn as nn


class RegressionHead(nn.Module):
    def __init__(
        self, input_dim, hidden_dim, dropout_prob=0.1, activation_fn=torch.sigmoid
    ):
        super().__init__()
        self.activation_fn = activation_fn
        self.dense_block = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.GELU(),
            nn.LayerNorm(hidden_dim),
            nn.Dropout(dropout_prob),
            nn.Linear(hidden_dim, 1),
        )
        self.pool = nn.AdaptiveAvgPool1d(1)  # Avarages information among tokens

        for module in self.dense_block:
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    module.bias.data.zero_()

    def forward(self, x):
        """
        Input: [batch_size, seq_len, input_dim]
        Output: [batch_size, 1]
        """
        x = self.dense_block(x)  # [batch, seq_len, 1]

        x = x.transpose(1, 2)  # [batch, 1, seq_len]
        x = self.pool(x)  # [batch, 1, 1]
        x = x.squeeze(-1)  # [batch, 1]
        return self.activation_fn(x)
