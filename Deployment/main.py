import pandas as pd
from flask import Flask, request, render_template
import pickle
import bz2
import _pickle as cPickle
import requests

app = Flask('__name__')
movie_list = pickle.load(open('movies_dict.pkl', 'rb'))
movies = pd.DataFrame(movie_list)


def decompress_pickle(file):
    data = bz2.BZ2File(file, 'rb')
    data = cPickle.load(data)
    return data


pklfile = decompress_pickle('similarity_comp.pbz2')
similarity = pklfile


def getposter(movie_id):
    response = requests.get(
        'https://api.themoviedb.org/3/movie/{}?api_key=d683514e4dc228c570bfb5ca530e89e3'.format(movie_id))
    movie_data = response.json()
    poster_path = movie_data.get('poster_path')
    if poster_path == None:
        return "https://www.movienewz.com/img/films/poster-holder.jpg"
    else:
        return "https://image.tmdb.org/t/p/original" + str(poster_path)


@app.route("/")
def home():
    poster_title = []
    poster_url = []
    top_list = movies.sort_values('popularity', ascending=False)
    for i in range(30):
        poster_title.append(top_list.title.iloc[i])
        poster_url.append(getposter(top_list.movie_id.iloc[i]))
    return render_template('index.html', movie_title=poster_title, poster_url=poster_url,
                           all_movie_list=movies.sort_values('title').title.values.tolist())


@app.route('/recommend', methods=['POST'])
def recommend():
    movie = request.form.get('title')
    movie_index = movies[movies['title'] == movie].index.values[0]
    distances = similarity[movie_index]
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:7]
    top_movie_id = []
    top_movie_title = []
    top_movie_poster_url = []
    for i in range(6):
        top_movie_id.append(movies_list[i][0])
        top_movie_title.append(movies.title[top_movie_id[i]])
        top_poster_url = getposter(movies[movies.title == top_movie_title[i]].movie_id.values[0])
        top_movie_poster_url.append(top_poster_url)
    return render_template('recommendpage.html', searched_for=movie, top_movie_title=top_movie_title,
                           poster_url=top_movie_poster_url,
                           all_movie_list=movies.sort_values('title').title.values.tolist())


def fetch_movie_details(movie_id):
    api_key = "d683514e4dc228c570bfb5ca530e89e3"
    base_url = "https://api.themoviedb.org/3"
    endpoint = f"/movie/{movie_id}"
    url = f"{base_url}{endpoint}"
    params = {
        "api_key": api_key,
        "append_to_response": "credits",
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        description = data.get("overview")
        release_date = data.get("release_date")
        rating = data.get("vote_average")
        genres = [genre["name"] for genre in data.get("genres")]
        cast = [actor["name"] for actor in data["credits"]["cast"][:5]]  # Get the first 5-cast members
        director = [crew["name"] for crew in data["credits"]["crew"] if crew["job"] == "Director"]
        runtime = data.get("runtime")
        production_companies = [company["name"] for company in data.get("production_companies")]
        production_countries = [country["name"] for country in data.get("production_countries")]
        spoken_languages = [language["name"] for language in data.get("spoken_languages")]
        movie_info = [
            description,
            release_date,
            rating,
            genres,
            cast,
            director,
            runtime,
            production_companies,
            production_countries,
            spoken_languages,
        ]
        return movie_info
    else:
        print(f"Error: Unable to fetch movie details. Status Code: {response.status_code}")
        return None


@app.route('/movie_detail/<movie_title>')
def movie_detail(movie_title):
    movie_title = movies[movies['title'] == movie_title].iloc[0]
    movie_details = fetch_movie_details(movie_title.movie_id)
    return render_template('movie_detail.html', all_movie_list=movies.sort_values('title').title.values.tolist(),
                           movie_title=movie_title.title,
                           poster_url=getposter(movie_title.movie_id),
                           movie_overview=movie_details[0],
                           movie_year=movie_details[1],
                           movie_rating=movie_details[2],
                           movie_cast=movie_details[4],
                           movie_director=movie_details[5],
                           movie_runtime=movie_details[6],
                           movie_production_companies=movie_details[7],
                           movie_production_countries=movie_details[8],
                           movie_spoken_languages=movie_details[9]
                           )


if __name__ == "__main__":
    app.run(debug=True)
