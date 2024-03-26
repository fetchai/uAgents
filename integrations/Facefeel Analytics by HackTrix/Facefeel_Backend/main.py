import tkinter as tk
from tkinter import simpledialog
from Cancer_Classification import cancer_classification
from Chennai_Housing_Prediction import chennai_housing_prediction
from Image_Emotion_Detection import image_emotion_detection
from Live_Emotion_Detection import live_emotion_detection

def run_tool():
    choice = choice_var.get()
    if choice == 1:
        path = input_entry.get()
        image_emotion_detection(path)
    elif choice == 3:
        cancer_classification()
    elif choice == 4:
        chennai_housing_prediction()
    elif choice == 2:
        live_emotion_detection()
    elif choice == 5:
        output_label.config(text="Program closed.")
        root.destroy()
        return
    else:
        output_label.config(text="Invalid choice. Please enter a valid option.")
        return
    output_label.config(text="Press enter to continue.")

def toggle_input_field():
    choice = choice_var.get()
    if choice == 1:
        input_frame.pack()
    else:
        input_frame.pack_forget()

root = tk.Tk()
root.title("Traceback")
root.geometry("400x300")

choice_var = tk.IntVar()
output_label = tk.Label(root, text="Welcome to Traceback!")
output_label.pack()

tk.Label(root, text="Which tool would you like to use today?").pack()

tools = [("Image Emotion Detection", 1),
         ("Live Emotion Detection", 2),
         ("Cancer Classification", 3),
         ("Chennai Housing Prediction", 4),
         ("Close", 5)]

for tool, val in tools:
    tk.Radiobutton(root, text=tool, variable=choice_var, value=val, command=toggle_input_field).pack()

input_frame = tk.Frame(root)
input_label = tk.Label(input_frame, text="Enter image file name:")
input_label.grid(row=0, column=0)

input_entry = tk.Entry(input_frame, width=40)
input_entry.grid(row=0, column=1)

run_button = tk.Button(root, text="Run", command=run_tool)
run_button.pack()

root.mainloop()