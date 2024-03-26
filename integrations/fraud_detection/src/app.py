import streamlit as st
import pandas as pd
import pickle


# import preproses
preproses = pickle.load(open("preproses.pkl", "rb"))
# import model
model = pickle.load(open("model.pkl", "rb"))

#title
st.title("Online Payments Fraud Detection")
st.write("Created by Aleen Dhar and Shivam Singh")

# User imput
step = st.number_input(label='Unit of time (hour)', min_value=1, max_value=143, value=1, step=1)
type = st.selectbox(label='Select type of online transaction', options=['PAYMENT', 'TRANSFER', 'CASH_OUT', 'DEBIT', 'CASH_IN'])
amount = st.number_input(label='Input amount of the transaction', min_value=0.0, max_value=10000000.0, value=0.0, step=0.1)
nameOrig = st.text_input('Input customer origin Id', value='')
oldbalanceOrg = st.number_input(label='Balance before the transaction', min_value=0.0, max_value=38939424.03, value=0.0, step=0.1)
newbalanceOrig = st.number_input(label='Balance after the transaction', min_value=0.0, max_value=38946233.02, value=0.0, step=0.1)
nameDest = st.text_input('Input customer destination Id', value='')
oldbalanceDest = st.number_input(label='Input initial balance of recipient before the transaction', min_value=0.0, max_value=42207404.59, value=0.0, step=0.1)
newbalanceDest = st.number_input(label='Input the new balance of recipient after the transaction', min_value=0.0, max_value=42207404.59, value=0.0, step=0.1)

# Convert ke data frame
data = pd.DataFrame({'step': [step],
                'type': [type],
                'amount': [amount],
                'nameOrig': [nameOrig],
                'oldbalanceOrg': [oldbalanceOrg],
                'newbalanceOrig': [newbalanceOrig],
                'nameDest': [nameDest],
                'oldbalanceDest': [oldbalanceDest],
                'newbalanceDest': [newbalanceDest]
            })

data = preproses.transform(data)
# model predict

if st.button('Predict'):
    prediction = model.predict(data).tolist()[0]

    if prediction == 1:
        prediction = 'Froud'
    else:
        prediction = 'Not Froud'

    st.write('The Prediction is: ')
    st.write(prediction)