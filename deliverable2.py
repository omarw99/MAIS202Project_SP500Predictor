# -*- coding: utf-8 -*-
"""Deliverable2.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1lhh-YNF4ziR9FSiRRccA7JrC2XXRuFGp
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import csv
import random
import string
import re

from sklearn import svm
from sklearn.svm import LinearSVC
from sklearn import metrics
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.decomposition import PCA
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer

from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
from keras.utils import to_categorical

from gensim.models.fasttext import FastText

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import sent_tokenize
from nltk import WordPunctTokenizer

nltk.download('punkt')
nltk.download('wordnet')
nltk.download('stopwords')
en_stop = set(nltk.corpus.stopwords.words('english'))

articles_datapath = "https://raw.githubusercontent.com/omarw99/MAIS202Project_SP500Predictor/master/Dataset/Combined_News_DJIA.csv"
articles_df = pd.read_csv(articles_datapath).drop(columns = ["Label"])

stockReturn_datapath = "https://raw.githubusercontent.com/omarw99/MAIS202Project_SP500Predictor/master/Dataset/SP500.csv"
stockReturn_df = pd.read_csv(stockReturn_datapath).drop(columns = ["High", "Low", "Close", "Volume"])
#Add column with daily return calculated using adjusted closing and opening prices
stockReturn_df["Daily Return"] = ((stockReturn_df["Adj Close"] - stockReturn_df["Open"]) / stockReturn_df["Open"])*100

combined_df = articles_df.merge(stockReturn_df).drop(columns = ["Open", "Adj Close"])

#Drop any row that has missing data
combined_df = combined_df.dropna()
#Reset index
combined_df = combined_df.reset_index(drop=True)
print(combined_df)

df = pd.DataFrame(columns= ['Headline', 'Daily Return'])

for i in range(len(combined_df)):
  for j in range(1, 26):
    df = df.append({'Headline' : combined_df.iat[i, j] , 'Daily Return' : combined_df.iat[i, 26]} , ignore_index=True)

combined_df = df
print(combined_df)

#Split combined_df into train and test sets
train, test = train_test_split(combined_df, test_size=0.2)

#Reset the indices of the train and test sets
train.reset_index(inplace=True, drop=True)
test.reset_index(inplace=True, drop=True)

print(train)
print(test)

#A function that will clean up, remove all stopwords, and tokenize a string headline
stemmer = WordNetLemmatizer()
stop = stopwords.words('english')

def cleanHeadline(headline):
  #Remove all the special characters
  headline = re.sub(r'\W', ' ', str(headline))

  #Remove all single characters
  headline = re.sub(r'\s+[a-zA-Z]\s+', ' ', headline)

  #Remove single characters from the start
  headline = re.sub(r'\^[a-zA-Z]\s+', ' ', headline)

  #Substituting multiple spaces with single space
  headline = re.sub(r'\s+', ' ', headline, flags=re.I)

  #Removing prefixed 'b'
  headline = re.sub(r'^b\s+', '', headline)

  #Converting to Lowercase
  headline = headline.lower()

  #Remove all punctuation and numbers
  headline = headline.translate(str.maketrans('','',string.punctuation)).translate(str.maketrans('','','1234567890'))

  #Remove stopwords
  headline_words = headline.split()
  headline = " ".join([word for word in headline_words if word not in stop])

  #Lemmatization
  tokens = headline.split()
  tokens = [stemmer.lemmatize(word) for word in tokens]
  tokens = [word for word in tokens if word not in en_stop]
  tokens = [word for word in tokens if len(word) > 2]

  cleanString = ' '.join(tokens)

  return cleanString

#Call cleanHeadline on all the headlines in the training set
for i in range(len(train)):
    train.iat[i, 0] = cleanHeadline(train.iat[i, 0])

print(train)

#Function that creates a series that has all the words from the day's headlines in a list
def tokenizeWordsSeries(df):
  arrayOfDailyHeadlineWords = []
  for i in range(len(df)):
    vector = df.iat[i,0].split()
    arrayOfDailyHeadlineWords.append(vector)
  series = pd.Series(arrayOfDailyHeadlineWords)
  return series
  
train_words = tokenizeWordsSeries(train)

#Create a series of all the words in the train set headlines
all_words = [word for i in train_words for word in i]

#Sort all_words and save as a list, get rid of the duplicates to find vocabulary
vocab = sorted(list(set(all_words)))

print("%s words total, with a vocabulary size of %s" % (len(all_words), len(vocab)))

"""DONE WITH DATA PROCESSING AT THIS POINT - 
START VECTORIZING
"""

#Create a corpus list of all the headline strings from the train dataset
list_corpus = train["Headline"].tolist()
#Create a list of the daily returns
list_labels = train["Daily Return"].tolist()

#Vectorize all the headlines using CountVectorizer() based on list_corpus
vectorizer = CountVectorizer()
X = vectorizer.fit_transform(list_corpus)
vocabulary = vectorizer.get_feature_names()

X_train = X.toarray()
y_train = np.asarray(list_labels)

print(X_train.shape)
print(y_train.shape)

#Create a function that vectorizes a single headline string based on the vocabulary list
def preprocess_sample_point(headline, vocab):
  #Create a vector of the same length as vocab and initialize with all zeroes
  vector = np.zeros((len(vocab),), dtype = int)
  #Clean up headline
  headline = cleanHeadline(headline)
  #Split headline by its words into a list
  wordsInHeadline = headline.split()

  #A double for loop that will check each word in some_string and put a 1 in vector if that word exists in vocab
  #The 1 will get put in the same index as where that word was in vocab
  for i in wordsInHeadline:
    for j in range(len(vocab)):
      if vocab[j] == i:
        vector[j] += 1
  
  return vector

print(X_train[0:5])
print(" ")

for i in range(5):
  print(sum(X_train[i]))

print(y_train[0:5])

"""DONE WITH SPLITTING UP THE DATA - START TESTING DIFFERENT MODELS

