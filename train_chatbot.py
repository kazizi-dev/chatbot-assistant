"""
Reads the natural language data, and puts it in a training set.
Then, it uses Keras sequential neural network to create a model.
"""

import nltk
nltk.download('punkt')
nltk.download('wordnet')
from nltk.stem import WordNetLemmatizer
lemmatizer = WordNetLemmatizer()
import json
import pickle

import numpy as np
from keras.models import Sequential
from keras.layers import Dense, Activation, Dropout
from keras.optimizers import SGD
import random

def perform_ETL(intents):
    """
    Extract the data from intents, and then 
    transform by performing lemmatisation on
    the words in the data.
    """

    words=[]            # list of words
    tags = []           # list of tags
    documents = []      # an array of tuples
    ignore_words = ['?', '!']

    # extract data from intents
    for intent in intents['intents']:
        for question in intent['questions']:
            words_list = nltk.word_tokenize(question)
            words.extend(words_list)

            documents.append((words_list, intent['tag']))

            if intent['tag'] not in tags:
                tags.append(intent['tag'])

    # lemmatize the words
    temp = []
    for w in words:
        if w not in ignore_words:
            temp.append(lemmatizer.lemmatize(w.lower()))    # create the base words

    words = sorted(list(set(temp)))
    tags = sorted(list(set(tags)))

    return documents, tags, words


def get_training_data(documents, tags, words):
    """
    Build and return the training data from 
    document data.
    """

    training_data = []       # training data
    list_of_zeros = [0 for _ in range(len(tags))]    # an array of empty 0's

    for doc in documents:
        bag = []                # a bag of 0 or 1 representing boolean
        pattern_words = doc[0]  # get the list of pattern words

        temp = []
        for word in pattern_words:
            temp.append(lemmatizer.lemmatize(word.lower()))     # create the base words
        pattern_words = temp

        for word in words:
            if word in pattern_words:
                bag.append(1)       # the words with matching patterns
            else:
                bag.append(0)
    
        output_row = list(list_of_zeros)
        output_row[tags.index(doc[1])] = 1
        training_data.append([bag, output_row])

    random.shuffle(training_data)
    return training_data


def create_neural_network_model(x_train, y_train):
    """
    Creates a 3 layer neural network model using the
    sequential model in keras. The model is trained 
    with stochastic gradient descent.
    """ 

    # create a model with 3 layers, 128, 64, and # of intents
    model = Sequential()
    model.add(Dense(128, input_shape=(len(x_train[0]), ), activation='relu'))
    model.add(Dropout(0.5))
    model.add(Dense(64, activation='relu'))
    model.add(Dropout(0.5))
    model.add(Dense(len(y_train[0]), activation='softmax'))
    
    # train model with with stochastic gradient descent and then compile it
    sgd = SGD(lr=0.01, decay=1e-6, momentum=0.9, nesterov=True)
    model.compile(loss='categorical_crossentropy', optimizer=sgd, metrics=['accuracy'])

    # fitting and saving the model
    model.save('./results/chatbot_model.h5', model.fit(np.array(x_train), 
                                            np.array(y_train), 
                                            epochs=200, 
                                            batch_size=5, 
                                            verbose=1))


if __name__ == "__main__":
    data_file = open('./data/intents.json', encoding='utf-8').read()
    intents = json.loads(data_file)

    documents, tags, words = perform_ETL(intents)

    # print the information after ETL
    print (len(documents), "documents")
    print (len(tags), "classe(s)", tags)
    print (len(words), "unique lemmatized words")

    # save the data as pickle files
    pickle.dump(words,open('./results/words.pkl','wb'))
    pickle.dump(tags,open('./results/classes.pkl','wb'))

    # get x and y training data for the model
    x_train = []
    y_train = []
    for train in get_training_data(documents, tags, words):
        x_train.append(train[0])
        y_train.append(train[1])

    create_neural_network_model(x_train, y_train)