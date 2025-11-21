from sklearn.metrics import accuracy_score
from sklearn.tree import DecisionTreeClassifier
import pandas as pd  
import numpy as np  
from sklearn.linear_model import LogisticRegression


from sklearn import datasets
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import train_test_split

iris = pd.read_csv('./fd_change-83.csv',
                   usecols=['Ad Supported', 'Fraud',	'In App Purchases',	'Rating', 'review'])
group1 = ['Ad Supported']
group2 = ['In App Purchases', 'Rating', 'review']
group3 = ['Fraud']
new_col = group1+group2+group3
df2 = iris[new_col]
df2.dropna(inplace=True)
variety_mappings = {0: 'Safe', 1: 'Fraud'}
X = df2.iloc[:, 0:-1]  

y = df2.iloc[:, -1] 

X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=0)

dtree_model = DecisionTreeClassifier(max_depth=2).fit(X_train, y_train)
dtree_predictions = dtree_model.predict(X_test)

cm = confusion_matrix(y_test, dtree_predictions)

print("Accuracy : ", accuracy_score(y_test, dtree_predictions))


def classify(a, b, c, d):
    arr = np.array([a, b, c, d])  
    arr = arr.astype(np.float64)  
    query = arr.reshape(1, -1)  
    prediction = variety_mappings[dtree_model.predict(
        query)[0]] 
    return prediction

