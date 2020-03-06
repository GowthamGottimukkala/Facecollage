import os,flask,glob,shutil
from flask import request, redirect, url_for,render_template,send_file
from werkzeug.utils import secure_filename
from imutils import build_montages
from imutils import paths
import random
import boto3
import cv2
import csv

app = flask.Flask(__name__)
app.config["DEBUG"] = True

@app.route('/')
def fun():
    return render_template("index.html")  

@app.route('/createCollage', methods=['GET','POST'])
def home():
    if request.method == 'POST':
        if 'data' not in request.files:
            return redirect(request.url)
        file = request.files['data']
        if file.filename == '':
            return redirect(request.url)
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join("receivedimages/" + filename))
        aws(filename)
        return send_file("Collage.jpg",mimetype='image/jpg')

def aws(filename):
    filename =  filename
    with open('credentials.csv','r') as inp:
        next(inp)
        reader = csv.reader(inp)
        for line in reader:
            aws_access_key_id = line[2]
            secret_access_key = line[3]
    image = filename
    client = boto3.client('rekognition',region_name='ap-south-1',aws_access_key_id = aws_access_key_id,aws_secret_access_key=secret_access_key)

    with open(image,'rb') as source_image:
        source_bytes = source_image.read()

    response = client.detect_faces(Image = {'Bytes':source_bytes},Attributes=['ALL']) 
    count = 5
    files = glob.glob('images/*')
    files2 = glob.glob('newimages/*')
    # for f in files:
    #     os.remove(f)
    for f in files2:
        os.remove(f)
    for facedetail in response["FaceDetails"]:
        point = facedetail["BoundingBox"]
        image = cv2.imread(filename)
        x,y,w,h = point["Left"], point["Top"], point["Width"], point["Height"]
        x,y,w,h = list(map(int,[x*image.shape[1],y*image.shape[0],w*image.shape[1],h*image.shape[0]]))
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
        roi_color = image[y:y + h, x:x + w] 
        print("[INFO] Object found. Saving locally.") 
        cv2.imwrite("images/"+str(count)+'.jpg', roi_color) 
        count += 1

    # comparing faces
    num = 0
    print(os.listdir("images"))
    for test1 in os.listdir("images"):
        with open("images/"+test1,'rb') as source_image:
            source_bytes = source_image.read()
        if(num==0):
            shutil.copy(glob.glob("images/"+test1)[0], "newimages/")
            num = 1
        else:
            match = 0
            for test2 in os.listdir("newimages"):
                with open("images/"+test2,'rb') as target_image:
                    target_bytes = target_image.read()
                response=client.compare_faces(SourceImage={'Bytes': source_bytes},TargetImage={'Bytes': target_bytes},SimilarityThreshold=80)
                if(len(response["FaceMatches"])!=0):
                    if(response["FaceMatches"][0]["Similarity"] > 90):
                        match = 1
                        break
            if(match==0):
                shutil.copy(glob.glob("images/"+test1)[0], "newimages/")

    images = []
    for imagePath in os.listdir("newimages"):
	    image = cv2.imread("newimages/"+imagePath)
	    images.append(image)
    montages = build_montages(images, (128, 196), (7, 3))
    for montage in montages:
        cv2.imwrite("Collage.jpg",montage)
  


if __name__ == "__main__":
    app.run(debug=True)