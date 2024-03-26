from flask import Flask, render_template, request
from cal import add

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add', methods=['POST'])
def perform_addition():
    num1 = float(request.form['num1'])
    num2 = float(request.form['num2'])
    result = add(num1, num2)
    return render_template('result.html', result=result)

if __name__ == '__main__':
    app.run(debug=True)
