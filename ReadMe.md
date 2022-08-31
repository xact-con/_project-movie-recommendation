# Django application for your movies from movie portal #  
Organise your rated (watched) and WTS (want to see) movies on your own www site.  
Get recommendation which movie you'd like the most on any of a VOD streaming portal.

### Functionalities ###
- parses rated and WTS movies from movie portal
- recommendation engine calculates foreseen like rate for WTS movies 
- easy selection of movies for chosen streaming platform 
- selects movies on multi-criteria
- displays all details of a movie
- supports selection of movies for two users

### Technologies ###
- language - Python 3
- parsing - BeautifulSoup
- recommendation engine - Pandas
- backend / frontend - Django, HTML, Bootstrap
- database - MySQL

### Functionality details ###
##### Parsing #####
- uploaded information: movie id, title, rate, user rate, No. of votes, link, production year, production countries, 
genres, box office, budget, 5 top roles / actors with role rates, awards, streaming platform
- rated and WTS movies are uploaded; rated only once
##### Recommendation engine #####
- foreseen user rate based on number of parameters of seen movies; more watched ones returns better prediction

<img src="movies\imgs\recommend.jpg" title="recommendation engine" height="218" width="800"/>

##### menu Configuration #####
- Genres - enter abbreviation and how much do you like each genre

<img src="movies\imgs\genre.jpg" title="genre" height="234" width="800"/>

- movie portal credentials - enter username and cookie; to be used for parsing user related information

<img src="movies\imgs\credentials.jpg" title="credential" height="350" width="369"/>

##### menu Imports/Updates #####
- to be used for parsing specific data

<img src="movies\imgs\import.jpg" title="imports updates" height="288" width="800"/>

##### Movie details #####
- go to the address /movies/movie_id/
- all parsed information are shown
- for WTS movie a movie can be rated

<img src="movies\imgs\movie_details.jpg" title="movie details" height="432" width="800"/>

##### menu Movie's list #####
- menu Movie's list
- list of movies for chosen criteria would be shown
- \# - link to movie details' page
- movie title - link to movies' portal movie page 

<img src="movies\imgs\movie_selection.jpg" title="movie selection" height="470" width="800"/>

<img src="movies\imgs\movie_list.jpg" title="movie list" height="101" width="800"/>

##### menu VOD #####
- list of movies for a user and selected streaming platform to be shown
- arrow on right side of each movie - click to move this movie to another user's list

<img src="movies\imgs\vod.jpg" title="VOD selection" height="331" width="800"/>

<img src="movies\imgs\vod_list.jpg" title="VOD list" height="142" width="800"/>

##### Usage flow #####
###### First time ######
- menu Configuration / movies' portal credentials - enter movie portal username and cookies (details on app page) 
- upload rated movies (just once) - menu Imports/Updates / ...Upload rated movies... 
- upload WTS movies - menu Imports/Updates / Upload WTS movies...
- menu Configuration / Genres - enter how much do you like genres
- calculate recommendation rate and actors rate - menu Imports/Updates / Update recommendation rate...  
###### From time to time ######
- rate seen movies in movie portal and on movie's details page
- mark WTS movie on movie portal as usual
- upload WTS movies - menu Imports/Updates / Upload WTS movies...
- upload actual streaming portals' availability - menu Imports/Updates / Update VOD... 
- update recommendation rate and actor rate if necessary (it's done when upload WTS movies anyway) - 
menu Imports/Updates / Update recommendation rate...
###### Daily ######
- select movies based on various criteria - menu Movie's list
- see the most WTS movies on selected streaming portal for any of two users - menu VOD
- rate seen movie on movie's detailed page
### License ###
Any license is offered
