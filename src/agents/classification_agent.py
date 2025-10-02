import nltk
from nltk.corpus import stopwords

class ClassificationAgent:
    def __init__(self):
        nltk.download('punkt')
        nltk.download('averaged_perceptron_tagger')
        nltk.download('stopwords')
        self.stop_words = set(stopwords.words('english'))
    