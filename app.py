from flask import Flask, request, url_for, session, redirect
from spotipy.oauth2 import SpotifyOAuth
from spotipy import Spotify
import time
import json

# -------------------------------------------------
# -- APP CRIDENTIALS FROM SPOTIFY FOR DEVELOPERS --
# -------------------------------------------------
CLIENT_ID = ""
CLIENT_SECRET = ""
# -------------------------------------------------

app = Flask(__name__)
app.config["ENV"] = "development"
app.config["DEBUG"] = True
app.config["TESTING"] = True

app.secret_key = "sdfjskalghnks42342"
app.config["SESSION_COOKIE_NAME"] = "Unfix Cookie"
TOKEN_INFO = "token_info"

# How many new artists to recommend
NEW_ARTISTS = 5
# How many songs for each artist
SNG_PER_ARTIST = 5


@app.route("/")
def login():
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)


@app.route("/authorize")
def authorize():
    sp_oauth = create_spotify_oauth()
    session.clear()
    code = request.args.get("code")
    token_info = sp_oauth.get_access_token(code)
    session[TOKEN_INFO] = token_info
    return redirect(url_for("getLastPlayed", _external=True))


@app.route("/getLastPlayed")
def getLastPlayed():
    token_info = get_token()
    sp = Spotify(auth=token_info["access_token"])

    query = sp.current_user_playing_track()

    lst_artist = query["item"]["album"]["artists"][0]["uri"]
    a_name = query["item"]["album"]["artists"][0]["name"]
    artists_json = sp.artist_related_artists(lst_artist)

    artists = [art["uri"] for art in artists_json["artists"][:NEW_ARTISTS]]
    songs = []
    for a in artists:
        temp = sp.artist_top_tracks(a)
        for t in temp["tracks"][:SNG_PER_ARTIST]:
            songs.append(t["uri"])

    sp.user_playlist_create(
        sp.current_user()["id"],
        f"pyRecA for {a_name}",
        public=False,
        description="Playlist created by pyRecomendArtists",
    )

    new_p_id = sp.current_user_playlists()["items"][0]["uri"]

    sp.playlist_add_items(new_p_id, songs)

    return new_p_id


def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        return redirect(url_for("login", _external=False))
    now = int(time.time())

    is_expired = token_info["expires_at"] - now < 1
    if is_expired:
        return redirect(url_for("login", _external=False))

    return token_info


def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=url_for("authorize", _external=True),
        scope="""user-library-read,
                    user-read-currently-playing,
                    playlist-modify-private,
                    playlist-read-private""",
    )


if __name__ == "__main__":
    app.run()
