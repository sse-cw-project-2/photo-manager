####################################################################################################
# Project Name: Motive Event Management System
# Course: COMP70025 - Software Systems Engineering
# File: photoManager.py
# Description: This file contains the flask routes to upload and fetch photos to display on a venue
#              or artist's home page.
#
# Authors: James Hartley, Ankur Desai, Patrick Borman, Julius Gasson, and Vadim Dunaevskiy
# Date: 2024-02-21
# Version: 1.1
#
# Changes: Added delete function.
#
# Notes: JS partial code to upload and retrieve photos included at the end of the file.
####################################################################################################


from flask import Flask, jsonify
from supabase import create_client, Client
from dotenv import load_dotenv
import os
import functions_framework


app = Flask(__name__)

# Supabase setup
load_dotenv()
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


@functions_framework.http
def api_upload_photo(request):
    # # Authenticate the user and get user_id if necessary
    # user_id, error = authenticate(request)
    # if error:
    #     return jsonify({'error': error}), 401
    user_id = request.args.get("user_id")

    if "file" not in request.files:
        return jsonify({"message": "No file part"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"message": "No selected file"}), 400

    # Organize uploads by user_id
    file_path = f"uploads/{user_id}/{file.filename}"

    # Upload to Supabase
    response = supabase.storage.from_("profile-photos").upload(file_path, file)

    if response.get("error") is None:
        public_url = (
            supabase.storage.from_("profile-photos")
            .get_public_url(file_path)
            .data.get("publicURL")
        )

        # Insert URL into images table to more easily associate photos with user IDs
        # db_insert_result = (
        #     supabase.table("images")
        #     .insert({"url": public_url, "user_id": user_id})
        #     .execute()
        # )

        return jsonify({"url": public_url}), 200
    else:
        return jsonify({"error": response["error"]["message"]}), 500


@functions_framework.http
def api_get_images(request):
    # Note: Have assumed so far that we want to store/filter by user_id
    user_id = request.args.get("user_id")

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    # Fetch images filtered by user_id
    response = supabase.table("images").select("*").eq("user_id", user_id).execute()

    if response.error:
        return jsonify({"error": response.error.message}), 500
    else:
        image_urls = [row["url"] for row in response.data]
        return jsonify(image_urls), 200


@functions_framework.http
def api_delete_photo(request):
    # Extract photo ID and user ID from the request - must coordinate with front end
    data = request.json
    photo_id = data.get("photo_id")
    user_id = data.get("user_id")

    # Fetch the photo from the database
    photo_query = supabase.table("photos").select("*").eq("id", photo_id).execute()

    if photo_query.error:
        return jsonify({"error": "Failed to fetch photo information"}), 500

    if not photo_query.data:
        return jsonify({"error": "Photo not found"}), 404

    photo = photo_query.data[0]

    # Verify that the photo belongs to the user
    if photo["user_id"] != user_id:
        return jsonify({"error": "Unauthorized to delete this photo"}), 403

    # Delete the photo file from storage
    storage_response = supabase.storage.from_("profile-photos").remove(
        [photo["file_path"]]
    )
    if storage_response.error:
        return jsonify({"error": "Failed to delete photo from storage"}), 500

    # Delete the photo reference from the database
    db_response = supabase.table("photos").delete().eq("id", photo_id).execute()
    if db_response.error:
        return jsonify({"error": "Failed to delete photo reference from database"}), 500

    return jsonify({"success": True, "message": "Photo deleted successfully"}), 200


if __name__ == "__main__":
    app.run(debug=True)


####################################################################################################
# JS placeholder to upload a photo - needs tweaking and design decisions
# --------------------------------------------------------------------------------------------------
# < input
# type = "file"
# id = "photoInput"
# accept = "image/*" >
# < button
# onclick = "uploadPhoto()" > Upload
# Photo < / button >
#
# < script >
# async function
# uploadPhoto()
# {
#     const
# fileInput = document.getElementById('photoInput');
# const
# file = fileInput.files[0];
#
# if (!file)
# {
#     alert('Please select a file to upload.');
# return;
# }
#
# userId = getCurrentUserId(); // Implement
# const photoType = 'profile';
#  const formData = new FormData();
#     formData.append('file', file);
#     formData.append('user_id', userId); // Need to decide how to pass user_id
#     formData.append('photo_type', photoType);
#
#     try {
#         const response = await fetch('http://localhost:5000/upload', {
#             method: 'POST',
#             body: formData, // automatically set to 'multipart/form-data'
#         });
#
#         if (response.ok) {
#             const result = await response.json();
#             console.log('Upload successful:', result.url);
#             alert('Upload successful!');
#         } else {
#             throw new Error('Upload failed');
#         }
#     } catch (error) {
#         console.error('Error uploading photo:', error);
#         alert(error.message);
#     }
# }
#
# </script>
####################################################################################################

####################################################################################################
# Clientside JS placeholder to retrieve a user's photos - needs tweaking and design decisions
# --------------------------------------------------------------------------------------------------
# const userId = 'your_user_id_here'; // Need a mechanism to retrieve this
# fetch(`http://localhost:5000/get-images?user_id=${userId}`) // ChatGPT suggested this
#     .then(response => response.json())
#     .then(urls => {
#         const container = document.getElementById('photos-container');
#         urls.forEach(url => {
#             const img = document.createElement('img');
#             img.src = url;
#             // Define styling here
#             img.style.width = '100px';
#             img.style.height = '100px';
#             img.alt = 'Photo';
#             container.appendChild(img);
#         });
#     })
#     .catch(error => console.error('Error fetching images:', error));
#
####################################################################################################

####################################################################################################
# Clientside JS placeholder to delete a user's photo - ChatGPT suggestion, need to tailor
# --------------------------------------------------------------------------------------------------
# <div id="photoList">
#     <!-- Dynamically list photos here -->
# </div>
#
# <script>
# async function deletePhoto(photoId) {
#     const response = await fetch('/delete-photo', {
#         method: 'POST',
#         headers: {
#             'Content-Type': 'application/json',
#         },
#         body: JSON.stringify({photo_id: photoId, user_id: 'user_id_here'}),
#     });
#
#     if (response.ok) {
#         alert("Photo deleted successfully");
#         // Remove the photo element from the DOM or refresh the photo list
#     } else {
#         const error = await response.json();
#         alert(error.message);
#     }
# }
#
# // Example function to dynamically add photos to the page (simplified)
# function addPhotoToPage(photo) {
#     const photoList = document.getElementById('photoList');
#     const photoElem = document.createElement('div');
#     photoElem.innerHTML = `<img src="${photo.url}" width="100"> \
#    <button onclick="deletePhoto('${photo.id}')">Delete</button>`;
#     photoList.appendChild(photoElem);
# }
# </script>
####################################################################################################
