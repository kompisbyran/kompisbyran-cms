# Kompisbyrån

## Setup for local development

 1. Clone the repo: `git@github.com:valtech/kompisbyran.github`
 2. Install Python, Pip, gem and Virtualenv
 3. Install sass: `gem install sass`
 4. Get the project packages: `make install`
 5. Get skeleton .env file: `make .env`
 6. Populate the .env file with your environment variables that you find on Contentful (Management API key can be found in the Oderland environment).
 7. Activate the environment variables with: `source .env`
 8. Use virtualenv: `source venv/bin/activate`
 8. In one terminal window, run: `make watch-css`
 9. In another terminal, run: `python src/app.py` or `make run`


## Oderland

On Oderland you have to specify the dependencies for the project in the web GUI for the python app. The environment variables are specified in the
.bashrc file. Pushing to Oderland is done through CircleCI and that is done with the commands `make production` and `make deploy` which you can see in circle.yml.

When the code is deployed you need to restart the python app in Oderlands web GUI.

## Mail integration

Mails sent to hej@kompisbyran.se will be parsed to create and upload a meetup to Contentful. If several images are present in the email, the largest will be used.
Both the image and the meetup itself must be published before it is shown on the webpage. No email may exceed 30Mb in size, or it will be ignored.
