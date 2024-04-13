from gradio_client import Client
import requests
z
client = Client("stabilityai/TripoSR")
result = client.predict(
		"https://raw.githubusercontent.com/gradio-app/gradio/main/test/test_files/bus.png",	# filepath  in 'Input Image' Image component
		api_name="/check_input_image"
)
print(result)

result = client.predict(
		"https://raw.githubusercontent.com/gradio-app/gradio/main/test/test_files/bus.png",	# filepath  in 'Input Image' Image component
		True,	# bool  in 'Remove Background' Checkbox component
		0.5,	# float (numeric value between 0.5 and 1.0) in 'Foreground Ratio' Slider component
		api_name="/preprocess"
)
print(result)

result = client.predict(
		"https://raw.githubusercontent.com/gradio-app/gradio/main/test/test_files/bus.png",	# filepath  in 'Processed Image' Image component
		32,	# float (numeric value between 32 and 320) in 'Marching Cubes Resolution' Slider component
		api_name="/generate"
)
print(result)