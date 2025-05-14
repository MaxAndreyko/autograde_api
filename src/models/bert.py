import torch
import torch.nn as nn
from transformers import BertModel

from .modules import RegressionHead


class MultiHeadBERT(nn.Module):
    """
    Multi-head BERT for regression task with layer-wise freezing
    """

    def __init__(
        self,
        freeze_bert: bool = False,
        freeze_layers: int = 0,
        dim_in: int = 768,
        head_hidden_dim: int = 256,
        dim_out: int = 1,
        p_dropout: float = 0.1,
        model_name: str = "bert-base-uncased",
    ):
        super().__init__()
        self.bert = BertModel.from_pretrained(model_name)
        self.model_name = model_name

        self.heads = nn.ModuleList(
            [RegressionHead(dim_in, head_hidden_dim, p_dropout) for _ in range(dim_out)]
        )

        if freeze_bert:

            # Freeze specified initial layers
            for i, layer in enumerate(self.bert.encoder.layer):
                freeze_layer = i < freeze_layers
                for param in layer.parameters():
                    param.requires_grad = not freeze_layer

            # Freeze embeddings if freezing any layers
            if freeze_layers > 0:
                for param in self.bert.embeddings.parameters():
                    param.requires_grad = False

            # Ensure pooler remains trainable
            for param in self.bert.pooler.parameters():
                param.requires_grad = True

    def forward(self, input_ids, attention_mask):
        """
        Feed input to BERT and the classifier to compute logits.
        @param    input_ids (torch.Tensor): an input tensor with shape (batch_size,
                        max_length)
        @param    attention_mask (torch.Tensor): a tensor that hold attention mask
                        information with shape (batch_size, max_length)
        @return   logits (torch.Tensor): an output tensor with shape (batch_size,
                        num_labels)
        """

        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        last_hidden_state = (
            outputs.last_hidden_state
        )  # -> torch.Size([batch, seq_len, 768])
        predictions = [head(last_hidden_state) for head in self.heads]
        output = torch.cat(predictions, dim=1)

        return output
