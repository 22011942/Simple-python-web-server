import os
import http.server
import urllib.parse
import base64
import requests
import _thread
import json
import sys

if len(sys.argv) > 1:
    serverPort = int(sys.argv[1])
else:
    serverPort = 8080

Username = '22011942'
Password = '22011942'

def auth(auth_header):
    info = base64.b64decode(auth_header.split(' ')[1]).decode('utf-8')
    username , password = info.split(':')
    return username == Username and password == Password

def fileopen(filename, mode='r'):
    with open(filename, mode) as fin:
        content = fin.read()
    return content
        

class MyHandler(http.server.BaseHTTPRequestHandler):
    
    data = {}
    profile = {}
    
    def do_GET(self):
        
        if 'Authorization' not in self.headers:
            self.send_response(401)
            self.send_header('WWW-Authenticate', 'Basic realm="Secure Area"')
            self.end_headers()
            self.wfile.write(b'401 Unauthorized')
            return
        
        if not auth(self.headers['Authorization']):
            self.send_response(401)
            self.send_header('WWW-Authenticate', 'Basic realm="Secure Area"')
            self.end_headers()
            self.wfile.write(b'401 Unauthorized')
            return
        
        filename = self.path.strip('/')
        
        if filename == '':
            filename = 'index.html'
        elif filename == 'form':
            filename = 'psycho.html'
        elif filename == 'view/input':
            print("hello")
            
            
        print('GET:', filename, _thread.get_native_id())
        
        content = b''
        
        if filename == 'view/input':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(MyHandler.data).encode())
            
        elif filename == 'view/profile':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(MyHandler.profile).encode())
    
        elif os.path.exists(filename):
            self.send_response(200)
            if filename.endswith('.html'):
                self.send_header('Content-type', 'text/html')
                content = fileopen(filename).encode()
            
            elif filename.endswith('.jpg'):
                self.send_header('Content-type', 'image/jpeg')
                content = fileopen(filename, mode='rb')
            
            elif filename.endswith('.ico'):
                self.send_header('Content-type', 'image/x-icon')
                content = fileopen(filename, mode='rb')
            
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            content = f'<h1>404 NOT FOUND</h1>{filename}'.encode()
        
        self.end_headers()
        self.wfile.write(content)
        
        
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        print('POST:', post_data, _thread.get_native_id())
        pdata = urllib.parse.parse_qs(post_data)
        print(pdata)
        
        try:
            name = pdata[b'name'][0].decode()
            gender = pdata[b'gender'][0].decode()
            birthYear = pdata[b'birthyear'][0].decode()
            birthPlace = pdata[b'birthplace'][0].decode()
            residence = pdata[b'residence'][0].decode()
            answers = {}
            for key, value in pdata.items():
                if key.startswith(b'question['):
                    question_number = int(key.split(b'[')[1].split(b']')[0])
                    answers[question_number]=int(value[0])
            job = pdata[b'job'][0].decode()
            pets = pdata.get(b'pets[]', [])
            chosen_pets = [pet.decode() for pet in pets]
            message = pdata[b'message'][0].decode()
            
            
            MyHandler.data = {
                "Name": name,
                "Gender": gender,
                "Birth year": birthYear,
                "Birth place": birthPlace,
                "Residence": residence,
                "Answers": answers,
                "Chosen job": job,
                "Chosen pets": chosen_pets,
                "Message": message   
            }
            
            formatted = [{"Title": movie[0], "Year": movie[1]} for movie in reccomend_movies(job)]
            formatted_score = [{"Score": score[0], "Suitability": score[1], "Description": score[2]} for score in analysis(answers, job)]
            MyHandler.profile = {
                "Movies": formatted,
                "Pet images": generate_pet(chosen_pets),
                "Results": formatted_score
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<div style="text-align: center;"><h1>Analysis complete</h1> <a href="http://localhost:8080/" class="btn">Go Back</a></div>')
            
            
        except KeyError:
            self.send_response(400)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Not all info can be found')
            resp = '<html>Not all info can be found</html>'
            
def reccomend_movies(chosen_job):
    response = requests.get(f'http://www.omdbapi.com/?apikey=745e81da&s={chosen_job}&type=movie')
    data = response.json()
    if response.status_code == 200:
        ids = [movie['imdbID'] for movie in data['Search']]
        
        reccomended_movies = []
        for id in ids:
            movie_response = requests.get(f'http://www.omdbapi.com/?apikey=745e81da&i={id}&type=movie')
            reccomended_movies.append((movie_response.json()['Title'], movie_response.json()['Year']))
        return reccomended_movies
    else:
        print("Failled to find movies")
        return None
        
            

def generate_pet(chosen_pets):
    pet_images = []
    for pet in chosen_pets:
        if pet == 'dog':
            response = requests.get(f'https://dog.ceo/api/breeds/image/random')
            if response.status_code == 200:
                pet_images.append(response.json()['message'])
            else:
                print("Failled to get dog image")
        elif pet == 'cat':
            response = requests.get(f'https://api.thecatapi.com/v1/images/search')
            if response.status_code == 200:
                pet_images.append(response.json()[0]['url'])
            else:
                print('Failled to get cat image')
        elif pet == 'duck':
            response = requests.get(f'https://random-d.uk/api/v2/random')
            if response.status_code == 200:
                pet_images.append(response.json()['url'])
            else:
                print('Failled to get duck iamge')
    return pet_images
            

def analysis(answers, job_title):
    score = []
    weights = {
        'ceo': [2, 3, 2, 1, 4, 4, 2, 3, 3, 1, 2, 1, 3, 1, 1, 1, 3, 3, 2, 4],
        'astro': [4, 5, 3, 4, 1, 5, 4, 4, 2, 4, 3, 1, 1, 3, 2, 2, 2, 2, 1, 5],
        'doc': [3, 5, 4, 4, 1, 4, 4, 3, 2, 4, 3, 1, 2, 3, 2, 3, 3, 2, 2, 4],
        'model': [4, 3, 2, 3, 3, 4, 3, 3, 3, 3, 3, 3, 2, 4, 3, 1, 3, 3, 2, 2],
        'rock': [3, 4, 5, 3, 5, 4, 3, 4, 3, 3, 4, 2, 2, 2, 2, 2, 3, 3, 2, 4],
        'garbage': [3, 4, 3, 3, 2, 3, 3, 3, 2, 4, 3, 3, 4, 4, 3, 4, 3, 4, 4, 3]
    }
    total = 0
    if job_title == 'ceo':
        for answer in answers:
            if answer == 5:
                if answers[answer] <= weights['ceo'][answer - 1]:
                    total = total + (weights['ceo'][answer - 1] - answers[answer])
                    continue
                else:
                    total = total + (weights['ceo'][answer - 1] - answers[answer])
                    continue
            elif answer == 9:
                if answers[answer] <= weights['ceo'][answer - 1]:
                    total = total + (weights['ceo'][answer - 1] - answers[answer])
                    continue
                else:
                    total = total + (weights['ceo'][answer - 1] - answers[answer])
                    continue
            elif answer >= 12 and answer <= 16:
                if answers[answer] <= weights['ceo'][answer - 1]:
                    total = total + (weights['ceo'][answer - 1] - answers[answer])
                    continue
                else:
                    total = total + (weights['ceo'][answer - 1] - answers[answer])
                    continue
            elif answer == 19:
                if answers[answer] <= weights['ceo'][answer - 1]:
                    total = total + (weights['ceo'][answer - 1] - answers[answer])
                    continue
                else:
                    total = total + (weights['ceo'][answer - 1] - answers[answer])
                    continue
            
            if answers[answer] >= weights['ceo'][answer - 1]:
                total = total + (answers[answer] - weights['ceo'][answer - 1])
            else:
                total = total + (answers[answer] - weights['ceo'][answer - 1])
    elif job_title == 'astronaut':
        for answer in answers:
            if answer == 5:
                if answers[answer] <= weights['astro'][answer - 1]:
                    total = total + (weights['astro'][answer - 1] - answers[answer])
                    continue
                else:
                    total = total + (weights['astro'][answer - 1] - answers[answer])
                    continue
            elif answer == 9:
                if answers[answer] <= weights['astro'][answer - 1]:
                    total = total + (weights['astro'][answer - 1] - answers[answer])
                    continue
                else:
                    total = total + (weights['astro'][answer - 1] - answers[answer])
                    continue
            elif answer >= 12 and answer <= 19:
                if answers[answer] <= weights['astro'][answer - 1]:
                    total = total + (weights['astro'][answer - 1] - answers[answer])
                    continue
                else:
                    total = total + (weights['astro'][answer - 1] - answers[answer])
                    continue
            if answers[answer] >= weights['astro'][answer - 1]:
                total = total + (answers[answer] - weights['astro'][answer - 1])
            else:
                total = total + (answers[answer] - weights['astro'][answer - 1])
    elif job_title == 'doctor':
        for answer in answers:
            if answer == 5:
                if answers[answer] <= weights['doc'][answer - 1]:
                    total = total + (weights['doc'][answer - 1] - answers[answer])
                    continue
                else:
                    total = total + (weights['doc'][answer - 1] - answers[answer])
                    continue
            elif answer == 9:
                if answers[answer] <= weights['doc'][answer - 1]:
                    total = total + (weights['doc'][answer - 1] - answers[answer])
                    continue
                else:
                    total = total + (weights['doc'][answer - 1] - answers[answer])
                    continue
            elif answer >= 12 and answer <= 19:
                if answers[answer] <= weights['doc'][answer - 1]:
                    total = total + (weights['doc'][answer - 1] - answers[answer])
                    continue
                else:
                    total = total + (weights['doc'][answer - 1] - answers[answer])
                    continue
            if answers[answer] >= weights['doc'][answer - 1]:
                total = total + (answers[answer] - weights['doc'][answer - 1])
            else:
                total = total + (answers[answer] - weights['doc'][answer - 1])
    elif job_title == 'model':
        for answer in answers:
            if answer == 5:
                if answers[answer] <= weights['model'][answer - 1]:
                    total = total + (weights['model'][answer - 1] - answers[answer])
                    continue
                else:
                    total = total + (weights['model'][answer - 1] - answers[answer])
                    continue
            elif answer == 9:
                if answers[answer] <= weights['model'][answer - 1]:
                    total = total + (weights['model'][answer - 1] - answers[answer])
                    continue
                else:
                    total = total + (weights['model'][answer - 1] - answers[answer])
                    continue
            elif answer == 12 or answer == 13:
                if answers[answer] <= weights['model'][answer - 1]:
                    total = total + (weights['model'][answer - 1] - answers[answer])
                    continue
                else:
                    total = total + (weights['model'][answer - 1] - answers[answer])
                    continue
            elif answer >= 15 and answer <= 20:
                if answers[answer] <= weights['model'][answer - 1]:
                    total = total + (weights['model'][answer - 1] - answers[answer])
                    continue
                else:
                    total = total + (weights['model'][answer - 1] - answers[answer])
                    continue
            if answers[answer] >= weights['model'][answer]:
                total = total + (answers[answer] - weights['model'][answer - 1])
            else:
                total = total + (answers[answer] - weights['model'][answer - 1])
    elif job_title == 'rockstar':
        for answer in answers:
            if answer == 5:
                if answers[answer] <= weights['rock'][answer - 1]:
                    total = total + (weights['rock'][answer - 1] - answers[answer])
                    continue
                else:
                    total = total + (weights['rock'][answer - 1] - answers[answer])
                    continue
            elif answer == 9:
                if answers[answer] <= weights['rock'][answer - 1]:
                    total = total + (weights['rock'][answer - 1] - answers[answer])
                    continue
                else:
                    total = total + (weights['rock'][answer - 1] - answers[answer])
                    continue
            elif answer >= 12 and answer <= 19:
                if answers[answer] <= weights['rock'][answer - 1]:
                    total = total + (weights['rock'][answer - 1] - answers[answer])
                    continue
                else:
                    total = total + (weights['rock'][answer - 1] - answers[answer])
                    continue
            if answers[answer] >= weights['rock'][answer - 1]:
                total = total + (answers[answer] - weights['rock'][answer - 1])
            else:
                total = total + (answers[answer] - weights['rock'][answer - 1])
    elif job_title == 'garbage':
        for answer in answers:
            if answer == 5:
                if answers[answer] <= weights['garbage'][answer - 1]:
                    total = total + (weights['garbage'][answer - 1] - answers[answer])
                    continue
                else:
                    total = total + (weights['garbage'][answer - 1] - answers[answer])
                    continue
            elif answer == 9:
                if answers[answer] <= weights['garbage'][answer - 1]:
                    total = total + (weights['garbage'][answer - 1] - answers[answer])
                    continue
                else:
                    total = total + (weights['garbage'][answer - 1] - answers[answer])
                    continue
            elif answer == 12 or answer == 13:
                if answers[answer] <= weights['garbage'][answer - 1]:
                    total = total + (weights['garbage'][answer - 1] - answers[answer])
                    continue
                else:
                    total = total + (weights['garbage'][answer - 1] - answers[answer])
                    continue
            elif answer >= 15 and answer <= 20:
                if answers[answer] <= weights['garbage'][answer - 1]:
                    total = total + (weights['garbage'][answer - 1] - answers[answer])
                    continue
                else:
                    total = total + (weights['garbage'][answer - 1] - answers[answer])
                    continue
            if answers[answer] >= weights['garbage'][answer - 1]:
                total = total + (answers[answer] - weights['garbage'][answer - 1])
            else:
                total = total + (answers[answer] - weights['garbage'][answer - 1])
                
        
    if job_title == 'ceo':
        if total == -42:
            suitability = "extermely unsuitable"
            explanation = "You gained the lowest possible score making it extermely unlikely you'd gain a position of power like a ceo."
        elif total > -42 and total < -22:
            suitability = "very unsuitable"
            explanation = "You have gained a very low score, dont be detered there are many other job opportunities available."
        elif total >= -22 and total <= 0:
            suitability = "unsuitable"
            explanation = "You have gained a low score but fear not you still gave a chance as long as you put your mind to it."
        elif total > 0  and total <= 20:
            suitability = "suitable"
            explanation = "congratulations you have recieved a suitable score, certainly not the best but you'll make do."
        elif total > 20 and total < 38:
            suitability = "very suitable"
            explanation = "congratulations you make a great ceo, with your skills you'd be a great leader."
        elif total == 38:
            suitability = "extremely suitable"
            explanation = "There arent many like you, you'd be an amazing leader unlike any other, truly leading the way."
    elif job_title == 'astronaut':
        if total == -64:
            suitability = "extermely unsuitable"
            explanation = "I dont think you're ready for this one, maybe space is far away from you for a reason."
        elif total > -64 and total < -20:
            suitability = "very unsuitable"
            explanation = "You should look into other careers this one just isnt for you."
        elif total >= -20 and total <= 0:
            suitability = "unsuitable"
            explanation = "You're close to succeeding but space is harsh and any mistake will cost you your life, you need to study up!"
        elif total > 0  and total <= 10:
            suitability = "suitable"
            explanation = "You are suitable enough to be an astronaut though most liekly only on the easiest missions."
        elif total > 10 and total < 16:
            suitability = "very suitable"
            explanation = "You'd make a great astronaut, having all the required qualities will set you apart from the rest."
        elif total == 16:
            suitability = "extremely suitable"
            explanation = "You are unlike any other. A mind of steel and the image of a legend, youd pave the way for mankind."
    elif job_title == 'doctor':
        if total == -57:
            suitability = "extermely unsuitable"
            explanation = "I reckon you shold only go to a hospital if you require help rather then working there."
        elif total > -57 and total < -17:
            suitability = "very unsuitable"
            explanation = "You should look into other less stressful career paths."
        elif total >= -17 and total <= 0:
            suitability = "unsuitable"
            explanation = "You might be very close being being suitable but being a medic is being responsible over anothers life, mistakes cannot be made."
        elif total > 0  and total <= 12:
            suitability = "suitable"
            explanation = "You are suitable to become a medic though you are a very long way away from the best of the best."
        elif total > 12 and total < 23:
            suitability = "very suitable"
            explanation = "You'd make a great medic, having a good mental clarity and team focus will allow you to save many lives."
        elif total == 23:
            suitability = "extremely suitable"
            explanation = "Why arent you a medic right now? You'd be out there saving lives without a second thought."
    elif job_title == 'model':
        if total == -47:
            suitability = "extermely unsuitable"
            explanation = "I dont think you have what it takes to be a model, the catwalk is a very stressful enviorment."
        elif total > -47 and total < -12:
            suitability = "very unsuitable"
            explanation = "I just dont think that this is for you, there are many other oppurtunities availible for you."
        elif total >= -12 and total <= 0:
            suitability = "unsuitable"
            explanation = "You're very close to being suitible for the role you just need some more study and practise."
        elif total > 0  and total <= 18:
            suitability = "suitable"
            explanation = "congratulations you have what it takes to be a model, but you have a long way from the best."
        elif total > 18 and total < 33:
            suitability = "very suitable"
            explanation = "You have what it takes to be an amazing model, you'd shake up any catwalk."
        elif total == 33:
            suitability = "extremely suitable"
            explanation = "You're face and style will be on every billboard and in every city you are simply a model."
    elif job_title == 'rockstar':
        if total == -51:
            suitability = "extermely unsuitable"
            explanation = "I think its time to focus on something else."
        elif total > -51 and total < -12:
            suitability = "very unsuitable"
            explanation = "I dont think think you have it in you to become a rockstar."
        elif total >= -12 and total <= 0:
            suitability = "unsuitable"
            explanation = "You're almost there you just need a bit more pratise and some metal hardening and you'll have what it takes."
        elif total > 0  and total <= 20:
            suitability = "suitable"
            explanation = "You have what it takes to become a rockstar but you have a long raod to becoming one of the greats."
        elif total > 20 and total < 29:
            suitability = "very suitable"
            explanation = "You'd become a great rockstar, one that will be remembered for one of their good hits."
        elif total == 29:
            suitability = "extremely suitable"
            explanation = "You shall be remembered as a legend, you band will be immortalised in the hall of fame."
    elif job_title == 'garbage':
        if total == -41:
            suitability = "extermely unsuitable"
            explanation = "I dont think this job is for you, it requires a strong mindest."
        elif total > -41 and total < -22:
            suitability = "very unsuitable"
            explanation = "You could try looking into other career paths this one isnt for everyone."
        elif total >= -22 and total <= 0:
            suitability = "unsuitable"
            explanation = "You're almost there though you might need to work on your skills a little more."
        elif total > 0  and total <= 20:
            suitability = "suitable"
            explanation = "You've got what it takes but you've got a long way from the best."
        elif total > 20 and total < 39:
            suitability = "very suitable"
            explanation = "You will known around the community as the one of the best garbage disposal units."
        elif total == 39:
            suitability = "extremely suitable"
            explanation = "You are the very best, they arent any like you, you'll make a difference in the world."
            
    score.append((total, suitability, explanation))
    return score
        
         


def main(port):
    webServer = http.server.HTTPServer(('', 8080), MyHandler)
    webServer.serve_forever()

if __name__ == '__main__':
    port = 8080
    main(port)