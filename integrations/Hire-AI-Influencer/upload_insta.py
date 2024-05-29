from instagrapi import Client

def upload(file,username):
	# Your Instagram credentials
	username = username
	password = "888888"

	# Create a client instance
	cl = Client()

	# Login using the provided credentials
	cl.login(username, password)

	# Upload the image
	media = cl.photo_upload(path=file, caption="#ai #artificial_intelligence #gen_ai #ai_art #influencer")


# # username='lalit.ai.2024'
# username='seema.ai.2024'
# upload('img.png',username)
