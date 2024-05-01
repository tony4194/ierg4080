from transformers import pipeline

class SpamEmailClassifier:
    def __init__(self):
        self.pipe = pipeline("text-classification", model="tony4194/distilbert-spamEmail")

    def classify(self, email_body):
        result = self.pipe(email_body)
        label = result[0]['label']
        probability = result[0]['score']
        return label, probability