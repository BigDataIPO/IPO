from sklearn.metrics import *
import copy
import pandas as pd
import numpy as np

def Result(clf = None, X_train = None, X_test = None, y_train = None, y_test = None):
    # 반복문을 돌면서 모형이 지속적으로 fit되는 것을 방지하기 위해서 model의 deepcopy(?)가 필요함
    # 마찬가지로 하이퍼 파라미터를 맞춘 clf를 밖에서 선언하고 가져와야함
    clf = RandomForestClassifier() # clf = copy.deepcopy(clf)
    
    clf.fit(X_train , y_train)
    train_pred = clf.predict(X_train)
    test_pred = clf.predict(X_test)
    
    # 성과 평가
    train_res = clf_eval(y_train, train_pred)
    test_res = clf_eval(y_test,test_pred)
    res = train_res + test_res
    
    #feature_importance
    feature_importance = clf.feature_importances_
    
    D = {"Score":res, "Feature":feature_importance, "y_pred":test_pred}
    return D


def get_clf_eval(y_test, pred=None, pred_proba=None): 
    confusion = confusion_matrix(y_test, pred) 
    accuracy = accuracy_score(y_test, pred) 
    precision = precision_score(y_test, pred , average= 'weighted') 
    recall = recall_score(y_test, pred , average= 'weighted') 
    f1 = f1_score(y_test, pred , average= 'weighted') 
    
    print('정확도(accuracy): {0:.4f}, 정밀도(precision): {1:.4f}, 재현율(recall): {2:.4f}, f1_score: {3:.4f}'.format(accuracy, precision, recall, f1))
    
    confusion = confusion_matrix(y_test, pred) 
    accuracy = accuracy_score(y_test, pred) 
    precision = precision_score(y_test, pred , average= 'macro') 
    recall = recall_score(y_test, pred , average= 'macro') 
    f1 = f1_score(y_test, pred , average= 'macro') 
    
    print('정확도(accuracy): {0:.4f}, 정밀도(precision): {1:.4f}, 재현율(recall): {2:.4f}, f1_score: {3:.4f}'.format(accuracy, precision, recall, f1))
    
    return [accuracy, precision, recall, f1]