CNN
"""

#DEEP NEURAL NETWORK
from keras.callbacks import ModelCheckpoint
from keras.models import Sequential
from keras.layers import Dense, Activation, Flatten
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error 
from matplotlib import pyplot as plt
import seaborn as sb
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import warnings 
warnings.filterwarnings('ignore')
warnings.filterwarnings('ignore', category=DeprecationWarning)
from xgboost import XGBRegressor

NN_model = Sequential()

# The Input Layer :
NN_model.add(Dense(128, kernel_initializer='normal',input_dim = train.shape[1], activation='relu'))

# The Hidden Layers :
NN_model.add(Dense(256, kernel_initializer='normal',activation='relu'))
NN_model.add(Dense(256, kernel_initializer='normal',activation='relu'))
NN_model.add(Dense(256, kernel_initializer='normal',activation='relu'))

# The Output Layer :
NN_model.add(Dense(1, kernel_initializer='normal',activation='linear'))

# Compile the network :
NN_model.compile(loss='mean_absolute_error', optimizer='adam', metrics=['mean_absolute_error'])
NN_model.summary()

checkpoint_name = 'Weights-{epoch:03d}--{val_loss:.5f}.hdf5' 
checkpoint = ModelCheckpoint(checkpoint_name, monitor='val_loss', verbose = 1, save_best_only = True, mode ='auto')
callbacks_list = [checkpoint]

NN_model.fit(X_train, train['Daily Return'], epochs=500, batch_size=32, validation_split = 0.2, callbacks=callbacks_list)

"""Linear Regression"""

#LINEAR REGRESSION ATTEMPT
from sklearn.linear_model import LinearRegression

regressor = LinearRegression()  
regressor.fit(X_train, y_train)

y_pred = regressor.predict(X_test)

plt.scatter(y_train, y_train_predict)
plt.show()

#Find the MSE of the training set
mse_train = np.mean(np.square(np.subtract(y_train, y_train_predict)))
print("Training set Mean Squared Error: {}".format(mse_train))

y_test = np.asarray(test["Daily Return"].tolist())

vectorizedXTest = []
for i in range(len(test)):
  temp = preprocess_sample_point(test.iat[i,0], vocabulary)
  vectorizedXTest.append(temp)

X_test = np.array(vectorizedXTest)

#Use .predict() to create the y_test_predict array
y_test_predict = regr.predict(X_test)

plt.scatter(y_test, y_test_predict)
plt.show()

#Find the MSE of the testing set
mse_test = np.mean(np.square(np.subtract(y_test, y_test_predict)))
print("Testing set Mean Squared Error: {}".format(mse_test))

#Test model on a single news headline
vector = preprocess_sample_point('Russia declares war on the United States', vocabulary)
print(sum(vector))
vector = vector.reshape(1, -1)
print(regr.predict(vector))

vector1 = preprocess_sample_point('The stock market is booming', vocabulary)
print(sum(vector1))
vector1 = vector.reshape(1, -1)
print(regr.predict(vector1))

"""Random Forest Regressor"""

#Call the RandomForestRegressor model and fit using X_train and y_train
regr = RandomForestRegressor(max_depth = 10, random_state = 0)
regr.fit(X_train, y_train)

#Use .predict() to create the y_train_predict array
y_train_predict = regr.predict(X_train)

plt.scatter(y_train, y_train_predict)
plt.show()

#Find the MSE of the training set
mse_train = np.mean(np.square(np.subtract(y_train, y_train_predict)))
print("Training set Mean Squared Error: {}".format(mse_train))

y_test = np.asarray(test["Daily Return"].tolist())

vectorizedXTest = []
for i in range(len(test)):
  temp = preprocess_sample_point(test.iat[i,0], vocabulary)
  vectorizedXTest.append(temp)

X_test = np.array(vectorizedXTest)

print(X_test[0:5])
print(" ")

for i in range(5):
  print(sum(X_test[i]))

print(y_test[0:5])

#Use .predict() to create the y_test_predict array
y_test_predict = regr.predict(X_test)

print(y_test_predict[0:5])

plt.scatter(y_test, y_test_predict)
plt.show()

#Find the MSE of the testing set
mse_test = np.mean(np.square(np.subtract(y_test, y_test_predict)))
print("Testing set Mean Squared Error: {}".format(mse_test))

#Test model on a single news headline
vector = preprocess_sample_point('Russia declares war on the United States', vocabulary)
print(sum(vector))
vector = vector.reshape(1, -1)
print(regr.predict(vector))

vector1 = preprocess_sample_point('The stock market is booming', vocabulary)
print(sum(vector1))
vector1 = vector.reshape(1, -1)
print(regr.predict(vector1))

"""SVM"""

#Scale the X_train and X_test matrices so the SVR model works best
scaler = StandardScaler()
scaler.fit(X_train)  # Don't cheat - fit only on training data
X_train = scaler.transform(X_train)
X_test = scaler.transform(X_test)  # apply same transformation to test data

#Call the SVR model and fit using X_train and y_train
clf = svm.SVR()
clf.fit(X_train, y_train)

#Use .predict() to create the y_train_predict and y_test_predict arrays
y_train_predict = clf.predict(X_train)
y_test_predict = clf.predict(X_test)

print(clf.score(X_train, y_train))
print(clf.score(X_test, y_test))

#Find the MSE of the training and testing sets
mse_train = np.mean(np.square(np.subtract(y_train, y_train_predict)))
print("Training set Mean Squared Error: {}".format(mse_train))

mse_test = np.mean(np.square(np.subtract(y_test, y_test_predict)))
print("Testing set Mean Squared Error: {}".format(mse_test))

#Test model on a single news headline
vector = preprocess_sample_point('Russia declares war on the United States', vocabulary)
print(sum(vector))
vector = vector.reshape(1, -1)
print(clf.predict(vector))

vector1 = preprocess_sample_point('The stock market is booming', vocabulary)
print(sum(vector1))
vector1 = vector.reshape(1, -1)
print(clf.predict(vector1))