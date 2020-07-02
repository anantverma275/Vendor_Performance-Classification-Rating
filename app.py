import pickle
from flask import Flask, request, render_template
import pandas as pd
import numpy as np

app = Flask(__name__)
clf = pickle.load(open("model.pkl", "rb"))

@app.route('/')
def home():
    #getting template for input page
    
    return render_template('home.html') 

@app.route('/predict', methods = ['GET'])
def prediction():
    #getting values from input screen
    
    de = request.args.get("de")
    dr = request.args.get("dr")
    qd = int(request.args.get("qd"))
    qr = int(request.args.get("qr"))
    q_return = int(request.args.get("q_return"))
    
    #check for return quantity > received quantity
    
    if q_return > qr:
        return ("Invalid input: Quantity returned cannot be greater than quantity received")
    
    #scaling for promptness
    
    daydiff = (pd.to_datetime(de) - pd.to_datetime(dr)).days
    if daydiff > 0:
        daydiff = -daydiff/10
    file = pd.read_csv('compiled.csv',usecols=['DeliveryTime','EnteredReceivedQuantity','QuantityDemandedFinal'])
    file = file.append({'DeliveryTime': daydiff, 'EnteredReceivedQuantity': qr, 'QuantityDemandedFinal': qd}, ignore_index = True)
    promptness = (daydiff - np.min(file['DeliveryTime']))/(np.max(file['DeliveryTime']) - np.min(file['DeliveryTime']))
    
    #scaling for quantity
    
    min = 1
    max = np.max(file['EnteredReceivedQuantity']/file['QuantityDemandedFinal'])
    if qr <= qd:
        quantity = qr/qd
    else:
        quantity = 1-(((qr/qd)-min)/(max-min))
    
    #scaling for quality and check for quantity received is 0
    
    try:
        quality = 1 - q_return/qr
    except ZeroDivisionError:
        quality = 1
   
    if qr != 0:
        final_score = round((0.5*quality + 0.3*promptness + 0.2*quantity)*5,2)  # Rating of the vendor out 5; weights 0.5,0.3,0.2 for quality, qty, promptness
    else: # quality doesn't make sense if quantity received is zero
        final_score = round((0.55*promptness + 0.45*quantity)*5, 2)
    
    #settings the labels correctly
    # label_dict = {}
    # test = [[[1,1,1]],[[0,1,1]],[[1,0,1]],[[1,1,0]]]
    # label_dict['Performing'] = clf.predict(test[0])[0]
    # label_dict['quantity'] = clf.predict(test[1])[0]
    # label_dict['promptness'] = clf.predict(test[2])[0]
    # label_dict['quality'] = clf.predict(test[3])[0]
    
    #probablitlites for quntity, promptness and quality of given input

    # result = clf.predict_proba([[quantity, promptness, quality]])[0]
    
    #new = [['Quantity', round(result[label_dict['quantity']], 2)], ['Promptness', round(result[label_dict['promptness']], 2)], ['Quality', round(result[label_dict['quality']], 2)]]
    new = [['Quantity', round(quantity, 2)], ['Promptness', round(promptness, 2)], ['Quality', round(quality, 2)]]
    if qr == 0:
        new.pop()
        
    if clf.predict([[quantity, promptness, quality]]) == clf.predict([[1,1,1]]):
        answer = "Performing"
        new.sort(key = lambda x: x[1], reverse = True)
    else:
        answer = "Non-performing"
        if qr == 0:
            new[0][1] = 0.0
        new.sort(key = lambda x: x[1])

    # print(quantity, promptness, quality)
    # print(*result)
    print(new)
    
    return render_template("result.html", answer = answer, value = new, rating = str(final_score), length = len(new))


if __name__ == "__main__":
    app.run()
    #app.run(debug=True,host='0.0.0.0',port=5000)
