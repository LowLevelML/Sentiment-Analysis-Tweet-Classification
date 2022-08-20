# -*- coding: utf-8 -*-
"""sentiment_analysis_review_classification.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/13am4hoVSYVOKZFtJCHDGVa3H9-b52z6Z

To run this python jupyter notebook: 
- [open in colab](https://colab.research.google.com/github/LowLevelML/Sentiment-Analysis-Review-Classification/blob/master/ml/main.ipynb)

# Install packages
"""

# Commented out IPython magic to ensure Python compatibility.
# %pip install datasets transformers
# %pip install cloud-tpu-client https://storage.googleapis.com/tpu-pytorch/wheels/colab/torch_xla-1.12-cp37-cp37m-linux_x86_64.whl

"""# Import Data"""

DATASETNAME = "emotion"

from datasets import load_dataset
dataset = load_dataset(DATASETNAME)

import torch
# import torch_xla
# import torch_xla.core.xla_model as xm
if torch.cuda.is_available():
	deviceName = "cuda"
else:
	deviceName = "cpu"

# deviceName = xm.xla_device()

print(deviceName)

device = torch.device(deviceName)

"""# Preprocess Data"""

MODELNAME = "bert-base-uncased" # MODELNAME = "bert-large-uncased"

from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained(MODELNAME)

def tokenize(batch):
    return tokenizer(batch["text"], padding=True, truncation=True)

datasetEncoded = dataset.map(tokenize, batched=True, batch_size=None)

datasetEncoded['train'][0]

from transformers import AutoModelForSequenceClassification, AutoConfig
# define the mappings as dictionaries
label2id = {
    "0": "Sad",
    "1": "Joy",
    "2": "Love",
    "3": "Anger",
    "4": "Fear",
    "5": "Surprise"
}
id2label = {
    "Sad": "0",
    "Joy": "1",
    "Love": "2",
    "Anger": "3",
    "Fear": "4",
    "Surprise": "5"
}
# use auto config so taht you can change model name and it will auto detect
# define config
config = AutoConfig.from_pretrained(MODELNAME, label2id=label2id, id2label=id2label)
# config done
numLabels = 6
model = (AutoModelForSequenceClassification.from_pretrained(MODELNAME, config=config).to(device))

datasetEncoded["train"].features

datasetEncoded.set_format("torch", columns=["input_ids", "attention_mask", "label"])
datasetEncoded["train"].features

"""# Train the model"""

from sklearn.metrics import accuracy_score, f1_score

def compute_metrics(pred):
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)
    f1 = f1_score(labels, preds, average="weighted")
    acc = accuracy_score(labels, preds)
    return {"accuracy": acc, "f1": f1}

from transformers import Trainer, TrainingArguments

batch_size = 64
logging_steps = len(datasetEncoded["train"]) // batch_size
training_args = TrainingArguments(
    output_dir="results",
    num_train_epochs=8,
    learning_rate=2e-5,
    per_device_train_batch_size=batch_size,
    per_device_eval_batch_size=batch_size,
    load_best_model_at_end=True,
    metric_for_best_model="f1",
    weight_decay=0.01,
    evaluation_strategy="epoch",
    save_strategy="epoch",
    disable_tqdm=False
)

from transformers import Trainer

trainer = Trainer(model=model, args=training_args,
                  compute_metrics=compute_metrics,
                  train_dataset=datasetEncoded["train"],
                  eval_dataset=datasetEncoded["validation"])

trainer.train()

results = trainer.evaluate()
results

preds_output = trainer.predict(datasetEncoded["validation"])
preds_output.metrics

"""# Show results in a confusion matrix"""

import numpy as np
import seaborn as sns
from sklearn.metrics import plot_confusion_matrix
from sklearn.metrics import confusion_matrix
from sklearn.metrics import ConfusionMatrixDisplay
from matplotlib import pyplot as plt
def confusion_ma(y_true, y_pred, class_names):
    cm = confusion_matrix(y_true, y_pred, normalize='true')
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=class_names)
    disp.plot(cmap=plt.cm.Blues)
    return plt.show()
yValid = np.array(datasetEncoded["validation"]["label"])
yPreds = np.argmax(preds_output.predictions, axis=1)
labels = ['Sad', 'Joy', 'Love', 'Anger', 'Fear', 'Surprise']
confusion_ma(yValid, yPreds, labels)

"""# Save model to Google Drive or Transformers

I am going to save to google drive, and then push to transformers
"""

# save pytorch model
model.save_pretrained('./model')
# Save
tokenizer.save_pretrained('./model')

!cd /content && zip -r ./model.zip ./model/

from google.colab import drive
drive.mount('/content/drive')

!cd /content && cp -r ./model.zip "./drive/My Drive/colabDownload/"