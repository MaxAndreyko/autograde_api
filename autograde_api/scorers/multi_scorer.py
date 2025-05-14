from typing import Callable, List, Union, Tuple
import torch
from transformers import BertTokenizer
from src.models.bert import MultiHeadBERT


class MultiHeadRegressorInferer:
    def __init__(
        self,
        model: Union[MultiHeadBERT],
        tokenizer: Union[BertTokenizer],
        max_target: float,
        min_target: float,
        scale_predictions: bool = True,
        padding: bool = True,
        truncation: str = "max_length",
        max_length: int = 512,
    ):
        self.model = model
        self.tokenizer = tokenizer
        self.scale_predictions = scale_predictions
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.max_target = max_target
        self.min_target = min_target
        self.padding = padding
        self.truncation = truncation
        self.max_length = max_length
        self.model.to(self.device)

        print(f"Using device: {self.device}")

    def tokenize_function(self, queries, texts) -> Tuple[torch.tensor, torch.tensor]:

        tokenized = self.tokenizer(
            queries,
            texts,
            padding=self.padding,
            truncation=self.truncation,
            max_length=self.max_length,
        )
        input_ids = tokenized.get("input_ids")
        attention_masks = tokenized.get("attention_mask")

        input_ids = torch.tensor(input_ids)
        attention_masks = torch.tensor(attention_masks)

        return input_ids, attention_masks
    
    def predict(
        self,
        queries: Union[str, List[str]],
        texts: Union[str, List[str]],
        post_process_func: Callable = None,
    ) -> torch.Tensor:
        """
        Predict scores for a given text or array of strings.

        Args:
            texts (Union[str, List[str]]): Input text or list of strings to predict scores for.

        Returns:
            torch.Tensor: Predicted scores as a tensor.
        """
        # Ensure the model is in evaluation mode
        self.model.eval()

        # If a single string is provided, convert it to a list
        if isinstance(queries, str):
            queries = [queries]
        if isinstance(texts, str):
            texts = [texts]

        # Preprocess the input text using the tokenizer from the model
        input_ids, attn_masks = self.tokenize_function(queries, texts)

        # Move inputs to the appropriate device
        input_ids = input_ids.to(self.device)
        attention_mask = attn_masks.to(self.device)

        # Make predictions
        with torch.no_grad():
            logits = self.model(input_ids, attention_mask)

        # Scale the output if necessary
        predictions = self.scale_output(logits, post_process_func).squeeze().cpu().int().tolist()
        return predictions

    def scale_output(
        self, predictions: torch.tensor, post_process_func: Callable = None
    ) -> torch.tensor:
        """Scales model predictions to the same scale as train targets

        Parameters
        ----------
        predictions : torch.tensor
            Model predictions in [0, 1] scale

        Returns
        -------
        torch.tensor
            Scaled model predictions in [min_target, max_target] scale
        """
        if (
            self.scale_predictions
            and self.max_target is not None
            and self.min_target is not None
        ):
            scaled_output = (
                self.min_target + (self.max_target - self.min_target) * predictions
            )
            if post_process_func is not None:
                return post_process_func(scaled_output)
            else:
                return scaled_output
        else:
            if post_process_func is not None:
                return post_process_func(predictions)
            else:
                return predictions

    def load_weights(self, weights_path: str) -> None:
        # with torch.serialization.safe_globals([MultiHeadBERT]):
        self.model = torch.load(
            weights_path, map_location=self.device, weights_only=False
        )
        print("Weights loaded successfully!")