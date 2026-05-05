# Chomp

Chomp is a simple web tool I built to see what the restaurant scene looks like in different cities. You just type in a place, set how far you want to search, and it pulls every restaurant it can find using OpenStreetMap data. 

I made a quick video showing how it works : https://www.youtube.com/watch?v=oJPEN5DmreQ

### How it works
It uses the Overpass API to grab restaurant data. Once it gets the results, it saves them to a local database and gives you a breakdown of what cuisines are popular and which places actually have their contact info listed. 

### Why I built it this way
* **Flask:** It's easy to use and I didn't need anything fancy for the backend.
* **SQLite:** Since it's a local tool, a simple database file works perfectly fine.
* **Vanilla JS:** I used Chart.js for the graphs, but everything else is just plain Javascript to keep it lightweight.
* **Overpass API:** It's free and has a ton of data without needing to sign up for an API key.

### Getting it running
If you want to try it out, you'll need Python and a couple of libraries:

```bash
pip install flask requests
```

Then just run the app:

```bash
python app.py
```

Open your browser to `http://localhost:5000` and you're good to go. The database gets created the first time you run it.

One heads up: if you search a really big area in a crowded city, it might take a second to load. I added some retry logic in case the API is being slow, but smaller searches are usually pretty fast.
