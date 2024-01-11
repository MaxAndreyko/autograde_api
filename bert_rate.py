import pandas as pd
from datasets import Dataset
from transformers import AutoTokenizer, AutoConfig, AutoModelForSequenceClassification
from transformers import DataCollatorWithPadding
from transformers import TrainingArguments, Trainer


class LetterScoreRegressor:
    def __init__(self,
                 model_dir: str,
                 question_col: str,
                 answer_col: str,
                 config_file: str
                ):
        """Initializes K2-criterion regression model from saved weights

        Parameters
        ----------
        model_dir : str
            Directory where required model files located
        question_col : str
            Name (key) of question column
        answer_col : str
            Name (key) of answer column
        config_file : str
            Name of model configuration file inside `model_dir` folder
        """

        # Define input columns and target column
        self.question_col = question_col
        self.answer_col = answer_col
        self.inputs = [question_col, answer_col]
        self.input_col = "input"
        self.text_cols = [self.input_col]

        # Initialize model-related attributes
        self.model_dir = model_dir

        # Initialize tokenizer and model configuration
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
        self.model_config = AutoConfig.from_pretrained(f"{model_dir}/{config_file}")

        # Initialize data collator for padding
        self.data_collator = DataCollatorWithPadding(
            tokenizer=self.tokenizer
        )

        # Load the trained content score prediction model
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_dir)
        self.model.eval()

        # Define model prediction arguments
        test_args = TrainingArguments(
            output_dir=self.model_dir,
            do_train=False,
            do_predict=True,
            per_device_eval_batch_size=4,
            dataloader_drop_last=False,
        )

        # Initialize a trainer for inference
        self.infer = Trainer(
                      model=self.model ,
                      tokenizer=self.tokenizer,
                      data_collator=self.data_collator,
                      args=test_args)

    def tokenize_function_infer(self, examples: pd.DataFrame):
        """Tokenizes input text

        Parameters
        ----------
        examples : pd.DataFrame
            Input dataframe with text input column
        """
        tokenized = self.tokenizer(examples[self.input_col])
        return tokenized

    def predict(self,
                test_df: pd.DataFrame,
               ) -> int:
        """Predicts letter score for input data

        Parameters
        ----------
        test_df : pd.DataFrame
            Input dataframe for prediction

        Returns
        -------
        int
            K2-criterion score prediction
        """
        sep = self.tokenizer.sep_token

        # Create input text for test data
        in_text = (
                    test_df[self.question_col] + sep
                    + test_df[self.answer_col]
                  )
        test_df[self.input_col] = in_text

        # Select the relevant columns
        test_ = test_df[[self.input_col]]

        # Create a dataset from the test data
        test_dataset = Dataset.from_pandas(test_, preserve_index=False)
        test_tokenized_dataset = test_dataset.map(self.tokenize_function_infer, batched=False)

        # Perform predictions
        pred = round(self.infer.predict(test_tokenized_dataset)[0][0][0])

        return pred
    